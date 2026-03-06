"""
Catalog pipeline helpers.

This module contains internal helper functions used by the catalog
generation pipeline implemented in create_catalog.py.

Responsibilities
----------------
- Configure and manage test-font filtering.
- Run diagnostics on inventory data before rendering.
- Filter and prepare fonts for catalog generation.

Design principles
-----------------
These helpers implement steps in the catalog generation workflow but
do not perform CLI handling or document rendering. They are separated
from the main pipeline module to keep create_catalog.py focused on
high-level orchestration.

Architectural role
------------------
This module belongs to the catalog domain layer and provides internal
pipeline utilities used during catalog generation.
"""

import logging

from fontshow.catalog.metadata import font_family
from fontshow.cli_utils import log_info, log_warn
from fontshow.constants.catalog import DEFAULT_TEST_FONTS
from fontshow.inventory.io import as_font_desc_list, group_fonts_by_family
from fontshow.logging_utils import log_trace_cat
from fontshow.types import CatalogFontEntryV12

log = logging.getLogger("fontshow")

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
