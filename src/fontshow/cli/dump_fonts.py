"""
Fontshow dump-fonts CLI command.

This module implements the inventory discovery stage of the Fontshow
pipeline and produces a raw inventory describing fonts available on the
system.

Responsibilities
----------------
- Discover fonts using platform-specific mechanisms (Fontconfig or
  equivalent tools).
- Extract raw font metadata from system sources.
- Serialize discovered font information into the initial inventory
  format used by subsequent pipeline stages.

Design principles
-----------------
This stage performs **no semantic interpretation** of font metadata.
All extracted information is preserved as-is so that later stages
(`parse-inventory`, validation, and catalog generation) can perform
analysis and enrichment deterministically.

Architectural role
------------------
This module belongs to the **CLI interface layer** and implements the
font discovery stage that generates the initial Fontshow inventory.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from fontshow import __version__
from fontshow.constants.catalog import IS_LINUX
from fontshow.core.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.core.global_constants import SCHEMA_VERSION
from fontshow.core.json_format import dumps_pretty
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.inventory.font_descriptor import build_font_descriptor
from fontshow.inventory.fonttools_extraction import (
    FONTTOOLS_AVAILABLE,
    TTLibError,
    detect_font_container,
    fonttools_extract_all,
)
from fontshow.inventory.latex_validation_metadata import (
    collect_latex_validation_metadata,
)
from fontshow.inventory.loadability import (
    DEFAULT_LOADABILITY_JOBS,
    probe_and_persist_lualatex_loadability,
)
from fontshow.inventory.platform_metadata import collect_platform_metadata
from fontshow.inventory.schema_accessors import get_font_metrics
from fontshow.inventory.types import FontBuildContext
from fontshow.inventory.validation import (
    has_style_leak_in_family,
    is_non_opentype_face,
    is_structurally_unloadable_face,
)
from fontshow.platform.font_discovery import (
    get_font_files_from_paths,
    get_installed_font_files,
    get_last_discovery_stats,
)
from fontshow.platform.fontconfig import fc_query_extract_many


def _positive_loadability_jobs(value: str) -> int:
    """
    Parse a positive loadability job count.

    Parameters
    ----------
    value : str
        Raw command-line argument value.

    Returns
    -------
    int
        Positive integer job count.

    Raises
    ------
    argparse.ArgumentTypeError
        Raised when ``value`` is not a positive integer.
    """
    try:
        jobs = int(value)
    except ValueError as exc:
        msg = "loadability jobs must be a positive integer"
        raise argparse.ArgumentTypeError(msg) from exc
    if jobs < 1:
        msg = "loadability jobs must be at least 1"
        raise argparse.ArgumentTypeError(msg)
    return jobs


def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register dump-fonts CLI arguments on an existing parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance to configure.

    Returns
    -------
    None
    """
    parser.description = (
        "Dump installed fonts into a canonical Fontshow JSON inventory."
    )
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "-c",
        "--cache-dir",
        type=Path,
        default=Path(".fontshow_cache"),
        help="Directory used to cache per-face fontTools results",
    )
    parser.add_argument(
        "-n",
        "--no-cache",
        action="store_true",
        help="Disable fontTools cache reuse",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        type=Path,
        help=(
            "Restrict discovery to one or more directories; disables system "
            "font discovery fallback"
        ),
    )
    parser.add_argument(
        "-i",
        "--include-fc-charset",
        action="store_true",
        help="Include Fontconfig-declared Unicode charset information (experimental, best-effort)",
    )
    parser.add_argument(
        "--loadability-jobs",
        type=_positive_loadability_jobs,
        default=DEFAULT_LOADABILITY_JOBS,
        help="Maximum parallel LuaLaTeX loadability batches",
    )
    add_common_arguments(
        parser,
        include_output=True,
        output_default=Path("font_inventory.json"),
        output_help="Output JSON file",
    )


def register_cli(parser) -> None:
    """
    Register dump-fonts CLI on a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance to configure.

    Returns
    -------
    None

    Notes
    -----
    Used by the top-level CLI dispatcher to bind the dump-fonts command
    to `main`.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


def run_dump_fonts(args) -> int:
    """
    Execute the dump-fonts pipeline.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code (0 for success, non-zero for failure).

    Raises
    ------
    OSError
        May propagate from filesystem writes such as cache directory
        creation or final inventory output.

    Notes
    -----
    This function performs the full dump pipeline and returns an exit code.
    It MUST NOT call sys.exit() and SHOULD NOT print directly.
    It orchestrates the full dump pipeline:

    1. Discover installed font files for the current platform.
    2. Extract per-face metadata using ``fontTools``.
    3. Optionally enrich metadata using FontConfig (Linux only).
    4. Build canonical font descriptors.
    5. Write the resulting JSON inventory to disk.

    All heavy lifting is delegated to dedicated helpers; this function is
    intentionally linear and side-effect driven (filesystem I/O).
    Best-effort Fontconfig enrichment failures are logged and downgraded
    to an empty enrichment map instead of aborting the command.
    """
    platform_name = platform.system().lower()
    cache_dir = args.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    inventory: dict[str, Any] = {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "input_inventory_tool": "dump_fonts",
            "input_inventory_tool_version": __version__,
            "inference_level": "none",
            "fonttools": {
                "available": bool(FONTTOOLS_AVAILABLE),
                "fontconfig_charset_included": bool(
                    args.include_fc_charset and IS_LINUX
                ),
                "version": (
                    __import__("fontTools").__version__
                    if FONTTOOLS_AVAILABLE
                    else "unavailable"
                ),
            },
            "run_environment": collect_platform_metadata(),
            "validation": {
                "lualatex": collect_latex_validation_metadata(),
            },
        },
        "fonts": [],
    }

    log_info(
        "font inventory generation started",
        extra={
            "output_path": str(args.output),
            "include_fc_charset": bool(args.include_fc_charset and IS_LINUX),
            "cache_dir": str(cache_dir),
        },
    )

    try:
        paths = getattr(args, "paths", None)
        font_files = (
            get_font_files_from_paths(paths)
            if paths is not None
            else get_installed_font_files()
        )
    except (OSError, ValueError) as exc:
        log_err(f"Font discovery failed: {exc}")
        return 1

    log_trace_cat(
        log,
        "perf",
        "font discovery metrics",
        extra={
            "fonts_found": len(font_files),
        },
    )

    discovery_stats = get_last_discovery_stats()

    # --- GLOBAL COUNTERS (must not reset per font file) ---
    total_faces = 0
    skipped_non_opentype = 0
    skipped_legacy_extension = discovery_stats.get("skipped_legacy_extension", 0)
    skipped_structurally_unloadable = 0
    style_leak_suspected = 0
    style_leak_details: list[str] = []
    warned_unloadable_fonts: set[Path] = set()

    fontconfig_by_path: dict[Path, dict[str, Any]] = {}
    if IS_LINUX:
        try:
            fontconfig_by_path = fc_query_extract_many(
                font_files,
                include_charset=args.include_fc_charset,
            )
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            log.warning(
                "fontconfig batch enrichment failed",
                extra={
                    "error_type": type(exc).__name__,
                    "error_reason": str(exc),
                },
            )
            fontconfig_by_path = {}

    for font_path in font_files:
        fontconfig: dict[str, Any] | None = None
        if IS_LINUX:
            fontconfig = fontconfig_by_path.get(font_path)

        try:
            faces = fonttools_extract_all(
                font_path,
                cache_dir=cache_dir,
                use_cache=not args.no_cache,
            )
        except (OSError, ValueError, TTLibError) as e:
            faces = [
                {
                    "ok": False,
                    "container": detect_font_container(font_path),
                    "ttc_index": None,
                    "error": f"Extraction failed: {e}",
                }
            ]

        for face in faces:
            total_faces += 1

            # Skip non-OpenType / bitmap fonts
            if is_non_opentype_face(face):
                skipped_non_opentype += 1
                log_warn(f"skipping non-opentype font: {font_path}")
                continue

            # Skip structurally unloadable faces (missing mandatory tables)
            if is_structurally_unloadable_face(face):
                skipped_structurally_unloadable += 1
                if font_path not in warned_unloadable_fonts:
                    log_warn(f"skipping structurally-unloadable font: {font_path}")
                    warned_unloadable_fonts.add(font_path)
                continue

            try:
                desc = build_font_descriptor(
                    FontBuildContext(
                        font_path=font_path,
                        platform_name=platform_name,
                        fonttools=face,
                        fontconfig=fontconfig,
                    )
                )

                if has_style_leak_in_family(desc):
                    style_leak_suspected += 1
                    style_leak_details.append(
                        " | ".join(
                            [
                                desc["path"],
                                desc["family"],
                                desc["subfamily"],
                                (
                                    "weight_class="
                                    f"{get_font_metrics(desc).get('weight_class')}"
                                ),
                                (
                                    "width_class="
                                    f"{get_font_metrics(desc).get('width_class')}"
                                ),
                                (
                                    "italic_angle="
                                    f"{get_font_metrics(desc).get('italic_angle')}"
                                ),
                            ]
                        )
                    )
                inventory["fonts"].append(desc)
            except (ValueError, TypeError, KeyError) as e:
                log_err(f"Descriptor build failed for {font_path}: {e}")
                return 1

    fonts_total = len(inventory.get("fonts", []))

    summary = {
        "total_fonts": fonts_total,
        "total_font_files": len(font_files),
        "total_faces_seen": total_faces,
        "skipped_discovery_legacy_files": skipped_legacy_extension,
        "skipped_face_non_opentype": skipped_non_opentype,
        "skipped_face_structurally_unloadable": skipped_structurally_unloadable,
        "style_leak_suspected": style_leak_suspected,
    }

    validation = inventory["metadata"]["validation"]["lualatex"]
    probe_and_persist_lualatex_loadability(
        inventory["fonts"],
        validation_metadata=validation,
        jobs=getattr(args, "loadability_jobs", DEFAULT_LOADABILITY_JOBS),
    )

    args.output.write_text(
        dumps_pretty(inventory, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    log_info(
        "font inventory generation completed",
        extra={
            "include_fc_charset": bool(args.include_fc_charset and IS_LINUX),
            "total_fonts": fonts_total,
        },
    )

    log_trace_cat(
        log,
        "perf",
        "inventory metrics",
        extra={"fonts_total": fonts_total},
    )

    log_info("dump-fonts summary", extra=summary)

    if style_leak_details:
        log_info(
            f"{style_leak_suspected} entries flagged for possible style leak",
            verbose="\n".join(
                [
                    "Possible style-leak entries:",
                    *style_leak_details,
                ]
            ),
        )

    log_info(
        f"Processed {total_faces} faces - {skipped_non_opentype} non-opentype skipped"
        f" - {style_leak_suspected} style-leak suspected",
        verbose=(
            f"Processed {total_faces} font faces — "
            f"{skipped_non_opentype} face skips (non-OpenType), "
            f"{skipped_legacy_extension} discovery skips (legacy extension), "
            f"{skipped_structurally_unloadable} face skips (structurally unloadable), "
            f"{style_leak_suspected} style-leak suspected, "
            f"{fonts_total} kept"
        ),
    )

    return 0


def _run_dump_fonts(args) -> int:
    """
    Injectable wrapper around the core dump-fonts implementation.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code returned by run_dump_fonts.

    Notes
    -----
    This indirection exists primarily to support tests that need to
    patch the core implementation without altering CLI wrapper logic.
    """
    return run_dump_fonts(args)


def main(args) -> int:
    """
    CLI wrapper for dump-fonts.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code.

    Notes
    -----
    Unexpected `TypeError` exceptions are treated as non-fatal to
    preserve the command's legacy wrapper semantics.

    Shared CLI quiet/verbose mode is configured before invoking the
    injectable runner.
    """
    set_cli_mode(getattr(args, "quiet", False), getattr(args, "verbose", False))

    exit_code = _run_dump_fonts(args)

    if exit_code == 0:
        log_ok(
            "dump-fonts completed successfully",
            verbose=f"wrote inventory to {args.output}",
        )
    else:
        log_err(f"dump-fonts failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="dump-fonts")
    build_parser(parser)
    args = parser.parse_args()
    sys.exit(main(args))
