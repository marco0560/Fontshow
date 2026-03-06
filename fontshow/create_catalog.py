"""
Fontshow create-catalog module.

This module implements the LaTeX catalog generation stage of the Fontshow
pipeline.

Responsibilities
----------------
- Load and strictly validate a schema v1.2 inventory.
- Enforce platform compatibility constraints.
- Perform semantic validation.
- Transform normalized font descriptors into deterministic LaTeX output.
- Provide CLI orchestration for the `create-catalog` command.

Design constraints
------------------
- Pure rendering stage: no font binary inspection.
- Inventory-driven: all semantic information originates from JSON.
- Deterministic output: stable ordering and identifiers.
- LaTeX-first: optimized for LuaLaTeX workflows.
- Whitespace-sensitive templates: LaTeX blocks must not be modified
  unintentionally.

Primary entry points
--------------------
- `run_create_catalog(args)`
- `generate_latex(font_list)`

All rendering decisions must operate exclusively on normalized font
descriptors.
"""

import argparse
import json
import platform
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from fontshow.catalog.document import generate_latex
from fontshow.catalog.metadata import font_family
from fontshow.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.constants.catalog import DEFAULT_TEST_FONTS
from fontshow.global_constants import SCHEMA_VERSION
from fontshow.inventory.io import as_font_desc_list
from fontshow.inventory.semantic_validation import enforce_semantic_validation
from fontshow.json_boundary import normalize_loaded_enums
from fontshow.logging_utils import log, log_trace_cat
from fontshow.platform.runtime import IS_WINDOWS
from fontshow.platform_metadata import collect_platform_metadata
from fontshow.types import (
    CatalogFontEntryV12,
    Severity,
)

# Platform-specific imports (deferred, typing-safe)
if TYPE_CHECKING:
    import winreg as _winreg  # noqa: F401

    winreg: Any
else:
    try:
        import winreg  # type: ignore
    except ImportError:
        winreg = None

if not IS_WINDOWS:
    winreg = None  # Placeholder for non-Windows systems

# --- Configuration ---
DATE_STR = datetime.now().strftime("%Y%m%d")
TEST_FONTS: set[str] = set()
DEFAULT_INVENTORY = "font_inventory_enriched.json"


# --------------------------------------------
# General helper functions
# --------------------------------------------


def get_unique_filename(base_name: str, extension: str) -> str:
    """
    Generate a unique filename by appending a three-digit counter (000–999).

    Parameters
    ----------
    base_name : str
        Base filename without extension.
    extension : str
        File extension without leading dot.

    Returns
    -------
    str
        A filename of the form:
            <base_name>_<NNN>.<extension>
        where NNN is the first available counter between 000 and 999.

    Raises
    ------
    ValueError
        If no available filename is found after 1000 attempts.
    """
    for i in range(1000):
        suffix = f"_{i:03d}"
        filename = f"{base_name}{suffix}.{extension}"
        if not Path(filename).exists():
            return filename
    msg = f"Impossibile trovare un nome file unico per {base_name}.{extension} dopo 1000 tentativi."
    raise ValueError(msg)


def group_fonts_by_family(
    fonts: list[CatalogFontEntryV12],
) -> list[CatalogFontEntryV12]:
    """
    Reduce a list of font entries to one entry per family.

    Parameters
    ----------
    fonts : list[dict]
        List of font descriptor dictionaries.

    Returns
    -------
    list[dict]
        List containing a single representative font for each family.
        The first encountered font per family is preserved, and the
        order of first occurrence is maintained.
    """
    families: OrderedDict[str, Any] = OrderedDict()
    for font in fonts:
        fam = font_family(font)
        families.setdefault(fam, []).append(font)
    result = [entries[0] for entries in families.values()]

    log_trace_cat(
        log,
        "flow",
        "fonts grouped by family",
        extra={
            "families": len(result),
            "input_fonts": len(fonts),
        },
    )

    return result


# ============================================================
# Inventory loading (pipeline mode)
# ============================================================


def load_font_inventory(path: Path) -> list[dict]:
    """
    Load and validate a Fontshow inventory file.

    Parameters
    ----------
    path : pathlib.Path
        Path to the inventory JSON file.

    Returns
    -------
    list[dict]
        List of normalized font descriptor dictionaries.

    Raises
    ------
    RuntimeError
        If validation fails or the inventory is incompatible.

    Notes
    -----
    Delegates strict validation to `_load_inventory()` while preserving
    the exception-based contract expected by library callers.
    """
    rc, fonts = _load_inventory(path, require_platform=False)

    if rc != 0:
        msg = "Invalid or incompatible inventory"
        raise RuntimeError(msg)

    return fonts


def _normalize_inventory_paths(inventory: dict) -> None:
    """
    Normalize inventory font entries so that `identity.file` is present when
    a file path is available.

    Parameters
    ----------
    inventory : dict
        Inventory dictionary expected to contain a `fonts` list with font
        descriptor mappings.

    Returns
    -------
    None

    Notes
    -----
    - Does not modify the schema version.
    - Does not delete fields.
    - Does not emit warnings.
    - Operation is idempotent.
    """

    fonts = inventory.get("fonts", [])
    for font in fonts:
        identity = font.get("identity")

        if not isinstance(identity, dict):
            continue

        if "file" in identity:
            continue

        if "path" in font:
            identity["file"] = font["path"]


# -------------------------------------------------
# --- System Functions ---
# -------------------------------------------------


def clean_font_name(name: str) -> str:
    """
    Normalize a raw font name to a base family-like name.

    Parameters
    ----------
    name : str
        Raw font name as obtained from system sources.

    Returns
    -------
    str
        Normalized base name with parenthetical hints removed and
        common variant suffixes (e.g., Bold, Italic) stripped.
    """
    clean_name = re.sub(r"\s*\((TrueType|OpenType|True Type|Type 1)\)\s*$", "", name)

    variants = r"\s+(Bold|Italic|Light|Regular|Medium|Semibold|Black|Thin|Heavy|Narrow|Condensed|Extended|Grassetto|Corsivo|Chiaro|Normale|Medio|Nero|Sottile|Pesante|Condensato|Esteso).*$"
    return re.sub(variants, "", clean_name, flags=re.IGNORECASE).strip()


class _FontDetail(TypedDict):
    raw_line: str
    extracted_names: list[str]
    base_names: list[str]


def generate_test_output(
    inventory_fonts: list[dict],
    limit: int | None = None,
    filter_test: bool = False,
) -> None:
    """
    Produce a small text file with parsing diagnostics for manual inspection.

    Parameters
    ----------
    limit : int | None, optional
        If positive, keep the first N items; if negative, keep the last |N|
        items; if None, no limit is applied.
    filter_test : bool, optional
        If True, include only fonts whose names match substrings listed
        in `TEST_FONTS`.

    Returns
    -------
    None
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
#
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
# TEST FONT CONFIGURATION
# ------------------------------------------------------------------


def _configure_test_fonts(args) -> set[str]:
    """
    Build the effective TEST_FONTS set from CLI arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the `test_font` option.

    Returns
    -------
    set[str]
        Final set of font names to be used for test filtering.

    Notes
    -----
    Semantics:
    - "__DEFAULT__" enables DEFAULT_TEST_FONTS.
    - Explicit values extend the set.
    """
    cli_fonts: set[str] = set()

    if args.test_font:
        for value in args.test_font:
            cli_fonts.add(value)

        # Explicit CLI fonts extend defaults.
        return set(DEFAULT_TEST_FONTS) | cli_fonts

    # No --test-font provided → use DEFAULT_TEST_FONTS.
    return set(DEFAULT_TEST_FONTS)


def _handle_list_test_fonts(test_fonts: set[str], inventory_fonts: list[dict]) -> int:
    """
    Implement the --list-test-fonts CLI behavior.

    Parameters
    ----------
    test_fonts : set[str]
        Effective set of test font names used for filtering.

    Returns
    -------
    int
        Exit code (0 on success).

    Notes
    -----
    - Must ignore --quiet by contract.
    - Lists configured TEST_FONTS and matching inventory fonts (JSON is the single source of truth).
    """
    log_info("TEST_FONTS configuration:")

    if not test_fonts:
        log_info("  (empty)")
    else:
        for name in sorted(test_fonts):
            log_info(f"  - {name}")

    log_info("Inventory fonts matching TEST_FONTS (exact):")

    inv_families = {
        str(f.get("family", "")).strip() for f in inventory_fonts if isinstance(f, dict)
    }
    matched = [name for name in sorted(test_fonts) if name in inv_families]

    if not matched:
        log_info("  (none)")
    else:
        for name in matched:
            log_info(f"  - {name}")

    log_info("Missing TEST_FONTS (not present in inventory):")
    missing = [name for name in sorted(test_fonts) if name not in inv_families]

    if not missing:
        log_info("  (none)")
    else:
        for name in missing:
            log_info(f"  - {name}")

    return 0


# ------------------------------------------------------------------
# OUTPUT FILE PREPARATION
# ------------------------------------------------------------------


def _prepare_output_filename() -> tuple[int, str | None]:
    """
    Build a unique output filename based on platform and DATE_STR.

    Parameters
    ----------
    None

    Returns
    -------
    tuple[int, str | None]
        A pair (exit_code, filename):
        - exit_code == 0 → success, filename contains the generated name.
        - exit_code == 1 → error already logged, filename is None.
    """
    base_name = f"fontshow_{platform.system()}_{DATE_STR}"

    try:
        output_filename = get_unique_filename(base_name, "tex")
    except ValueError as e:
        log_err(f"Error: {e}")
        return 1, None
    else:
        return 0, output_filename


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
    """
    if args.inventory:
        return Path(args.inventory)

    default = Path(DEFAULT_INVENTORY)
    if default.exists():
        return default

    return None


def _inventory_platform_mismatch(inv_env: dict, runtime: dict) -> list[str]:
    """
    Compare inventory and runtime platform metadata and report mismatches.

    Parameters
    ----------
    inv_env : dict
        Inventory run-environment metadata.
    runtime : dict
        Runtime platform metadata collected from the current system.

    Returns
    -------
    list[str]
        List of metadata keys that differ between inventory and runtime.
        Empty if no mismatch is detected.
    """

    def _norm(v: object) -> str:
        """
        Normalize a value for platform metadata comparison.

        Parameters
        ----------
        v : object
            Value to normalize.

        Returns
        -------
        str
            Lowercased and stripped string representation of the value.
        """
        return str(v).strip().lower()

    mismatches: list[str] = []

    for key in ("os", "machine"):
        if _norm(inv_env.get(key)) != _norm(runtime.get(key)):
            mismatches.append(key)

    inv_ctx = inv_env.get("execution_context")
    run_ctx = runtime.get("execution_context")

    if _norm(inv_ctx) != _norm(run_ctx):
        mismatches.append("execution_context")

    return mismatches


def _enforce_platform(inv_env: dict) -> tuple[bool, list[str]]:
    """
    Enforce inventory/platform compatibility.

    Parameters
    ----------
    inv_env : dict
        Inventory run-environment metadata.

    Returns
    -------
    tuple[bool, list[str]]
        A pair (ok, mismatches):
        - ok is True if inventory matches runtime platform.
        - mismatches contains the differing metadata keys.
    """
    runtime = collect_platform_metadata()
    mismatches = _inventory_platform_mismatch(inv_env, runtime)
    return (not mismatches), mismatches


def _validate_fonts_structure(inventory: dict) -> tuple[bool, list]:
    """
    Validate the structure of the `fonts` section in an inventory.

    Parameters
    ----------
    inventory : dict
        Inventory dictionary expected to contain a `fonts` list.

    Returns
    -------
    tuple[bool, list]
        A pair (ok, fonts):
        - ok is True if the `fonts` section exists, is a non-empty list,
          and all elements are dictionaries.
        - fonts is the extracted list (or an empty list on failure).
    """
    if "fonts" not in inventory:
        return False, []

    fonts = inventory.get("fonts")
    if not isinstance(fonts, list):
        return False, []

    if not fonts:
        return False, []

    if any(not isinstance(f, dict) for f in fonts):
        return False, []

    return True, fonts


def _load_inventory(
    inv_path: Path, *, require_platform: bool = True
) -> tuple[int, list]:
    """
    Load and strictly validate an inventory file.

    Parameters
    ----------
    inv_path : pathlib.Path
        Path to the inventory JSON file.
    require_platform : bool, optional
        If True, enforce platform compatibility between inventory metadata
        and the current runtime environment.

    Returns
    -------
    tuple[int, list]
        A pair (exit_code, fonts):
        - exit_code == 0 → success, fonts contains validated descriptors.
        - exit_code == 1 → validation or load error (already logged), fonts empty.

    Notes
    -----
    Validation rejects:
    - Invalid schema version.
    - Missing required metadata.
    - Platform-incompatible inventories (when require_platform is True).
    - Malformed or empty `fonts` section.
    - Semantic validation failures.

    Validation is always strict; non-strict operation is not supported.
    """
    try:
        with inv_path.open(encoding="utf-8") as f:
            inventory = json.load(f)

        if not isinstance(inventory, dict):
            log_err("Invalid inventory JSON: expected top-level object.")
            return 1, []

        metadata = inventory.get("metadata", {}) or {}
        if not isinstance(metadata, dict):
            log_err("Invalid inventory JSON: expected 'metadata' to be an object.")
            return 1, []

        schema_version = metadata.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            log_err(
                f"Unsupported inventory schema_version: {schema_version!r} "
                f"(required {SCHEMA_VERSION})"
            )
            return 1, []

        inv_env = metadata.get("run_environment")
        if require_platform and not isinstance(inv_env, dict):
            log_err("Inventory missing required metadata.run_environment (schema v1.2)")
            return 1, []

        if require_platform and isinstance(inv_env, dict):
            ok, mismatches = _enforce_platform(inv_env)
            if not ok:
                log_err(f"Inventory platform mismatch: {', '.join(mismatches)}")
                return 1, []

        log_trace_cat(
            log,
            "flow",
            "inventory JSON loaded",
            extra={
                "fonts_count": len(inventory.get("fonts", [])),
                "path": str(inv_path),
            },
        )

        normalize_loaded_enums(inventory)

        ok_fonts, fonts = _validate_fonts_structure(inventory)
        if not ok_fonts:
            log_err("Invalid inventory JSON: malformed or empty 'fonts' section.")
            return 1, []

        _normalize_inventory_paths(inventory)

        ok, semantic_warnings = enforce_semantic_validation(
            inventory,
            strict=True,
        )
        log_trace_cat(
            log,
            "flow",
            "semantic validation completed",
            extra={
                "ok": ok,
                "warnings": len(semantic_warnings),
            },
        )

        if not ok:
            for w in semantic_warnings:
                sev = w.get("severity", Severity.INFO)
                if sev in (Severity.ERROR, Severity.WARN):
                    log_err(w.get("message", "semantic validation error"))
            return 1, []

        log_ok(f"Inventory loaded: {inv_path} ({len(fonts)} fonts)")

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        log_err(f"failed to load inventory: {e}")
        return 1, []
    else:
        return 0, fonts


# ------------------------------------------------------------------
# DIAGNOSTICS
# ------------------------------------------------------------------


def _run_inventory_diagnostics(fonts: list) -> None:
    """
    Run consistency diagnostics for inventory-based execution.

    Parameters
    ----------
    fonts : list
        List of validated font descriptor dictionaries.

    Returns
    -------
    None

    Notes
    -----
    Applies only when inventory mode is active and CLI is not in quiet mode.
    Emits informational or warning messages if language coverage is missing
    for a significant fraction of fonts.
    """
    missing_lang_count = 0
    total_fonts = 0

    for font in fonts:
        if not isinstance(font, dict):
            continue

        total_fonts += 1
        declared = set(font.get("coverage", {}).get("languages", []))

        if not declared:
            missing_lang_count += 1

    if not missing_lang_count:
        return

    ratio = missing_lang_count / total_fonts if total_fonts else 0.0

    if ratio < 0.10:
        log_info(
            f"{missing_lang_count} fonts have no declared language coverage "
            f"({ratio:.0%})"
        )
    elif ratio < 0.50:
        log_warn(
            f"{missing_lang_count} fonts have no declared language coverage "
            f"({ratio:.0%})"
        )
    else:
        log_warn(
            f"{missing_lang_count} fonts have no declared language coverage "
            f"({ratio:.0%}) — catalog usefulness may be severely degraded"
        )


# ------------------------------------------------------------------
# FONT FILTERING / OUTPUT GENERATION
# ------------------------------------------------------------------


def _filter_and_prepare_fonts(
    fonts: list[CatalogFontEntryV12], args, test_fonts: set[str]
) -> list[CatalogFontEntryV12]:
    """
    Filter and prepare fonts for catalog generation.

    Parameters
    ----------
    fonts : list
        List of font descriptor objects.
    args : argparse.Namespace
        Parsed CLI arguments controlling filtering and limiting.
    test_fonts : set[str]
        Set of font name substrings used for test filtering.

    Returns
    -------
    list
        List of filtered, sorted, and deduplicated font descriptor dictionaries.
    """
    log_trace_cat(
        log,
        "flow",
        "font filtering started",
        extra={
            "input_fonts": len(fonts),
        },
    )

    if test_fonts:
        fonts = [f for f in as_font_desc_list(fonts) if font_family(f) in test_fonts]

    if args.number:
        fonts = fonts[: args.number] if args.number > 0 else fonts[args.number :]

    fonts = sorted(
        as_font_desc_list(fonts),
        key=lambda f: font_family(f),
    )

    # Schema v1.2 forbids adding non-schema keys (e.g. 'name').
    # Rendering code must derive display name dynamically instead of mutating the descriptor.
    for f in fonts:
        _ = (
            f.get("full_name")
            or f.get("postscript_name")
            or f"{(f.get('family') or '')} {(f.get('subfamily') or '')}".strip()
        )
    result = group_fonts_by_family(fonts)
    log_trace_cat(
        log,
        "flow",
        "font filtering completed",
        extra={
            "output_fonts": len(result),
        },
    )

    return result


def _write_latex_output(output_filename: str, latex_content: str) -> None:
    """
    Write generated LaTeX catalog to disk and emit user messages.

    Parameters
    ----------
    output_filename : str
        Target filename for the LaTeX document.
    latex_content : str
        Full LaTeX document content to be written.

    Returns
    -------
    None
    """
    log_info(f"Writing file {output_filename}...")

    with Path(output_filename).open("w", encoding="utf-8") as f:
        f.write(latex_content)

    log_ok("Done! LaTeX file generated successfully.")
    log_ok("Ready for compilation.")
    log_ok(
        f"  Execute: lualatex -interaction=nonstopmode {output_filename} | texlogsieve (twice)"
    )


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
            "Font inventory not found. Catalog generation requires a valid v1.2 inventory."
        )
        return 1  # MUST fail deterministically even in --quiet mode

    rc, fonts = _load_inventory(inv_path)
    if rc != 0:
        return 1

    if args.test:
        generate_test_output(fonts, args.number, bool(TEST_FONTS))

    if args.list_test_fonts:
        return _handle_list_test_fonts(TEST_FONTS, fonts)

    # --------------------------------------------------------------
    # CONSISTENCY DIAGNOSTICS (inventory mode only)
    # --------------------------------------------------------------
    if inv_path and inv_path.exists():
        _run_inventory_diagnostics(fonts)

    # --------------------------------------------------------------
    # FONT FILTERING / OUTPUT PREPARATION
    # --------------------------------------------------------------
    fonts = _filter_and_prepare_fonts(fonts, args, TEST_FONTS)

    # Invariant guard: rendering requires normalized font descriptors.
    if not isinstance(fonts, list) or any(not isinstance(f, dict) for f in fonts):
        log_err("Internal error: invalid font descriptor list after filtering.")
        return 1

    latex_content = generate_latex(fonts)

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


def run(args):
    """
    Public CLI entrypoint for create-catalog.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Exit code returned by `main`.

    Notes
    -----
    Thin wrapper around `main` kept stable for compatibility with
    the top-level dispatcher and tests.
    """
    return main(args)


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
