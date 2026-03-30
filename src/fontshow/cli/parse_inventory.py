"""
Fontshow parse-inventory CLI command.

This module implements the inventory enrichment stage of the Fontshow
pipeline. It reads a raw inventory produced by `dump-fonts`, performs
deterministic metadata inference, and produces a normalized inventory
ready for validation and catalog generation.

Responsibilities
----------------
- Load and validate the structure of a raw Fontshow inventory.
- Perform deterministic inference of scripts and languages.
- Enrich inventory entries with derived metadata.
- Serialize the normalized inventory for downstream processing.

Design principles
-----------------
This stage operates exclusively on JSON inventory data and performs
no direct inspection of font binaries. All inference logic must be
deterministic so that identical inputs produce identical outputs.

Architectural role
------------------
This module belongs to the **CLI interface layer** and implements the
inventory enrichment stage of the Fontshow processing pipeline.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fontshow import __version__
from fontshow.catalog.labels import primary_script
from fontshow.core.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    set_cli_mode,
)
from fontshow.core.global_constants import SCHEMA_VERSION
from fontshow.core.json_boundary import normalize_loaded_enums
from fontshow.core.json_format import dumps_pretty
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import ScriptISO
from fontshow.diagnostics.inventory_warnings import _emit_verbose_warnings
from fontshow.inventory.io import _validate_fonts_container
from fontshow.inventory.latex_validation_metadata import (
    collect_latex_validation_metadata,
)
from fontshow.inventory.loadability import inventory_has_attempted_lualatex_validation
from fontshow.inventory.metadata_processing import (
    _infer_and_attach_metadata,
    _process_charset,
    _process_language_metadata,
)
from fontshow.inventory.platform_metadata import collect_platform_metadata
from fontshow.inventory.schema_accessors import ensure_v13_typography
from fontshow.inventory.schema_validation import _validate_inventory_schema_strict
from fontshow.inventory.specimens import _specimen_generate_for_font
from fontshow.inventory.validation import _apply_schema_validation, validate_inventory
from fontshow.latex.policy import _format_script_display, _get_render_policy

# ============================================================
# REFACTORED MAIN FUNCTION
# ============================================================


def parse_inventory(
    data: dict[str, Any],
    level: str,
    *,
    strict_bcp47: bool = False,
) -> dict[str, Any]:
    """
    Parse and enrich a font inventory structure.

    Parameters
    ----------
    data : dict[str, Any]
        Raw inventory structure to validate, enrich, and update in place.
    level : str
        Inference aggressiveness level forwarded to metadata processing.
    strict_bcp47 : bool, optional
        Whether language-tag normalization must reject non-compliant
        BCP-47 values.

    Returns
    -------
    dict[str, Any]
        Enriched inventory structure with updated metadata and per-font
        inferred fields.

    Raises
    ------
    ValueError
        Propagated when schema validation or downstream metadata helpers
        reject the input inventory.

    Notes
    -----
    Refactored version:
    - reduced complexity
    - separated concerns
    - behavior unchanged
    The function validates the input first, then processes charset,
    inference, language metadata, and specimen generation for each font
    before updating top-level inventory metadata.
    """
    _apply_schema_validation(data)

    log.info(
        "font inventory parsing started",
        extra={
            "schema_version": data.get("schema_version"),
            "fonts_count": len(data.get("fonts", [])),
        },
    )

    for font in data.get("fonts", []):
        font_path = font.get("path")
        family = font.get("family")
        style = font.get("subfamily")

        log.debug(
            "font entry parsing started",
            extra={"font_path": font_path, "family": family, "style": style},
        )

        coverage: dict[str, Any] = font.get("coverage", {}) or {}

        _process_charset(font, coverage, font_path)

        _infer_and_attach_metadata(
            font,
            coverage,
            level=level,
            font_path=font_path,
        )

        _process_language_metadata(
            font,
            coverage,
            strict_bcp47=strict_bcp47,
        )

        _specimen_generate_for_font(font, coverage, font_path)
        typography = ensure_v13_typography(font)
        script = primary_script(font)
        script_iso = script.upper() if isinstance(script, str) and script else ""
        lang, fontspec_opts = _get_render_policy(ScriptISO(script_iso))
        typography["primary_script"] = script or None
        typography["script_display_name"] = (
            _format_script_display(script_iso) if script_iso else None
        )
        typography["render_policy"] = {
            "polyglossia_language": lang or None,
            "fontspec_opts": fontspec_opts or None,
        }
        if isinstance(font.get("coverage"), dict) and font.get("coverage", {}).get(
            "script_coverage_from_charset"
        ):
            typography["script_source"] = "charset_coverage"
        elif isinstance(font.get("inference"), dict) and font.get("inference", {}).get(
            "scripts"
        ):
            typography["script_source"] = "inference"
        elif isinstance(font.get("coverage"), dict) and font.get("coverage", {}).get(
            "scripts"
        ):
            typography["script_source"] = "coverage"
        else:
            typography["script_source"] = None

    metadata = data.setdefault("metadata", {})
    metadata["schema_version"] = SCHEMA_VERSION
    metadata["inference_level"] = level
    metadata.setdefault("input_inventory_tool", "parse_font_inventory")
    metadata.setdefault("input_inventory_tool_version", __version__)
    validation = metadata.setdefault("validation", {})
    if not isinstance(validation, dict):
        validation = {}
        metadata["validation"] = validation
    if not inventory_has_attempted_lualatex_validation(metadata):
        validation["lualatex"] = collect_latex_validation_metadata()

    log.info(
        "font inventory parsing completed",
        extra={"fonts_processed": len(data.get("fonts", []))},
    )

    return data


# ============================================================
# CLI
# ============================================================


def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register parse-inventory CLI arguments on an existing parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance to configure for the parse-inventory command.

    Returns
    -------
    None
    """
    parser.description = (
        "Parse and enrich a Fontshow font_inventory.json with deterministic inference."
    )
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=None,
        help="Input inventory JSON file",
    )
    parser.add_argument(
        "-i",
        "--infer-level",
        choices=["conservative", "medium", "aggressive"],
        default="medium",
        help="Inference aggressiveness level",
    )
    parser.add_argument(
        "-I",
        "--validate-inventory",
        action="store_true",
        help="Validate inventory structure and exit (no output generation)",
    )
    parser.add_argument(
        "--list-missing-language-coverage",
        action="store_true",
        help="List fonts whose coverage.languages is empty and exit",
    )
    parser.add_argument(
        "-s",
        "--strict-bcp47",
        action="store_true",
        help="Reject non-compliant BCP-47 language tags",
    )
    add_common_arguments(
        parser,
        include_output=True,
        output_default=Path("font_inventory_enriched.json"),
        output_help="Output enriched JSON file",
    )


def register_cli(parser) -> None:
    """
    Register parse-inventory CLI arguments.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance configured by the top-level dispatcher.

    Returns
    -------
    None

    Notes
    -----
    This function is used by the top-level fontshow dispatcher.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


# ============================================================
# Helper: default I/O adapters (test-friendly)
# ============================================================


def _default_read_text(p: Path) -> str:
    """
    Read text from a path using the default CLI encoding policy.

    Parameters
    ----------
    p : Path
        Path to the input text file.

    Returns
    -------
    str
        File contents decoded as UTF-8.

    Raises
    ------
    OSError
        Propagates filesystem errors raised while reading the file.
    """
    return p.read_text(encoding="utf-8")


def _default_write_text(p: Path, s: str) -> None:
    """
    Write text to a path using the default CLI encoding policy.

    Parameters
    ----------
    p : Path
        Destination path for the text payload.
    s : str
        Text content to write.

    Returns
    -------
    None

    Raises
    ------
    OSError
        Propagates filesystem errors raised while writing the file.
    """
    p.write_text(s, encoding="utf-8")


def _list_missing_language_coverage(data: dict[str, Any]) -> int:
    """
    List fonts whose declared language coverage is missing.

    Parameters
    ----------
    data : dict[str, Any]
        Inventory root containing a `fonts` list.

    Returns
    -------
    int
        Exit code ``0`` after emitting the report.

    Notes
    -----
    The report is deterministic:
    - preserves input order,
    - prints one line per matching font,
    - uses family name plus path to disambiguate duplicates.
    """
    fonts = data.get("fonts", [])
    if not isinstance(fonts, list):
        log_err("invalid inventory: missing or invalid 'fonts' list")
        return 1

    missing: list[tuple[str, str]] = []
    for font in fonts:
        if not isinstance(font, dict):
            continue
        coverage = font.get("coverage")
        coverage_dict = coverage if isinstance(coverage, dict) else {}
        languages = coverage_dict.get("languages")
        if isinstance(languages, list) and languages:
            continue
        family = str(font.get("family", "")).strip() or "Unknown"
        path = str(font.get("path", "")).strip()
        missing.append((family, path))

    log_info(f"Fonts with missing declared language coverage: {len(missing)}")
    for family, path in missing:
        if path:
            log_info(f"{family} | {path}")
        else:
            log_info(family)

    return 0


# ============================================================
# REFACTORED MAIN RUNNER
# ============================================================


def run_parse_font_inventory(
    args,
    *,
    parse_inventory_fn=parse_inventory,
    validate_inventory_fn=validate_inventory,
    read_text_fn=None,
    write_text_fn=None,
) -> int:
    """
    Run the internal parse-font-inventory CLI flow.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments controlling input, output, validation-only
        mode, and inference strictness.
    parse_inventory_fn : callable, optional
        Injectable inventory enrichment function used for testing.
    validate_inventory_fn : callable, optional
        Injectable validation function used in validate-only mode.
    read_text_fn : callable | None, optional
        Optional file-reading adapter. Defaults to `_default_read_text`.
    write_text_fn : callable | None, optional
        Optional file-writing adapter. Defaults to `_default_write_text`.

    Returns
    -------
    int
        Process exit code for the parse-inventory workflow.

    Raises
    ------
    json.JSONDecodeError
        May propagate indirectly from the injected read/parse path if
        malformed JSON is not intercepted by the caller.
    OSError
        May propagate from injected read or write adapters.
    ValueError
        May propagate from `parse_inventory_fn` if enrichment or strict
        validation rejects the loaded inventory.

    Notes
    -----
    Refactored version:
    - reduced complexity
    - helpers extracted
    - behavior unchanged
    The runner validates platform compatibility and schema integrity
    before either executing validate-only mode or producing an enriched
    inventory and writing it to disk.
    """
    strict_bcp47 = bool(getattr(args, "strict_bcp47", False))

    log_trace_cat(
        log,
        "flow",
        "parse-inventory runner started",
        extra={
            "input": str(args.input),
            "output": str(args.output),
            "infer_level": getattr(args, "infer_level", None),
            "strict_bcp47": strict_bcp47,
            "validate_only": bool(getattr(args, "validate_inventory", False)),
            "list_missing_language_coverage": bool(
                getattr(args, "list_missing_language_coverage", False)
            ),
        },
    )

    read_text_fn = read_text_fn or _default_read_text
    write_text_fn = write_text_fn or _default_write_text

    if args.input is None:
        input_path = (
            Path("font_inventory_enriched.json")
            if getattr(args, "validate_inventory", False)
            else Path("font_inventory.json")
        )
    else:
        input_path = args.input
    if not input_path.exists():
        log_err(f"input file not found: {input_path}")
        log_err("Hint: run dump_fonts.py first to generate the inventory.")
        return 1

    log.debug("inference level enabled", extra={"infer_level": args.infer_level})

    data: dict[str, Any] = json.loads(read_text_fn(input_path))
    normalize_loaded_enums(data)
    log_trace_cat(
        log,
        "io",
        "inventory JSON loaded",
        extra={
            "fonts": len(data.get("fonts", [])),
            "schema_version": data.get("metadata", {}).get("schema_version"),
        },
    )

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        log_err("invalid inventory: missing or invalid 'metadata' object")
        return 1

    actual_env = metadata.get("run_environment")
    if not isinstance(actual_env, dict):
        log_err("invalid inventory: missing or invalid 'metadata.run_environment'")
        return 1

    expected_env = collect_platform_metadata()
    if actual_env != expected_env:
        log_err(
            "invalid inventory: 'metadata.run_environment' does not match current platform"
        )
        return 1
    try:
        _validate_inventory_schema_strict(data)
    except ValueError as exc:
        log_err(f"schema validation failed: {exc}")
        return 1
    fonts = _validate_fonts_container(data)
    if fonts is None:
        return 1

    if args.validate_inventory:
        log_trace_cat(
            log,
            "flow",
            "validate-only mode",
            extra={
                "fonts": len(data.get("fonts", [])),
            },
        )

        rc = int(validate_inventory_fn(data))

        if rc != 0:
            log_info("Inventory validation failed with errors")

        return rc

    if getattr(args, "list_missing_language_coverage", False):
        log_trace_cat(
            log,
            "flow",
            "list-missing-language-coverage mode",
            extra={
                "fonts": len(data.get("fonts", [])),
            },
        )
        return _list_missing_language_coverage(data)

    enriched = parse_inventory_fn(
        data,
        args.infer_level,
        strict_bcp47=args.strict_bcp47,
    )
    log_trace_cat(
        log,
        "flow",
        "inventory enriched",
        extra={
            "fonts": len(enriched.get("fonts", [])),
            "schema_version": enriched.get("metadata", {}).get("schema_version"),
        },
    )

    try:
        # Validate normalized JSON, not Python object
        normalized_for_validation = json.loads(
            dumps_pretty(enriched, indent=2, ensure_ascii=False)
        )
        _validate_inventory_schema_strict(normalized_for_validation)
    except ValueError as exc:
        log_err(f"schema validation failed (output): {exc}")
        return 1

    write_text_fn(
        args.output,
        dumps_pretty(enriched, indent=2, ensure_ascii=False),
    )
    log_trace_cat(
        log,
        "io",
        "enriched inventory written",
        extra={
            "path": str(args.output),
            "fonts": len(enriched.get("fonts", [])),
        },
    )
    log_trace_cat(
        log,
        "flow",
        "verbose warning emission started",
        extra={
            "fonts": len(enriched.get("fonts", [])),
        },
    )

    _emit_verbose_warnings(enriched)

    log_ok("Done.", f"Inventory written to {args.output}")
    log_trace_cat(
        log,
        "flow",
        "parse-inventory runner completed",
        extra={
            "fonts": len(enriched.get("fonts", [])),
            "output": str(args.output),
        },
    )

    return 0


def _run_parse_inventory(args) -> int:
    """
    Indirection layer for CLI testing.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments forwarded to the injectable runner.

    Returns
    -------
    int
        Exit code returned by `run_parse_font_inventory`.

    Notes
    -----
    This function exists so CLI tests can monkeypatch it
    without touching the core implementation.
    """
    return run_parse_font_inventory(args)


def main(args) -> int:
    """
    Public CLI entrypoint (kept stable).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments controlling parse-inventory execution.

    Returns
    -------
    int
        Process exit code returned by the CLI workflow.

    Notes
    -----
    Thin wrapper around the injectable runner.
    Unexpected `TypeError` exceptions are converted into exit code ``2``
    after user-facing error reporting and performance tracing.
    """
    set_cli_mode(getattr(args, "quiet", False), getattr(args, "verbose", False))

    from time import perf_counter

    t0 = perf_counter()
    try:
        exit_code = _run_parse_inventory(args)
        log_trace_cat(
            log,
            "perf",
            "inventory parse metrics",
            extra={
                "exit_code": exit_code,
            },
        )
    except TypeError as exc:
        if not getattr(args, "quiet", False):
            log_err(f"parse-inventory failed: {exc}")
        log_trace_cat(
            log,
            "perf",
            "inventory parse metrics",
            extra={
                "exit_code": 2,
                "exception": True,
            },
        )
        exit_code = 2
    finally:
        duration_ms = int((perf_counter() - t0) * 1000)
        log_trace_cat(
            log,
            "perf",
            "parse-inventory timing",
            extra={
                "duration_ms": duration_ms,
                "exit_code": exit_code,
            },
        )

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="parse-inventory")
    build_parser(parser)
    args = parser.parse_args()
    sys.exit(main(args))
