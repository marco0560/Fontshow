#!/usr/bin/env python3
"""
Fontshow – parse_font_inventory.py
=================================

Parse and enrich a ``font_inventory.json`` produced by ``dump_fonts.py`` by
applying deterministic inference of writing scripts and language candidates.

Design principles
-----------------
- **Cross-platform**: works only on JSON data, never touches font files.
- **Deterministic**: same input → same output.
- **Non-destructive**: declared metadata is never overwritten.
- **Configurable**: inference aggressiveness selectable from CLI.

Default inference level: ``medium``.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from fontshow import __version__
from fontshow.cli_utils import add_common_arguments
from fontshow.dump_fonts import UNICODE_BLOCKS
from fontshow.infer_languages import infer_languages
from fontshow.json_format import dumps_pretty
from fontshow.schema_validation import validate_inventory_schema

# ============================================================
# Set up logger
# ============================================================
logger = logging.getLogger("fontshow")

# ============================================================
# Inference thresholds
# ============================================================

#: Mapping of inference level → numeric thresholds.
#:
#: Structure::
#:
#:     {
#:         "<level>": {
#:             "script_min_cp": int,  # minimum code points to consider a script
#:         }
#:     }
#:
INFERENCE_THRESHOLDS: dict[str, dict[str, int]] = {
    "conservative": {
        "script_min_cp": 10,
    },
    "medium": {
        "script_min_cp": 5,
    },
    "aggressive": {
        "script_min_cp": 1,
    },
}

# ============================================================
# Unicode → script ranges
# ============================================================

#: Mapping of ISO 15924 script codes to Unicode code point ranges.
#:
#: Each value is a list of ``(start, end)`` integer tuples, inclusive.
# NOTE:
# All script identifiers MUST be uppercase ISO-15924-like codes
# (e.g. LATN, HANI, JPAN).
#:
#: Example::
#:
#:     "LATN": [(0x0041, 0x007A), (0x00C0, 0x024F)]
#:
UNICODE_SCRIPT_RANGES: dict[str, list[tuple[int, int]]] = {
    "LATN": [(0x0041, 0x007A), (0x00C0, 0x024F)],
    "GREK": [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    "CYRL": [(0x0400, 0x04FF), (0x0500, 0x052F)],
    "ARAB": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)],
    "HEBR": [(0x0590, 0x05FF)],  # Hebrew
    "DEVA": [(0x0900, 0x097F)],  # Devanagari
    "HANI": [(0x4E00, 0x9FFF)],  # CJK Unified Ideographs
    "HANG": [(0xAC00, 0xD7AF)],  # Hangul Syllables
    "THAI": [(0x0E00, 0x0E7F)],  # Thai
    "ARMN": [(0x0530, 0x058F)],  # Armenian
    "JPAN": [(0x3040, 0x30FF)],  # Japanese (Hiragana + Katakana)
    "VIET": [(0x1EA0, 0x1EFF)],  # Vietnamese extensions
    "COPT": [(0x2C80, 0x2CFF)],  # Coptic
    "ETHI": [(0x1200, 0x137F)],  # Ethiopic (incl. Tigrinya)
}

# ============================================================
# Script → language candidates
# ============================================================

#: Mapping of inferred script identifiers to plausible language codes.
#:
#: Values are **examples**, not a guarantee of full language support.
#:
SCRIPT_TO_LANGUAGES: dict[str, list[str]] = {
    "LATN": ["en", "fr", "de", "it", "es", "pt", "nl", "sv", "no", "da", "fi", "vi"],
    "GREK": ["el"],
    "CYRL": ["ru", "uk", "bg", "sr", "mk"],
    "ARAB": ["ar"],
    "HEBR": ["he"],
    "DEVA": ["hi", "ne"],
    "HANI": ["zh"],
    "HANG": ["ko"],
    "JPAN": ["ja"],
    "THAI": ["th"],
    "ARMN": ["hy"],
    "COPT": ["cop"],
    "ETHI": ["ti"],
}

#: Mapping of primary language codes to their primary script.
LANGUAGE_PRIMARY_SCRIPT: dict[str, str] = {
    "en": "LATN",
    "fr": "LATN",
    "de": "LATN",
    "it": "LATN",
    "es": "LATN",
    "pt": "LATN",
    "nl": "LATN",
    "sv": "LATN",
    "no": "LATN",
    "da": "LATN",
    "fi": "LATN",
    "vi": "LATN",
    "el": "GREK",
    "ru": "CYRL",
    "uk": "CYRL",
    "bg": "CYRL",
    "sr": "CYRL",
    "mk": "CYRL",
    "ar": "ARAB",
    "he": "HEBR",
    "hi": "DEVA",
    "ne": "DEVA",
    "zh": "HANI",
    "ja": "JPAN",
    "ko": "HANG",
    "th": "THAI",
    "hy": "ARMN",
    "cop": "COPT",
    "ti": "ETHI",
}


# ============================================================
# Helper functions
# ============================================================


def decode_fc_charset_bitmap(raw: str) -> list[list[int]]:
    """
    Decode a FontConfig charset bitmap into Unicode codepoint ranges.

    The input is the raw multiline bitmap produced by fc-query, e.g.:

        0000: 00000000 ffffffff ffffffff 7fffffff ...
        0001: ffffffff ...

    Each line encodes 256 codepoints:
    - block index * 256
    - 8 words of 32 bits
    - bits are interpreted MSB → LSB

    Returns
    -------
    list[list[int]]
        Sorted, merged [start, end] Unicode ranges (inclusive).
    """
    codepoints: list[int] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue

        block_hex, rest = line.split(":", 1)
        try:
            block_index = int(block_hex.strip(), 16)
        except ValueError:
            continue

        words = rest.strip().split()
        if len(words) != 8:
            continue

        base = block_index * 256

        for word_index, word_hex in enumerate(words):
            try:
                word = int(word_hex, 16)
            except ValueError:
                continue

            for bit in range(32):
                if word & (1 << (31 - bit)):
                    codepoints.append(base + word_index * 32 + bit)

    if not codepoints:
        return []

    codepoints = sorted(set(codepoints))

    ranges: list[list[int]] = []
    start = prev = codepoints[0]

    for cp in codepoints[1:]:
        if cp == prev + 1:
            prev = cp
        else:
            ranges.append([start, prev])
            start = prev = cp

    ranges.append([start, prev])
    return ranges


def unicode_blocks_from_charset_ranges(
    ranges: list[list[int]],
) -> dict[str, int]:
    """
    Derive Unicode block coverage counts from normalized charset ranges.

    Parameters
    ----------
    ranges : list[list[int]]
        Normalized [start, end] codepoint ranges (inclusive).

    Returns
    -------
    dict[str, int]
        Mapping of Unicode block name to covered codepoint count.
    """
    blocks: dict[str, int] = {}

    for r_start, r_end in ranges:
        for block_name, b_start, b_end in UNICODE_BLOCKS:
            start = max(r_start, b_start)
            end = min(r_end, b_end)
            if start <= end:
                blocks[block_name] = blocks.get(block_name, 0) + (end - start + 1)

    return blocks


def script_coverage_from_unicode_blocks(
    unicode_blocks: dict[str, int],
    script_ranges: dict[str, list[tuple[int, int]]],
    total_codepoints: int,
) -> dict[str, float]:
    """
    Derive script coverage ratios from Unicode block coverage.

    Parameters
    ----------
    unicode_blocks : dict[str, int]
        Mapping of Unicode block name to covered codepoint count.
    script_ranges : dict[str, list[tuple[int, int]]]
        Mapping of script tag to list of Unicode codepoint ranges.
    total_codepoints : int
        Total number of codepoints covered by the charset.

    Returns
    -------
    dict[str, float]
        Mapping of script tag to coverage ratio (0.0–1.0).
    """
    if not unicode_blocks or total_codepoints <= 0:
        return {}

    # Map block name -> (start, end)
    block_ranges = {name: (start, end) for name, start, end in UNICODE_BLOCKS}

    script_counts: dict[str, int] = {}

    for block_name, count in unicode_blocks.items():
        block_range = block_ranges.get(block_name)
        if not block_range:
            continue

        b_start, b_end = block_range

        for script, ranges in script_ranges.items():
            for r_start, r_end in ranges:
                # Check intersection between block and script range
                if b_start <= r_end and b_end >= r_start:
                    script_counts[script] = script_counts.get(script, 0) + count
                    break
            else:
                continue
            break

    return {
        script: cnt / total_codepoints
        for script, cnt in script_counts.items()
        if cnt > 0
    }


def normalize_charset_ranges(ranges: list[list[int]]) -> dict[str, Any]:
    """
    Normalize a list of Unicode codepoint ranges.

    The normalization:
    - sorts ranges by start codepoint,
    - merges overlapping or adjacent ranges,
    - computes the total number of covered codepoints (inclusive).

    The function is pure and idempotent.

    Parameters
    ----------
    ranges : list[list[int]]
        A list of [start, end] codepoint ranges (inclusive).

    Returns
    -------
    dict[str, Any]
        {
            "ranges": list[list[int]],
            "codepoints_count": int,
        }
    """
    if not ranges:
        return {"ranges": [], "codepoints_count": 0}

    # Defensive copy + sort
    ordered = sorted((int(a), int(b)) for a, b in ranges)

    merged: list[list[int]] = []
    cur_start, cur_end = ordered[0]

    for start, end in ordered[1:]:
        if start <= cur_end + 1:
            cur_end = max(cur_end, end)
        else:
            merged.append([cur_start, cur_end])
            cur_start, cur_end = start, end

    merged.append([cur_start, cur_end])

    codepoints_count = sum(end - start + 1 for start, end in merged)

    return {
        "ranges": merged,
        "codepoints_count": codepoints_count,
    }


def add_structured_warning(
    target: dict,
    *,
    code: str,
    message: str,
    severity: str = "warning",
) -> None:
    """
    Attach a structured warning to an inventory node.

    Parameters
    ----------
    target : dict
        Inventory root or font entry.
    code : str
        Machine-readable warning code.
    message : str
        Human-readable warning message.
    severity : str, optional
        Severity level (default: ``"warning"``).

    Notes
    -----
    - Warnings are appended to the ``warnings`` list of the target.
    - The target dictionary is modified in place.
    """
    warnings = target.setdefault("warnings", [])
    warnings.append(
        {
            "code": code,
            "message": message,
            "severity": severity,
        }
    )


def validate_font_entry(entry: dict, *, index: int) -> list[str]:
    """
    Validate the structural integrity of a single font entry.

    This function performs schema-level validation of a font entry
    independently of any inference logic.

    Parameters
    ----------
    entry : dict
        Font entry object to validate.
    index : int
        Index of the font entry in the inventory (for diagnostics only).

    Returns
    -------
    list[str]
        A list of human-readable error messages.
        An empty list indicates a valid entry.

    Notes
    -----
    - This function does not modify the entry.
    - Inference results are not required to be present.
    """
    errors: list[str] = []

    # --- Required structural fields ---
    if not isinstance(entry, dict):
        return ["entry is not an object"]

    path = entry.get("path")
    if not isinstance(path, str) or not path:
        errors.append("missing or invalid 'path'")

    family = entry.get("family")
    if not isinstance(family, str) or not family:
        errors.append("missing or invalid 'family'")

    style = entry.get("style")
    if not isinstance(style, str) or not style:
        errors.append("missing or invalid 'style'")

    # --- sample_text validation (optional) ---
    if "sample_text" in entry:
        st = entry["sample_text"]

        if st is not None:
            if not isinstance(st, dict):
                errors.append("sample_text must be an object or null")
            else:
                source = st.get("source")
                text = st.get("text")

                if source != "font":
                    errors.append("sample_text.source must be 'font'")

                if not isinstance(text, str) or not text.strip():
                    errors.append("sample_text.text must be a non-empty string")

    return errors


def validate_inventory(
    data: dict,
    *,
    verbose: bool = False,
    quiet: bool = False,
) -> int:
    """
    Validate a Fontshow font inventory.

    This function performs two distinct classes of checks:

    1. Fatal validation errors:
       These indicate that one or more font entries are structurally or
       semantically invalid according to the current data model.
       Fatal errors are reported as ERROR and cause the validation to fail
       (non-zero return value).

    2. Non-fatal consistency warnings:
       These highlight incomplete or suspicious entries that may still be
       usable, but are worth reporting to the user.
       Warnings do not cause validation failure.

    Validation is best-effort and exhaustive:
    all font entries are inspected and all issues are reported in a single run.

    This function does not raise exceptions and does not modify the inventory.
    It is intended to be used by the '--validate-inventory' CLI option, where
    the caller decides how to handle the returned error count and exit status.

    Args:
        data: Parsed inventory JSON object.

    Returns:
        The number of font entries with fatal validation errors.

    Notes:
    - This function is validation-only and never mutates inference results.
    """

    fatal_errors = 0
    warnings = 0

    if not isinstance(data, dict):
        if not quiet:
            print("❌ Inventory root is not a JSON object")
        return 1

    # Ensure inventory-level warnings container exists
    data.setdefault("warnings", [])

    metadata = data.get("metadata", {})
    schema_version = metadata.get("schema_version")

    if schema_version is None:
        add_structured_warning(
            data,
            code="missing_schema_version",
            message="Inventory has no schema_version",
            severity="warning",
        )
    elif schema_version != "1.0":
        add_structured_warning(
            data,
            code="unknown_schema_version",
            message=f"Unknown schema_version '{schema_version}'",
            severity="warning",
        )

    fonts = data.get("fonts")
    if not isinstance(fonts, list):
        if not quiet:
            print("❌ 'fonts' field missing or not a list")
        return 1

    for idx, font in enumerate(fonts):
        # ---------- Fatal entry validation ----------
        entry_errors = validate_font_entry(font, index=idx)
        if entry_errors:
            fatal_errors += 1
            path = font.get("path") if isinstance(font, dict) else None

            print(f"ERROR font[{idx}]")
            print(f"  path: {path}")
            for err in entry_errors:
                print(f"  - {err}")
            print()

        # ---------- Non-fatal consistency warnings ----------
        if not isinstance(font, dict):
            warnings += 1
            add_structured_warning(
                font,
                code="missing_family",
                message="Font entry has no family or base_names",
                severity="warning",
            )
            continue

        identity = font.get("identity", {})
        family = identity.get("family")
        base_names = font.get("base_names")

        if not family and not base_names:
            warnings += 1
            add_structured_warning(
                font,
                code="missing_family",
                message="Font entry has no family or base_names",
                severity="warning",
            )

    if verbose:
        for idx, font in enumerate(fonts):
            for warning in font.get("warnings", []):
                print(
                    f"⚠️  Warning font[{idx}]: "
                    f"{warning['code']} - {warning['message']}"
                )

    if not quiet:
        if fatal_errors == 0:
            print("✅ Inventory validation completed (no fatal errors)")
        else:
            print(f"❌ Inventory validation failed with {fatal_errors} invalid entries")

    return fatal_errors


# ============================================================
# Inference helpers
# ============================================================

# Script normalization

#: Normalize human-readable script names to ISO 15924 codes.
#: This mapping enforces a single canonical representation
#: across the entire pipeline.
SCRIPT_NAME_TO_ISO: dict[str, str] = {
    "latin": "latn",
    "greek": "grek",
    "cyrillic": "cyrl",
    "arabic": "arab",
    "hebrew": "hebr",
    "devanagari": "deva",
    "japanese": "jpan",
    "korean": "hang",
    "han": "hani",
}

# NOTE:
# Script identifiers emitted by infer_scripts() MUST be ISO 15924 codes.
# Human-readable names (e.g. "latin", "greek") are considered internal-only
# and must never appear in the enriched inventory.


def infer_scripts(coverage: dict[str, Any], level: str = "medium") -> list[str]:
    """
    Infer writing scripts from Unicode coverage metadata.

    The function follows a two-step strategy:

    1. **Primary path**: analyze ``coverage["unicode_blocks"]`` if present.
    2. **Fallback path**: infer from ``coverage["unicode"]["max"]``.

    Args:
        coverage: Coverage block extracted from a font entry. Expected keys are
            ``unicode_blocks`` (mapping block name → count) and/or
            ``unicode.max`` (maximum code point).
        level: Inference aggressiveness level. One of
            ``"conservative"``, ``"medium"`` (default), or ``"aggressive"``.

    Returns:
        A list of inferred script identifiers (lowercase strings).
        Returns ``["unknown"]`` if no reliable inference is possible.
        The value ``"unknown"`` is a sentinel and must not be used
        for downstream language inference.
    """
    blocks: dict[str, int] = coverage.get("unicode_blocks", {}) or {}

    # -------------------------------
    # 1. Primary path: unicode_blocks
    # -------------------------------
    if blocks:
        total = sum(blocks.values()) or 1

        def significant(count: int) -> bool:
            """Check whether a block count is significant for the given level."""
            if level == "conservative":
                return count >= 50 or (count / total) >= 0.10
            if level == "aggressive":
                return count >= 5
            # medium (default)
            return count >= 20 or (count / total) >= 0.05

        scripts_found: set[str] = set()

        # --- block → script mapping
        for block, count in blocks.items():
            if not significant(count):
                continue

            if block.startswith("Latin"):
                scripts_found.add("latin")
            elif block == "Greek and Coptic":
                scripts_found.add("greek")
            elif block == "Cyrillic":
                scripts_found.add("cyrillic")
            elif block == "Arabic":
                scripts_found.add("arabic")
            elif block == "Hebrew":
                scripts_found.add("hebrew")
            elif block == "Devanagari":
                scripts_found.add("devanagari")
            elif block in ("Hiragana", "Katakana"):
                scripts_found.add("japanese")
            elif block == "Hangul Syllables":
                scripts_found.add("korean")
            elif block.startswith("CJK Unified Ideographs"):
                scripts_found.add("han")

        # --- CJK disambiguation
        if "han" in scripts_found:
            if "japanese" in scripts_found:
                return ["jpan"]
            if "korean" in scripts_found:
                return ["hang"]
            return ["hani"]

        # Normalize to ISO 15924 codes
        normalized = [SCRIPT_NAME_TO_ISO.get(s, s) for s in scripts_found]

        return sorted(set(normalized)) or ["unknown"]

    # -------------------------------
    # 2. Fallback: unicode.max
    # -------------------------------
    unicode_max = coverage.get("unicode", {}).get("max")
    if isinstance(unicode_max, int):
        if unicode_max <= 0x024F:
            return ["latn"]
        if 0x0370 <= unicode_max <= 0x03FF:
            return ["grek"]
        if 0x0400 <= unicode_max <= 0x04FF:
            return ["cyrl"]
        if 0x0590 <= unicode_max <= 0x05FF:
            return ["hebr"]
        if 0x0600 <= unicode_max <= 0x06FF:
            return ["arab"]
        if 0x0900 <= unicode_max <= 0x097F:
            return ["deva"]
        if unicode_max >= 0x4E00:
            return ["hani"]

    return ["unknown"]


# ============================================================
# Core processing
# ============================================================


def parse_inventory(data: dict[str, Any], level: str) -> dict[str, Any]:
    """
    Parse and enrich a font inventory structure.

    This function:
    - validates the inventory schema
    - performs script and language inference
    - enriches font entries with derived metadata
    - emits structured log events during processing

    Parameters
    ----------
    inventory : dict
        Parsed JSON inventory as produced by `dump_fonts`.
    level : str
        Inference aggressiveness level ("low", "medium", "high").

    Returns
    -------
    dict
        Enriched inventory with inferred metadata.

    Notes
    -----
    - This function does NOT perform any I/O.
    - Logging is emitted through the global `fontshow` logger.
    """
    # Standard library imports for debug purposes
    import os
    import pprint

    logger.info(
        "inventory schema validation requested",
        extra={
            "schema_version": data.get("schema_version"),
        },
    )
    logger.debug("inventory schema validation started")
    # --- Schema validation (C4.4) -----------------------------------------
    schema_warnings = validate_inventory_schema(data)
    logger.info(
        "inventory schema validation completed",
        extra={
            "schema_version": data.get("schema_version"),
            "warnings_count": len(schema_warnings),
        },
    )
    if schema_warnings:
        severity_counts: dict[str, int] = {}
        for w in schema_warnings:
            sev = w.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        logger.debug(
            "inventory schema validation produced warnings",
            extra={
                "schema_version": data.get("schema_version"),
                "severity_counts": severity_counts,
            },
        )

    for warning in schema_warnings:
        add_structured_warning(
            data,
            code=warning["code"],
            message=warning["message"],
            severity=warning["severity"],
        )
    # ----------------------------------------------------------------------

    logger.info(
        "font inventory parsing started",
        extra={
            "schema_version": data.get("schema_version"),
            "fonts_count": len(data.get("fonts", [])),
        },
    )

    for font in data.get("fonts", []):
        identity = font.get("identity", {})
        font_path = font.get("path")
        family = identity.get("family")
        style = identity.get("style")

        logger.debug(
            "font entry parsing started",
            extra={
                "font_path": font_path,
                "family": family,
                "style": style,
            },
        )

        # Unicode coverage metadata extracted upstream
        coverage: dict[str, Any] = font.get("coverage", {}) or {}

        # ------------------------------------------------------------
        # FontConfig charset decoding (C5.1)
        # ------------------------------------------------------------
        charset = coverage.get("charset")
        if isinstance(charset, dict):
            raw = charset.get("raw")
            if isinstance(raw, str) and raw.strip():
                try:
                    ranges = decode_fc_charset_bitmap(raw)
                    charset["ranges"] = ranges

                    logger.debug(
                        "fontconfig charset bitmap decoded",
                        extra={
                            "font_path": font_path,
                            "ranges_count": len(ranges),
                        },
                    )
                except Exception as exc:
                    charset["ranges"] = []
                    logger.warning(
                        "fontconfig charset bitmap decoding failed",
                        extra={
                            "font_path": font_path,
                            "error_type": type(exc).__name__,
                            "error_reason": str(exc),
                        },
                    )
        # ------------------------------------------------------------

        charset = coverage.get("charset")
        if isinstance(charset, dict) and charset.get("ranges"):
            normalized = normalize_charset_ranges(charset["ranges"])
            coverage["normalized_charset"] = normalized

            logger.debug(
                "charset normalized",
                extra={
                    "font_path": font_path,
                    "ranges_count": len(normalized["ranges"]),
                    "codepoints_count": normalized["codepoints_count"],
                },
            )

            normalized = coverage.get("normalized_charset")
            if normalized:
                blocks = unicode_blocks_from_charset_ranges(normalized["ranges"])
                if blocks:
                    coverage["unicode_blocks_from_charset"] = blocks

                    logger.debug(
                        "unicode blocks derived from charset",
                        extra={
                            "font_path": font_path,
                            "blocks_count": len(blocks),
                        },
                    )

        blocks = coverage.get("unicode_blocks_from_charset")
        normalized = coverage.get("normalized_charset")

        if blocks and normalized:
            script_cov = script_coverage_from_unicode_blocks(
                blocks,
                UNICODE_SCRIPT_RANGES,
                normalized["codepoints_count"],
            )

            if script_cov:
                coverage["script_coverage_from_charset"] = script_cov

                logger.debug(
                    "script coverage derived from charset",
                    extra={
                        "font_path": font_path,
                        "scripts_count": len(script_cov),
                    },
                )

        # Declared metadata provided by FontConfig or inventory tools
        # These values are informational and never overwritten
        declared_scripts: list[str] = list(coverage.get("scripts", []) or [])
        declared_languages: list[str] = list(coverage.get("languages", []) or [])
        if not declared_languages:
            add_structured_warning(
                font,
                code="missing_declared_languages",
                message=(
                    "No declared languages available from FontConfig; "
                    "inference.languages will be derived solely from Unicode data"
                ),
                severity="info",
            )
        if not declared_languages:
            logger.debug(
                "declared languages missing",
                extra={
                    "font_path": font_path,
                    "family": family,
                    "style": style,
                },
            )

        # C4.2 – Infer Unicode scripts from coverage metadata
        inferred_scripts: list[str] = list(infer_scripts(coverage, level) or [])
        logger.debug(
            "scripts inferred",
            extra={
                "font_path": font_path,
                "family": family,
                "style": style,
                "inferred_scripts": inferred_scripts,
                "infer_level": level,
            },
        )

        # Infer candidate languages from Unicode coverage
        inferred_languages_map: dict[str, dict[str, Any]] = infer_languages(
            coverage,
            policy="permissive",
        )
        logger.debug(
            "languages inferred",
            extra={
                "font_path": font_path,
                "family": family,
                "style": style,
                "language_candidates": list(inferred_languages_map.keys()),
            },
        )

        # Normalize inferred scripts to canonical uppercase form (ISO-15924-like)
        # inferred_scripts may come from different sources and must not be trusted
        # to already be normalized.
        normalized_scripts: list[str] = [str(s).upper() for s in inferred_scripts]
        font_scripts = set(normalized_scripts)

        def _language_sort_key(lang: str) -> tuple[int, str]:
            """
            Sort languages by compatibility with the font primary scripts.

            Priority rules:
            1. Languages whose PRIMARY script matches one of the inferred font scripts
            2. Fallback to alphabetical order for deterministic behavior
            """
            primary_script = LANGUAGE_PRIMARY_SCRIPT.get(lang)
            return (
                0 if primary_script and primary_script in font_scripts else 1,
                lang,
            )

        # Order languages deterministically, preferring script-compatible ones
        inferred_languages: list[str] = sorted(
            inferred_languages_map.keys(),
            key=_language_sort_key,
        )

        # ------------------------------------------------------------
        # DEBUG: inference inspection (opt-in via env var)
        # ------------------------------------------------------------
        if os.environ.get("FONTSHOW_DEBUG_INFERENCE") == "1":
            print("\n[DEBUG] Font inference diagnostics")
            print(
                "  font identity:",
                font.get("identity", {}).get("family"),
                font.get("identity", {}).get("style"),
            )
            print("  unicode blocks:")
            for block, count in coverage.get("unicode_blocks", {}).items():
                print(f"    {block}: {count}")
            print("  inferred_languages_map:")
            for lang, info in inferred_languages_map.items():
                print(f"    {lang}: {info}")
            print("  language primary script matching:")
            for lang in inferred_languages_map.keys():
                primary_script = LANGUAGE_PRIMARY_SCRIPT.get(lang)
                matches = primary_script in font_scripts if primary_script else False
                print(
                    f"    {lang}: primary_script={primary_script}, "
                    f"matches_font={matches}"
                )
            print(f"  inferred_scripts (raw): {inferred_scripts}")
            print(f"  inferred_scripts (normalized): {normalized_scripts}")
            print("  inferred_languages_map:")
            pprint.pprint(inferred_languages_map)
            print("  language primary scripts:")
            for lang in inferred_languages_map.keys():
                ps = LANGUAGE_PRIMARY_SCRIPT.get(lang)
                match = ps in font_scripts if ps else False
                print(f"    - {lang}: primary_script={ps}, matches_font={match}")
            print(f"  final language order: {inferred_languages}")
            print()
        # ------------------------------------------------------------

        # Persist inference results (rich, audit-friendly structure)
        font["inference"] = {
            "level": level,
            "scripts": normalized_scripts,
            "languages": inferred_languages,
            # Declared metadata (never overwritten, informational only)
            "declared_scripts": declared_scripts,
            "declared_languages": declared_languages,
            # Raw evidence used for inference
            "unicode_blocks": coverage.get("unicode_blocks", {}),
        }
        logger.debug(
            "font entry parsing completed",
            extra={
                "font_path": font_path,
                "family": family,
                "style": style,
                "scripts_count": len(normalized_scripts),
                "languages_count": len(inferred_languages),
            },
        )

    metadata = data.setdefault("metadata", {})

    # Inventory produced by parse_inventory is schema 1.1 compliant
    metadata["schema_version"] = "1.1"

    metadata["inference_level"] = level
    metadata.setdefault("input_inventory_tool", "parse_font_inventory")
    metadata.setdefault("input_inventory_tool_version", __version__)
    logger.info(
        "font inventory parsing completed",
        extra={
            "fonts_processed": len(data.get("fonts", [])),
        },
    )

    return data


# ============================================================
# CLI
# ============================================================


def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register parse-inventory CLI arguments on an existing parser.
    """
    parser.description = (
        "Parse and enrich a Fontshow font_inventory.json with deterministic inference."
    )
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("font_inventory.json"),
        help="Input font_inventory.json generated by dump_fonts.py",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("font_inventory_enriched.json"),
        help="Output enriched JSON file",
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
    add_common_arguments(parser)


def register_cli(parser) -> None:
    """
    Register parse-inventory CLI arguments.

    This function is used by the top-level fontshow dispatcher.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


def run_parse_font_inventory(
    args,
    *,
    # injectable core functions
    parse_inventory_fn=parse_inventory,
    validate_inventory_fn=validate_inventory,
    # injectable I/O helpers (test-friendly)
    read_text_fn=None,
    write_text_fn=None,
    print_fn=print,
    eprint_fn=None,
) -> int:
    """
    Internal runner for the parse-font-inventory CLI.

        Command-line interface entry point for inventory parsing and inference.

        This function:
        - parses CLI arguments
        - loads a Fontshow font inventory from JSON
        - optionally validates the inventory structure
        - enriches the inventory with deterministic inference results
        - writes the enriched inventory back to disk

        The function handles all user-facing error reporting and exit codes,
        while delegating validation and inference logic to dedicated helpers.

        Notes
        -----
        - This function performs file I/O.
        - Core inference logic is implemented in :func:`parse_inventory`.
        - Validation logic is implemented in :func:`validate_inventory`.

    Why it exists:
    - Makes CLI tests deterministic by allowing injection/stubbing of:
      - core functions (parse_inventory / validate_inventory)
      - I/O (read/write/print)
    - Keeps the public entrypoint stable:
        - top-level dispatcher (fontshow __main__)
        - `python -m fontshow.parse_font_inventory`

    Contract:
    - returns an int exit code
    - performs user-facing output via print_fn/eprint_fn
    """
    if read_text_fn is None:

        def read_text_fn(p: Path) -> str:
            return p.read_text(encoding="utf-8")

    if write_text_fn is None:

        def write_text_fn(p: Path, s: str) -> None:
            return p.write_text(s, encoding="utf-8")

    if eprint_fn is None:

        def eprint_fn(msg: str) -> None:
            print_fn(msg, file=sys.stderr)

    # NOTE: don't call parser.error here: args may come from dispatcher tests.
    if getattr(args, "verbose", False) and getattr(args, "quiet", False):
        eprint_fn("❌ Error: --verbose and --quiet are mutually exclusive")
        return 2

    input_path = args.input
    if not input_path.exists():
        eprint_fn(f"❌ Error: input file not found: {input_path}")
        eprint_fn("Hint: run dump_fonts.py first to generate the inventory.")
        return 1

    logger.debug(
        "inference level enabled",
        extra={"infer_level": args.infer_level},
    )

    data: dict[str, Any] = json.loads(read_text_fn(input_path))

    # --- Soft schema validation (keep behavior, but never crash tests) ---
    metadata = data.setdefault("metadata", {})
    schema_version = metadata.get("schema_version")
    if schema_version is None:
        add_structured_warning(
            data,
            code="missing_schema_version",
            message="Inventory has no schema_version",
            severity="warning",
        )
        metadata["schema_version"] = "1.0"
    elif schema_version != "1.0":
        add_structured_warning(
            data,
            code="unsupported_schema_version",
            message=f"Unsupported schema_version '{schema_version}'",
            severity="warning",
        )

    fonts = data.get("fonts")
    if not isinstance(fonts, list):
        eprint_fn("❌ Error: Invalid inventory JSON: 'fonts' must be a list")
        return 1

    if args.validate_inventory:
        return int(
            validate_inventory_fn(
                data,
                verbose=args.verbose,
                quiet=args.quiet,
            )
        )

    enriched = parse_inventory_fn(data, args.infer_level)

    write_text_fn(
        args.output,
        dumps_pretty(enriched, indent=2, ensure_ascii=False),
    )
    print_fn(f"OK: wrote enriched inventory to {args.output}")
    return 0


def _run_parse_inventory(args) -> int:
    """
    Indirection layer for CLI testing.

    This function exists so CLI tests can monkeypatch it
    without touching the core implementation.
    """
    return run_parse_font_inventory(args)


def run(args):
    """
    Public CLI entrypoint (kept stable).
    Thin wrapper around the injectable runner.
    Needed for tests via the top-level dispatcher.
    """
    return main(args)


def main(args) -> int:
    """
    Public CLI entrypoint (kept stable).
    Thin wrapper around the injectable runner.
    """
    try:
        return _run_parse_inventory(args)
    except Exception as exc:
        if not getattr(args, "quiet", False):
            print(f"ERROR: parse-inventory failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="parse-inventory")
    build_parser(parser)
    args = parser.parse_args()
    sys.exit(main(args))
