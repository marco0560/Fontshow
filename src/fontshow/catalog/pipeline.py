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

import argparse
from collections.abc import Mapping, Sequence

from fontshow.catalog.labels import primary_script
from fontshow.constants.catalog import DEFAULT_TEST_FONTS
from fontshow.core.cli_utils import log_info, log_warn
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import CatalogFontEntryV12
from fontshow.inventory.io import as_font_desc_list
from fontshow.inventory.metadata_processing import font_family


def _configure_test_fonts(args: argparse.Namespace) -> set[str]:
    """
    Build the effective TEST_FONTS set from CLI arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the `test_font` option.

    Returns
    -------
    set[str]
        Final set of font family names used for test filtering.

    Notes
    -----
    Activation rules:
    - Plain `create-catalog` performs no test-font filtering.
    - `--test` and `--list-test-fonts` use `DEFAULT_TEST_FONTS`.
    - `--test-font` with no value (`__DEFAULT__`) enables
      `DEFAULT_TEST_FONTS`.
    - Explicit `--test-font NAME` values add named families to the
      effective test set.
    """
    cli_fonts: set[str] = set()
    use_defaults = bool(
        getattr(args, "test", False) or getattr(args, "list_test_fonts", False)
    )

    if args.test_font:
        for value in args.test_font:
            if value == "__DEFAULT__":
                use_defaults = True
            else:
                cli_fonts.add(value)

    effective: set[str] = set(cli_fonts)
    if use_defaults:
        effective |= set(DEFAULT_TEST_FONTS)

    return effective


def _handle_list_test_fonts(
    test_fonts: set[str], inventory_fonts: list[CatalogFontEntryV12]
) -> int:
    """
    Implement the --list-test-fonts CLI behavior.

    Parameters
    ----------
    test_fonts : set[str]
        Effective set of test font names used for filtering.
    inventory_fonts : list[CatalogFontEntryV12]
        Inventory font descriptors used as the authoritative source for
        exact family-name matching.

    Returns
    -------
    int
        Exit code (0 on success).

    Notes
    -----
    - Must ignore --quiet by contract.
    - Lists configured TEST_FONTS and matching inventory fonts (JSON is the single source of truth).
    - Matching is performed against exact family names after trimming the
      inventory-side `family` field to avoid false negatives caused by
      surrounding whitespace.
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


def _run_inventory_diagnostics(fonts: Sequence[Mapping[str, object] | object]) -> None:
    """
    Run consistency diagnostics for inventory-based execution.

    Parameters
    ----------
    fonts : Sequence[Mapping[str, object] | object]
        Sequence of validated font descriptor dictionaries.

    Returns
    -------
    None

    Notes
    -----
    Applies only when inventory mode is active and CLI is not in quiet mode.
    Emits informational or warning messages if language coverage is missing
    for a significant fraction of fonts.
    Thresholds are severity-based: below 10 percent logs as info, from
    10 to below 50 percent logs as warning, and 50 percent or above
    emits the strongest warning message.
    """
    missing_lang_count = 0
    total_fonts = 0

    for font in fonts:
        if not isinstance(font, Mapping):
            continue
        total_fonts += 1
        coverage = font.get("coverage", {})
        if not isinstance(coverage, Mapping):
            continue

        languages = coverage.get("languages", [])
        if not isinstance(languages, list):
            missing_lang_count += 1
            continue

        declared = {
            lang for lang in languages if isinstance(lang, str) and lang.strip()
        }

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


def _normalized_language_filters(args: argparse.Namespace) -> tuple[str, ...]:
    """
    Normalize language selector arguments for deterministic filtering.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments that may contain repeated ``--language``
        values.

    Returns
    -------
    tuple[str, ...]
        Distinct normalized language tags sorted lexicographically.
    """
    raw_values = getattr(args, "language", None) or []
    normalized = {
        str(value).strip().lower()
        for value in raw_values
        if isinstance(value, str) and str(value).strip()
    }
    return tuple(sorted(normalized))


def _normalized_script_filters(args: argparse.Namespace) -> tuple[str, ...]:
    """
    Normalize script selector arguments for deterministic filtering.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments that may contain repeated ``--script``
        values.

    Returns
    -------
    tuple[str, ...]
        Distinct normalized script tags sorted lexicographically.
    """
    raw_values = getattr(args, "script", None) or []
    normalized = {
        str(value).strip().upper()
        for value in raw_values
        if isinstance(value, str) and str(value).strip()
    }
    return tuple(sorted(normalized))


def _normalized_sort_keys(args: argparse.Namespace) -> tuple[str, ...]:
    """
    Normalize sort-mode arguments for deterministic catalog ordering.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments that may contain repeated ``--sort-by``
        values.

    Returns
    -------
    tuple[str, ...]
        Sort keys in CLI order with duplicates removed.
    """
    raw_values = getattr(args, "sort_by", None) or []
    ordered: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        if not isinstance(value, str):
            continue
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _font_language_tags(font: Mapping[str, object]) -> tuple[str, ...]:
    """
    Return the normalized language tags associated with a font.

    Parameters
    ----------
    font : Mapping[str, object]
        Catalog font descriptor whose coverage and inference metadata
        are inspected.

    Returns
    -------
    tuple[str, ...]
        Distinct normalized language tags sorted lexicographically.
    """
    tags: set[str] = set()
    for section_name in ("coverage", "inference"):
        section_raw = font.get(section_name)
        section = section_raw if isinstance(section_raw, Mapping) else {}
        values = section.get("languages")
        if isinstance(values, Sequence) and not isinstance(values, str):
            for value in values:
                if isinstance(value, str) and value.strip():
                    tags.add(value.strip().lower())
    return tuple(sorted(tags))


def _font_script_tags(font: Mapping[str, object]) -> tuple[str, ...]:
    """
    Return the normalized script tags associated with a font.

    Parameters
    ----------
    font : Mapping[str, object]
        Catalog font descriptor whose script metadata is inspected.

    Returns
    -------
    tuple[str, ...]
        Distinct normalized script tags sorted lexicographically.
    """
    tags: set[str] = set()
    primary = primary_script(font)
    if isinstance(primary, str) and primary.strip():
        tags.add(primary.strip().upper())

    for section_name in ("coverage", "inference"):
        section_raw = font.get(section_name)
        section = section_raw if isinstance(section_raw, Mapping) else {}
        values = section.get("scripts")
        if isinstance(values, Sequence) and not isinstance(values, str):
            for value in values:
                if isinstance(value, str) and value.strip():
                    tags.add(value.strip().upper())
    return tuple(sorted(tags))


def _font_primary_language(font: Mapping[str, object]) -> str:
    """
    Return the primary language tag used for sorting a catalog font.

    Parameters
    ----------
    font : Mapping[str, object]
        Catalog font descriptor whose language metadata is inspected.

    Returns
    -------
    str
        The first declared coverage language when present, otherwise the
        first inferred language, otherwise the empty string.
    """
    for section_name in ("coverage", "inference"):
        section_raw = font.get(section_name)
        section = section_raw if isinstance(section_raw, Mapping) else {}
        values = section.get("languages")
        if isinstance(values, Sequence) and not isinstance(values, str):
            for value in values:
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()
    return ""


def _font_primary_script(font: Mapping[str, object]) -> str:
    """
    Return the primary script tag used for sorting a catalog font.

    Parameters
    ----------
    font : Mapping[str, object]
        Catalog font descriptor whose script metadata is inspected.

    Returns
    -------
    str
        Deterministic primary script tag, or the empty string when no
        script metadata is available.
    """
    primary = primary_script(font)
    if isinstance(primary, str) and primary.strip():
        return primary.strip().upper()
    return ""


def _catalog_sort_key(
    font: CatalogFontEntryV12, sort_keys: tuple[str, ...]
) -> tuple[str, ...]:
    """
    Build the deterministic catalog sort key for a font descriptor.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font descriptor being ordered.
    sort_keys : tuple[str, ...]
        Normalized sort modes requested by the CLI.

    Returns
    -------
    tuple[str, ...]
        Composite sort key ending with the canonical family name.
    """
    parts: list[str] = []
    for sort_key in sort_keys:
        if sort_key == "language":
            parts.append(_font_primary_language(font))
        elif sort_key == "script":
            parts.append(_font_primary_script(font))
    parts.append(font_family(font))
    return tuple(parts)


def _filter_and_prepare_fonts(
    fonts: list[CatalogFontEntryV12], args: argparse.Namespace, test_fonts: set[str]
) -> list[CatalogFontEntryV12]:
    """
    Filter and prepare fonts for catalog generation.

    Parameters
    ----------
    fonts : list[CatalogFontEntryV12]
        Input font descriptor objects.
    args : argparse.Namespace
        Parsed CLI arguments controlling filtering and limiting.
    test_fonts : set[str]
        Set of exact family names used for test filtering.

    Returns
    -------
    list[CatalogFontEntryV12]
        Filtered font descriptors normalized with `as_font_desc_list`,
        optionally limited by `args.number`, and sorted by family name.

    Raises
    ------
    TypeError
        May propagate from downstream normalization helpers if the input
        collection contains values that cannot be treated as catalog
        font descriptors.

    Notes
    -----
    The helper does not mutate descriptors by adding non-schema keys.
    Display-name fallbacks are derived transiently to remain compliant
    with the archived schema v1.2 layout.
    Processing order is deterministic: optional test-font filtering,
    optional selector filtering, optional count limiting, normalization,
    and deterministic sorting.
    """
    log_trace_cat(
        log,
        "flow",
        "font filtering started",
        extra={
            "input_fonts": len(fonts),
        },
    )

    language_filters = _normalized_language_filters(args)
    script_filters = _normalized_script_filters(args)
    sort_keys = _normalized_sort_keys(args)

    if test_fonts:
        fonts = [f for f in as_font_desc_list(fonts) if font_family(f) in test_fonts]

    if language_filters:
        fonts = [
            f
            for f in as_font_desc_list(fonts)
            if set(_font_language_tags(f)) & set(language_filters)
        ]

    if script_filters:
        fonts = [
            f
            for f in as_font_desc_list(fonts)
            if set(_font_script_tags(f)) & set(script_filters)
        ]

    if args.number:
        fonts = fonts[: args.number] if args.number > 0 else fonts[args.number :]

    fonts = sorted(
        as_font_desc_list(fonts),
        key=lambda f: _catalog_sort_key(f, sort_keys),
    )

    # Inventory descriptors remain schema-shaped; rendering code must not mutate them.
    # Rendering code must derive display name dynamically instead of mutating the descriptor.
    for f in fonts:
        _ = (
            f.get("full_name")
            or f.get("postscript_name")
            or f"{(f.get('family') or '')} {(f.get('subfamily') or '')}".strip()
        )
    log_trace_cat(
        log,
        "flow",
        "font filtering completed",
        extra={
            "output_fonts": len(fonts),
        },
    )

    return fonts
