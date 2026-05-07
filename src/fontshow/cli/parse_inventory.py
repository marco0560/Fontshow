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
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import cast

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
from fontshow.core.types import FontRef, InventoryDocument, JSONDict, ScriptISO
from fontshow.diagnostics.inventory_warnings import _emit_verbose_warnings
from fontshow.inventory.io import _validate_fonts_container
from fontshow.inventory.latex_validation_metadata import (
    collect_latex_validation_metadata,
)
from fontshow.inventory.loadability import (
    DEFAULT_LOADABILITY_JOBS,
    probe_and_persist_lualatex_render_variants,
    validate_persisted_lualatex_loadability,
)
from fontshow.inventory.metadata_processing import (
    _infer_and_attach_metadata,
    _process_charset,
    _process_language_metadata,
)
from fontshow.inventory.platform_metadata import collect_platform_metadata
from fontshow.inventory.schema_accessors import (
    MutableFontMapping,
    ensure_v13_typography,
)
from fontshow.inventory.schema_validation import _validate_inventory_schema_strict
from fontshow.inventory.script_analysis import infer_scripts
from fontshow.inventory.specimens import _specimen_generate_for_font
from fontshow.inventory.validation import _apply_schema_validation, validate_inventory
from fontshow.latex.policy import _format_script_display, _get_render_policy
from fontshow.ontology.unicode_tables import UNICODE_BLOCK_RANGES

# ============================================================
# REFACTORED MAIN FUNCTION
# ============================================================


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


def _unicode_blocks_from_text(text: str) -> dict[str, int]:
    """
    Count Unicode blocks represented in a specimen string.

    Parameters
    ----------
    text : str
        Specimen text to analyze.

    Returns
    -------
    dict[str, int]
        Per-block codepoint counts derived from visible characters in
        ``text``.
    """
    counts: Counter[str] = Counter()
    for ch in text:
        if not ch.strip():
            continue
        cp = ord(ch)
        for name, (start, end) in UNICODE_BLOCK_RANGES.items():
            if start <= cp <= end:
                counts[name] += 1
                break
    return dict(counts)


def _promote_primary_script(
    scripts: list[str],
    primary: str,
) -> list[str]:
    """
    Move a chosen primary script to the front of an ordered script list.

    Parameters
    ----------
    scripts : list[str]
        Existing ordered script list.
    primary : str
        Script code that should become the first element.

    Returns
    -------
    list[str]
        New ordered script list with ``primary`` in front and without
        duplicates.
    """
    ordered = [primary]
    ordered.extend(script for script in scripts if script != primary)
    return ordered


def _latin_block_count(blocks: dict[str, int]) -> int:
    """
    Return the amount of Latin-family coverage present in specimen blocks.

    Parameters
    ----------
    blocks : dict[str, int]
        Per-block counts derived from specimen text.

    Returns
    -------
    int
        Sum of counts belonging to Latin-family Unicode blocks.
    """
    return sum(
        count
        for block_name, count in blocks.items()
        if block_name == "Basic Latin" or block_name.startswith("Latin")
    )


def _non_latin_block_count(blocks: dict[str, int]) -> int:
    """
    Return the amount of non-Latin coverage present in specimen blocks.

    Parameters
    ----------
    blocks : dict[str, int]
        Per-block counts derived from specimen text.

    Returns
    -------
    int
        Sum of counts belonging to non-Latin Unicode blocks.
    """
    return sum(
        count
        for block_name, count in blocks.items()
        if not (block_name == "Basic Latin" or block_name.startswith("Latin"))
    )


def _generic_specimen_strategy(strategy: str | None) -> bool:
    """
    Return whether a specimen strategy should be treated as generic evidence.

    Parameters
    ----------
    strategy : str | None
        Persisted top-level specimen strategy.

    Returns
    -------
    bool
        True when the specimen was built from a generic fallback rather than
        trusted script-aware or internal evidence.
    """
    return strategy in {"cmap", "validated-fallback", "pua"}


def _normalized_script_list(value: object) -> list[str]:
    """
    Normalize one script list to uppercase ISO strings.

    Parameters
    ----------
    value : object
        Candidate raw script list read from inventory metadata.

    Returns
    -------
    list[str]
        Uppercase script codes with non-string entries removed.
    """
    if not isinstance(value, list):
        return []
    return [str(script).upper() for script in value if isinstance(script, str)]


def _preferred_specimen_primary(
    specimen_scripts: list[str],
    *,
    known_scripts: list[str],
    specimen_blocks: dict[str, int],
    strategy: str | None,
) -> str:
    """
    Resolve the preferred primary script inferred from specimen evidence.

    Parameters
    ----------
    specimen_scripts : list[str]
        Ordered scripts inferred directly from specimen text.
    known_scripts : list[str]
        Ordered scripts already known from coverage and inference data.
    specimen_blocks : dict[str, int]
        Unicode block counts derived from specimen text.
    strategy : str | None
        Persisted specimen strategy associated with the accepted sample.

    Returns
    -------
    str
        Chosen primary script code derived from the specimen.
    """
    specimen_primary = specimen_scripts[0]
    known_non_latin = [
        script
        for script in known_scripts
        if script not in {"LATN", "UNKNOWN"} and script != "PUAA"
    ]
    if specimen_primary != "LATN":
        return specimen_primary

    if _generic_specimen_strategy(strategy) and known_non_latin:
        non_latin_count = _non_latin_block_count(specimen_blocks)
        if non_latin_count >= 8:
            return known_non_latin[0]
        return specimen_primary

    if _generic_specimen_strategy(strategy):
        return specimen_primary

    known_script_set = set(known_scripts)
    for candidate in specimen_scripts[1:]:
        if candidate != "LATN" and candidate in known_script_set:
            return candidate
    return specimen_primary


def _reconcile_primary_script_with_specimen(
    font: FontRef,
    coverage: JSONDict,
    *,
    level: str,
) -> None:
    """
    Align primary-script metadata with the accepted specimen text.

    Parameters
    ----------
    font : dict[str, Any]
        Inventory entry updated in place.
    coverage : dict[str, Any]
        Coverage block whose explicit primary-script metadata may be
        updated.
    level : str
        Inference aggressiveness level used for specimen-text script
        analysis.

    Returns
    -------
    None

    Notes
    -----
    ``parse-inventory`` owns the semantic coherence contract between
    ``primary_script`` and ``typography.specimen_text``. When the
    accepted specimen clearly points to a different writing script than
    the currently selected primary script, this helper promotes the
    specimen-derived script to the explicit primary-script fields and
    reorders the explicit script lists accordingly.
    """
    typography = ensure_v13_typography(cast("MutableFontMapping", font))
    specimen = typography.get("specimen_text")
    if not isinstance(specimen, str) or not specimen.strip():
        return
    strategy = typography.get("specimen_strategy")
    if strategy == "pua":
        return

    specimen_blocks = _unicode_blocks_from_text(specimen)
    if not specimen_blocks:
        return

    specimen_scripts = [
        str(script).upper()
        for script in infer_scripts(
            {
                "unicode_blocks": specimen_blocks,
                "unicode": {"max": max(ord(ch) for ch in specimen)},
            },
            level,
        )
        if isinstance(script, str) and script and str(script).lower() != "unknown"
    ]
    if not specimen_scripts:
        return

    coverage_scripts = _normalized_script_list(coverage.get("scripts"))
    inference_raw = font.get("inference")
    inference = inference_raw if isinstance(inference_raw, dict) else {}
    inference_scripts = _normalized_script_list(inference.get("scripts"))
    known_scripts = coverage_scripts + inference_scripts
    specimen_primary = _preferred_specimen_primary(
        specimen_scripts,
        known_scripts=known_scripts,
        specimen_blocks=specimen_blocks,
        strategy=strategy if isinstance(strategy, str) else None,
    )

    current_primary = primary_script(font)
    if isinstance(current_primary, str) and current_primary.upper() == specimen_primary:
        return

    if (
        specimen_primary not in coverage_scripts
        and specimen_primary not in inference_scripts
    ):
        return

    coverage["primary_script"] = specimen_primary
    if coverage_scripts:
        coverage["scripts"] = _promote_primary_script(
            coverage_scripts, specimen_primary
        )

    if inference:
        inference["primary_script"] = specimen_primary
        if inference_scripts:
            inference["scripts"] = _promote_primary_script(
                inference_scripts,
                specimen_primary,
            )
    typography["primary_script"] = specimen_primary


def parse_inventory(
    data: InventoryDocument,
    level: str,
    *,
    strict_bcp47: bool = False,
    loadability_jobs: int = DEFAULT_LOADABILITY_JOBS,
) -> InventoryDocument:
    """
    Parse and enrich a font inventory structure.

    Parameters
    ----------
    data : InventoryDocument
        Inventory root document to validate, enrich, and update in place.
    level : str
        Inference aggressiveness level forwarded to metadata processing.
    strict_bcp47 : bool, optional
        Whether language-tag normalization must reject non-compliant
        BCP-47 values.
    loadability_jobs : int, optional
        Maximum parallel LuaLaTeX loadability batches used for render
        variant probing.

    Returns
    -------
    InventoryDocument
        Enriched inventory document.

    Notes
    -----
    This function operates on the inventory root. Individual elements of
    ``data["fonts"]`` are `FontRef` entries.
    """
    _apply_schema_validation(data)

    fonts = data["fonts"]

    metadata = data.get("metadata", {})

    log.info(
        "font inventory parsing started",
        extra={
            "schema_version": (
                metadata.get("schema_version") if isinstance(metadata, dict) else None
            ),
            "fonts_count": len(fonts),
        },
    )

    for font in fonts:
        font_path = font.get("path")
        family = font.get("family")
        style = font.get("subfamily")

        log.debug(
            "font entry parsing started",
            extra={"font_path": font_path, "family": family, "style": style},
        )

        coverage: JSONDict = font["coverage"]

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
        _reconcile_primary_script_with_specimen(
            font,
            coverage,
            level=level,
        )
        typography = ensure_v13_typography(cast("MutableFontMapping", font))
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
    validation["lualatex"] = collect_latex_validation_metadata()
    probe_and_persist_lualatex_render_variants(
        fonts,
        validation_metadata=validation["lualatex"],
        jobs=loadability_jobs,
    )
    loadability_errors = validate_persisted_lualatex_loadability(
        fonts,
        validation["lualatex"],
    )
    if loadability_errors:
        preview = "; ".join(loadability_errors[:5])
        suffix = "" if len(loadability_errors) <= 5 else "; ..."
        msg = f"LuaLaTeX loadability incomplete: {preview}{suffix}"
        raise ValueError(msg)

    log.info(
        "font inventory parsing completed",
        extra={"fonts_processed": len(fonts)},
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
        "-L",
        "--list-missing-language-coverage",
        action="store_true",
        help="Report fonts whose coverage.languages is empty and exit",
    )
    parser.add_argument(
        "-S",
        "--show-all-missing-language-coverage",
        action="store_true",
        help=(
            "When used with --list-missing-language-coverage, print one "
            "line per matching font instead of the summary only"
        ),
    )
    parser.add_argument(
        "-s",
        "--strict-bcp47",
        action="store_true",
        help="Reject non-compliant BCP-47 language tags",
    )
    parser.add_argument(
        "-l",
        "--loadability-jobs",
        type=_positive_loadability_jobs,
        default=DEFAULT_LOADABILITY_JOBS,
        help="Maximum parallel LuaLaTeX render-loadability batches",
    )
    add_common_arguments(
        parser,
        include_output=True,
        output_default=Path("font_inventory_enriched.json"),
        output_help="Output enriched JSON file",
    )


def register_cli(parser: argparse.ArgumentParser) -> None:
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


def _list_missing_language_coverage(
    data: InventoryDocument, *, show_all: bool = False
) -> int:
    """
    List fonts whose declared language coverage is missing.

    Parameters
    ----------
    data : InventoryDocument
        Inventory root containing a `fonts` list.

    show_all : bool, optional
        Whether to print one line per matching font instead of only the
        summary count.

    Returns
    -------
    int
        Exit code ``0`` after emitting the report.

    Notes
    -----
    The report is deterministic and preserves input order. When
    ``show_all`` is enabled, it prints one line per matching font and
    uses family name plus path to disambiguate duplicates.
    """
    fonts = data.get("fonts", [])

    missing: list[tuple[str, str]] = []
    for font in fonts:
        coverage = font.get("coverage")
        coverage_dict = coverage if isinstance(coverage, dict) else {}
        languages = coverage_dict.get("languages")
        if isinstance(languages, list) and languages:
            continue
        family = str(font.get("family", "")).strip() or "Unknown"
        path = str(font.get("path", "")).strip()
        missing.append((family, path))

    log_info(f"Fonts with missing declared language coverage: {len(missing)}")
    if not show_all:
        return 0

    for family, path in missing:
        if path:
            log_info(f"{family} | {path}")
        else:
            log_info(family)

    return 0


def run_parse_font_inventory(
    args: argparse.Namespace,
    *,
    parse_inventory_fn: Callable[..., InventoryDocument] = parse_inventory,
    validate_inventory_fn: Callable[[InventoryDocument], int] = validate_inventory,
    read_text_fn: Callable[[Path], str] | None = None,
    write_text_fn: Callable[[Path, str], None] | None = None,
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
    loadability_jobs = int(getattr(args, "loadability_jobs", DEFAULT_LOADABILITY_JOBS))

    log_trace_cat(
        log,
        "flow",
        "parse-inventory runner started",
        extra={
            "input": str(args.input),
            "output": str(args.output),
            "infer_level": getattr(args, "infer_level", None),
            "strict_bcp47": strict_bcp47,
            "loadability_jobs": loadability_jobs,
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

    raw_data: JSONDict = json.loads(read_text_fn(input_path))
    normalize_loaded_enums(raw_data)
    log_trace_cat(
        log,
        "io",
        "inventory JSON loaded",
        extra={
            "fonts": len(raw_data.get("fonts", [])),
            "schema_version": raw_data.get("metadata", {}).get("schema_version"),
        },
    )

    metadata = raw_data["metadata"]
    actual_env = metadata["run_environment"]

    expected_env = collect_platform_metadata()
    if actual_env != expected_env:
        log_err(
            "invalid inventory: 'metadata.run_environment' does not match current platform"
        )
        return 1
    try:
        _validate_inventory_schema_strict(raw_data)
    except ValueError as exc:
        log_err(f"schema validation failed: {exc}")
        return 1
    fonts = _validate_fonts_container(raw_data)
    if fonts is None:
        return 1

    data = cast("InventoryDocument", raw_data)
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
        return _list_missing_language_coverage(
            data,
            show_all=bool(
                getattr(args, "show_all_missing_language_coverage", False)
                or getattr(args, "verbose", False)
            ),
        )

    try:
        enriched = parse_inventory_fn(
            data,
            args.infer_level,
            strict_bcp47=strict_bcp47,
            loadability_jobs=loadability_jobs,
        )
    except ValueError as exc:
        log_err(f"parse-inventory failed: {exc}")
        return 1
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

    _emit_verbose_warnings(enriched, enabled=bool(getattr(args, "verbose", False)))

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


def _run_parse_inventory(args: argparse.Namespace) -> int:
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


def main(args: argparse.Namespace) -> int:
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
