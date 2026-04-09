"""
Fontshow create-catalog CLI command.

This module implements the catalog generation stage of the Fontshow
pipeline and provides the CLI entry point for the `create-catalog`
command.

Responsibilities
----------------
- Load and strictly validate the current inventory schema.
- Run semantic and platform validation checks before catalog generation.
- Orchestrate catalog preparation steps (filtering, grouping, diagnostics).
- Invoke catalog helpers that transform normalized font descriptors
  into deterministic LaTeX output.

Design principles
-----------------
The module acts as the orchestration layer for catalog generation.
Rendering logic lives in the `fontshow.catalog` domain modules,
while inventory analysis and validation belong to the
`fontshow.inventory` subsystem. This separation keeps the CLI entry
point focused on workflow coordination.

Architectural role
------------------
This module belongs to the **CLI interface layer** and coordinates the
catalog generation workflow between the inventory subsystem and the
catalog rendering helpers.
"""

import argparse
import platform
import shlex
import socket
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fontshow.catalog.document import generate_latex_with_report
from fontshow.catalog.loadability import filter_loadable_catalog_fonts_with_report
from fontshow.catalog.output import (
    _prepare_output_filename,
    _write_latex_output,
    get_unique_filename,
)
from fontshow.catalog.pipeline import (
    _configure_test_fonts,
    _filter_and_prepare_fonts,
    _handle_list_test_fonts,
    _run_inventory_diagnostics,
)
from fontshow.constants.runtime import DATE_STR, TIMESTAMP_STR
from fontshow.core.cli_utils import (
    add_common_arguments,
    log_err,
    log_ok,
    set_cli_mode,
)
from fontshow.core.global_constants import SCHEMA_VERSION
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.inventory.io import _load_inventory
from fontshow.platform.runtime import IS_WINDOWS

# Platform-specific imports (deferred, typing-safe)
if TYPE_CHECKING:
    import winreg as _winreg  # noqa: F401

    from fontshow.catalog.types import _FontDetail

    winreg: Any
else:
    try:
        import winreg  # type: ignore
    except ImportError:
        winreg = None

if not IS_WINDOWS:
    winreg = None  # Placeholder for non-Windows systems

# --- Configuration ---
TEST_FONTS: set[str] = set()
DEFAULT_INVENTORY = "font_inventory_enriched.json"


def _format_display_path(raw_path: str) -> str:
    """
    Render a CLI path argument in a stable, human-readable form.

    Parameters
    ----------
    raw_path : str
        Raw path value taken from parsed CLI arguments.

    Returns
    -------
    str
        Path relative to the current working directory when possible,
        otherwise the original string value.
    """
    candidate = Path(raw_path)
    if not raw_path:
        return raw_path
    if candidate.is_absolute():
        try:
            return str(candidate.relative_to(Path.cwd()))
        except ValueError:
            return raw_path
    return raw_path


def _render_invocation_command(args) -> str:
    """
    Reconstruct the create-catalog invocation from parsed arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments controlling catalog generation.

    Returns
    -------
    str
        Stable command line string suitable for human-readable output.
    """
    argv = ["fontshow", "create-catalog"]
    inventory = str(getattr(args, "inventory", "") or "")
    if inventory:
        argv.extend(["--inventory", _format_display_path(inventory)])

    output = getattr(args, "output", None)
    if output is not None:
        argv.extend(["--output", _format_display_path(str(output))])

    number = getattr(args, "number", None)
    if number is not None:
        argv.extend(["--number", str(number)])

    if getattr(args, "catalog_detail", "compact") != "compact":
        argv.extend(["--catalog-detail", str(args.catalog_detail)])
    if getattr(args, "indexed_navigation", False):
        argv.append("--indexed-navigation")
    for language in getattr(args, "language", None) or []:
        argv.extend(["--language", str(language)])
    for script in getattr(args, "script", None) or []:
        argv.extend(["--script", str(script)])
    for sort_key in getattr(args, "sort_by", None) or []:
        argv.extend(["--sort-by", str(sort_key)])

    if getattr(args, "test", False):
        argv.append("--test")
    if getattr(args, "list_test_fonts", False):
        argv.append("--list-test-fonts")

    test_fonts = getattr(args, "test_font", None) or []
    for test_font in test_fonts:
        argv.append("--test-font")
        if test_font != "__DEFAULT__":
            argv.append(str(test_font))

    if getattr(args, "quiet", False):
        argv.append("--quiet")
    if getattr(args, "verbose", False):
        argv.append("--verbose")

    return shlex.join(argv)


def _build_generation_metadata(args) -> dict[str, str]:
    """
    Build first-page metadata for the generated catalog document.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments controlling catalog generation.

    Returns
    -------
    dict[str, str]
        Mapping containing the formatted generation timestamp, CLI
        command line, operating system name, and hostname.
    """
    hostname = socket.gethostname().strip() or "unknown"
    return {
        "generation_timestamp": TIMESTAMP_STR,
        "command_line": _render_invocation_command(args),
        "system_name": platform.system() or "unknown",
        "hostname": hostname,
    }


def _generate_test_output(
    inventory_fonts: list[dict],
    limit: int | None = None,
    filter_test: bool = False,
) -> None:
    """
    Produce a small text file with parsing diagnostics for manual inspection.

    Parameters
    ----------
    inventory_fonts : list[dict]
        Inventory font descriptors used to derive family-level test
        output and associated file paths.
    limit : int | None, optional
        If positive, keep the first N items; if negative, keep the last |N|
        items; if None, no limit is applied.
    filter_test : bool, optional
        If True, include only fonts whose names match substrings listed
        in `TEST_FONTS`.

    Returns
    -------
    None

    Raises
    ------
    OSError
        Propagates filesystem errors raised while writing the auxiliary
        diagnostics file.

    Notes
    -----
    The generated file groups inventory data at the family level and
    writes a compact diagnostic view intended for manual inspection.
    Output filenames are generated via `get_unique_filename`.
    """
    details: list[_FontDetail] = []

    families = {
        str(font_item.get("family", "")).strip()
        for font_item in inventory_fonts
        if font_item.get("family")
    }

    for family in sorted(families):
        details.append(
            {
                "raw_line": family,
                "extracted_names": [family],
                "base_names": [family],
            }
        )

    if filter_test:
        details = [
            item
            for item in details
            if any(name in TEST_FONTS for name in item["base_names"])
        ]

    if limit:
        details = details[:limit] if limit > 0 else details[limit:]

    # Sort alphabetically for the first base name
    details.sort(key=lambda x: x["base_names"][0].lower() if x["base_names"] else "")

    base_name = f"TODF_{platform.system()}_{DATE_STR}"
    try:
        test_filename = get_unique_filename(base_name, "txt")
    except ValueError as e:
        log_err(f"Error generating test file: {e}")
        return
    with Path(test_filename).open("w", encoding="utf-8") as f:
        for item in details:
            family = item["base_names"][0]

            f.write(f"Raw line: {family}\n")
            f.write(f"Extracted names: {family}\n")
            f.write(f"Base names: {family}\n")

            # List all files belonging to this family
            paths = sorted(
                str(font_item.get("path", "")).strip()
                for font_item in inventory_fonts
                if isinstance(font_item, dict)
                and str(font_item.get("family", "")).strip() == family
                and font_item.get("path")
            )

            if paths:
                f.write("Files:\n")
                for p in paths:
                    f.write(f"  - {p}\n")
            else:
                f.write("Files: (none)\n")

            f.write("\n")

    log_ok(f"Test file generated: {test_filename}")


# ============================================================
# Platform integration and CLI orchestration
# ============================================================
#
# This section contains:
# - platform-specific helpers (Linux / Windows),
# - deterministic inventory-only operation,
# - LaTeX escaping utilities,
# - the CLI entry point (main).
#
# Design notes:
# - Platform detection is best-effort and defensive.
# - Failures in discovery or rendering provoke rejection of the specific
#   font but do not abort the whole process,
# - The CLI is intentionally thin: orchestration only, no business logic.
# ============================================================


def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register create-catalog CLI arguments on an existing parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Argument parser to be configured with create-catalog options.

    Returns
    -------
    None

    Notes
    -----
    This command supports diagnostic modes (`--test`,
    `--list-test-fonts`) in addition to the normal catalog-generation
    path.
    """
    parser.description = "Generate system font catalog in LaTeX"
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Generate auxiliary text file with parsing details",
    )
    parser.add_argument(
        "-T",
        "--test-font",
        nargs="?",
        const="__DEFAULT__",
        action="append",
        metavar="FONT_NAME",
        help=(
            "Restrict processing to a test font subset. "
            "If used without argument, enables the default test font set. "
            "If used with a font name, adds it to the test font set. "
            "Can be repeated multiple times."
        ),
    )
    parser.add_argument(
        "-l",
        "--list-test-fonts",
        action="store_true",
        help=(
            "List the effective test font set and the installed fonts matching it, then exit "
            "without generating the LaTeX catalog."
        ),
    )
    parser.add_argument(
        "-i",
        "--inventory",
        type=str,
        default=DEFAULT_INVENTORY,
        help="Path to font inventory JSON file to be used.",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        help="Limit the number of processed fonts to the first N (if positive) or the last |N| (if negative)",
    )
    parser.add_argument(
        "-D",
        "--catalog-detail",
        choices=("compact", "extended"),
        default="compact",
        help=(
            "Catalog output detail level. Use 'compact' to keep short "
            "family and specimen labels, or 'extended' to include the full "
            "metadata blocks."
        ),
    )
    parser.add_argument(
        "-I",
        "--indexed-navigation",
        action="store_true",
        help=(
            "Enable indexed navigation output with a clickable table of "
            "contents and end-of-document navigation index."
        ),
    )
    parser.add_argument(
        "-L",
        "--language",
        action="append",
        metavar="LANG",
        help=(
            "Restrict output to fonts matching at least one selected "
            "language tag. Repeatable and combined AND-wise with other "
            "selector families."
        ),
    )
    parser.add_argument(
        "-S",
        "--script",
        action="append",
        metavar="SCRIPT",
        help=(
            "Restrict output to fonts matching at least one selected "
            "script tag. Repeatable and combined AND-wise with other "
            "selector families."
        ),
    )
    parser.add_argument(
        "-s",
        "--sort-by",
        action="append",
        choices=("language", "script"),
        metavar="FIELD",
        help=(
            "Add a deterministic catalog sort key before the default "
            "family ordering. Repeat to sort by multiple metadata "
            "fields in CLI order."
        ),
    )
    add_common_arguments(
        parser,
        include_output=True,
        output_default=None,
        output_help="Output LaTeX .tex file (optional; default is an auto-generated unique name)",
    )


def register_cli(parser) -> None:
    """
    Register create-catalog CLI arguments.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Argument parser to be configured for the create-catalog command.

    Returns
    -------
    None

    Notes
    -----
    Used by the top-level Fontshow dispatcher.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


# ------------------------------------------------------------------
# INVENTORY / FONT SOURCE
# ------------------------------------------------------------------


def _resolve_inventory_path(args) -> Path | None:
    """
    Resolve the inventory file path according to CLI semantics.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the `inventory` option.

    Returns
    -------
    pathlib.Path | None
        Resolved inventory path if found, otherwise None.

    Notes
    -----
    Resolution priority:
    1. Explicit --inventory path.
    2. DEFAULT_INVENTORY if it exists.
    3. None if no valid inventory can be resolved.

    An explicit ``--inventory`` value is returned as-is without checking
    for existence; existence is validated by the caller.
    """
    if args.inventory:
        return Path(args.inventory)

    default = Path(DEFAULT_INVENTORY)
    if default.exists():
        return default

    return None


def run_create_catalog(args) -> int:
    """
    Execute the create-catalog workflow.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments controlling catalog generation.

    Returns
    -------
    int
        Process exit code:
        - 0 on success
        - non-zero on failure

    Raises
    ------
    Exception
        Unexpected exceptions from downstream helpers are allowed to
        propagate to `main`, which converts them into exit code ``2``.

    Notes
    -----
    Workflow:
    - Configure TEST_FONTS.
    - Handle --list-test-fonts early exit.
    - Prepare output filename.
    - Resolve inventory source.
    - Run diagnostics (inventory mode only).
    - Filter and prepare fonts.
    - Generate and write LaTeX output.

    Behavior is identical to the pre-refactor implementation.
    I/O failures during final output writing are caught and converted to
    exit code ``1``.
    """
    global TEST_FONTS

    # --------------------------------------------------------------
    # TEST FONT CONFIGURATION
    # --------------------------------------------------------------
    TEST_FONTS = _configure_test_fonts(args)

    # --------------------------------------------------------------
    # OUTPUT FILE PREPARATION
    # --------------------------------------------------------------
    output_arg = getattr(args, "output", None)
    if output_arg is not None:
        output_filename = str(output_arg)
    else:
        rc, out_name = _prepare_output_filename()
        if rc != 0 or out_name is None:
            return 1
        output_filename = out_name

    # --------------------------------------------------------------
    # INVENTORY / FONT SOURCE
    # --------------------------------------------------------------
    inv_path = _resolve_inventory_path(args)

    if not inv_path or not inv_path.exists():
        log_err(
            "Font inventory not found. Catalog generation requires a valid "
            f"v{SCHEMA_VERSION} inventory."
        )
        return 1  # MUST fail deterministically even in --quiet mode

    rc, fonts = _load_inventory(inv_path)
    if rc != 0:
        return 1

    if args.test:
        _generate_test_output(fonts, args.number, bool(TEST_FONTS))

    if args.list_test_fonts:
        return _handle_list_test_fonts(TEST_FONTS, fonts)

    # --------------------------------------------------------------
    # FONT FILTERING / OUTPUT PREPARATION
    # --------------------------------------------------------------
    fonts = _filter_and_prepare_fonts(fonts, args, TEST_FONTS)

    # Invariant guard: rendering requires normalized font descriptors.
    if not isinstance(fonts, list) or any(not isinstance(f, dict) for f in fonts):
        log_err("Internal error: invalid font descriptor list after filtering.")
        return 1

    # --------------------------------------------------------------
    # CONSISTENCY DIAGNOSTICS (effective render set)
    # --------------------------------------------------------------
    _run_inventory_diagnostics(fonts)

    loadability_result = filter_loadable_catalog_fonts_with_report(fonts)
    latex_content = generate_latex_with_report(
        loadability_result.kept,
        excluded_fonts=loadability_result.excluded,
        catalog_detail=args.catalog_detail,
        indexed_navigation=bool(getattr(args, "indexed_navigation", False)),
        generation_metadata=_build_generation_metadata(args),
    )

    # --------------------------------------------------------------
    # WRITE OUTPUT
    # --------------------------------------------------------------
    try:
        _write_latex_output(output_filename, latex_content)
    except OSError as exc:
        log_err(f"Failed to write output file: {exc}")
        return 1

    log_trace_cat(
        log,
        "io",
        "catalog tex written",
        extra={
            "path": str(output_filename),
        },
    )
    log_trace_cat(
        log,
        "flow",
        "create-catalog completed",
        extra={
            "fonts_used": len(fonts),
            "output": str(output_filename),
        },
    )

    return 0


def _run_create_catalog(args) -> int:
    """
    Indirection layer for CLI testing.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments forwarded to the core implementation.

    Returns
    -------
    int
        Exit code returned by `run_create_catalog`.

    Notes
    -----
    Exists so CLI tests can monkeypatch this function without
    modifying the core implementation.
    """
    return run_create_catalog(args)


def main(args) -> int:
    """
    CLI entrypoint for create-catalog.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments controlling catalog execution.

    Returns
    -------
    int
        Process exit code returned by the catalog workflow.

    Notes
    -----
    Handles user-facing output and delegates execution to the core
    implementation. Unexpected exceptions are converted to exit code 2.
    """
    set_cli_mode(getattr(args, "quiet", False), getattr(args, "verbose", False))

    try:
        exit_code = _run_create_catalog(args)
    except Exception as exc:  # noqa: BLE001
        # (Crash barrier: convert unexpected failure → exit code 2)
        log_err(f"create-catalog failed: {exc}")
        log_trace_cat(
            log,
            "perf",
            "catalog metrics",
            extra={
                "exit_code": 2,
                "exception": True,
            },
        )
        return 2

    if exit_code == 0:
        log_ok("Done", verbose="catalog created successfully")
    else:
        # Do not mask failure - CLI nust propagate real exit code even in --quiet mode
        log_err(f"create-catalog failed with exit code {exit_code}")

    log_trace_cat(
        log,
        "perf",
        "catalog metrics",
        extra={
            "exit_code": exit_code,
        },
    )

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="create-catalog")
    build_parser(parser)
    args = parser.parse_args()
    sys.exit(main(args))
