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
import re
import sys
from pathlib import Path
from typing import Any, cast

from fontshow import __version__
from fontshow.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.dump_fonts import UNICODE_BLOCKS
from fontshow.infer_languages import infer_languages
from fontshow.json_format import dumps_pretty
from fontshow.logging_utils import log, log_trace_cat
from fontshow.schema_validation import validate_inventory_schema
from fontshow.semantic_validation import normalize_languages
from fontshow.types import (
    FontRef,
    LanguageInferenceInfo,
    WarningInfo,
)

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
    _ = index  # for potential future use in error messages
    errors: list[str] = []

    if not isinstance(entry, dict):
        return ["entry is not an object"]

    identity = entry.get("identity") or {}
    identity_raw = entry.get("identity")
    if identity_raw is not None and not isinstance(identity_raw, dict):
        return ["identity must be an object or null"]

    identity = identity_raw or {}

    base_names = entry.get("base_names") or []

    # If base_names is present, identity is optional
    if not base_names:
        if not isinstance(identity, dict):
            errors.append("missing required field: identity (expected object)")
        else:
            if not identity.get("file"):
                errors.append(
                    "missing required field: identity.file (expected non-empty string)"
                )
            if not identity.get("family"):
                errors.append(
                    "missing required field: identity.family (expected non-empty string)"
                )
            if not identity.get("style"):
                errors.append(
                    "missing required field: identity.style (expected non-empty string)"
                )

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
    data: dict[str, Any],
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
        log_err("Inventory root is not a JSON object")
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

    raw_fonts = data.get("fonts")
    if not isinstance(raw_fonts, list):
        log_err("'fonts' field missing or not a list")
        return 1

    fonts: list[dict[str, Any]] = [f for f in raw_fonts if isinstance(f, dict)]

    for idx, font in enumerate(fonts):
        # ---------- Fatal entry validation ----------
        entry_errors = validate_font_entry(font, index=idx)
        if entry_errors:
            fatal_errors += 1
            path = _get_font_path_for_diagnostics(font)

            log_err(f"[ERR] font[{idx}]")
            log_err(f"  path: {path}")
            for err in entry_errors:
                log_err(f"  - {err}")

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
            ident = _format_font_identity(font, index=idx)
            for warning in font.get("warnings", []):
                log_warn(f"Warning [{ident}]: {warning['code']} - {warning['message']}")

    if fatal_errors == 0 and not quiet:
        # NOTE:
        # Do NOT replace this with a generic "OK" message.
        # Unlike preflight or dump-fonts, parse-inventory is a
        # user-facing diagnostic command and must emit a
        # human-readable success message.
        #
        # See: docs/decisions/0009-cli-verbosity-contract.md
        log_ok("Inventory validation completed (no fatal errors)")
        if verbose:
            log_info(f"Validation completed for {len(fonts)} font entries")

    return fatal_errors


def _format_font_identity(font: dict, index: int) -> str:
    """
    Return a human-readable identifier for a font entry,
    compatible with schema 1.0 and 1.1.

    Format:
        font[<index>] <filename>:<face_index>
    """
    label = f"font[{index}]"

    identity = font.get("identity", {})
    path = _get_font_path_for_diagnostics(font)
    face_index = identity.get("face_index")
    family = identity.get("family")
    style = identity.get("style")

    if path:
        name = Path(path).name
        if family is not None:
            if style is not None:
                name += f" ({family} {style})"
            else:
                name += f" ({family})"
        if face_index is not None:
            return f"{label} {name}:{face_index}"
        return f"{label} {name}"

    return label


def _language_base_tag(raw: str) -> str:
    """
    Extract a conservative base language tag used by our normalization rules.

    Examples:
        "yuw(s)"  -> "yuw"
        "az-az"   -> "az"
        "pt_BR"   -> "pt"
    """
    if not isinstance(raw, str):
        return ""

    value = raw.strip().lower()

    # Strip parenthesized suffix
    if "(" in value:
        value = value.split("(", 1)[0]

    # Strip region/script/variants
    if "-" in value:
        value = value.split("-", 1)[0]
    elif "_" in value:
        value = value.split("_", 1)[0]

    return value


def _get_font_path_for_diagnostics(font: dict) -> str | None:
    """
    Return the best-available path for diagnostics purposes only.

    Preference order:
    1. font["path"]            (schema >= 1.1)
    2. font["identity"]["file"] (schema 1.0)

    This function MUST NOT mutate data.
    """
    if isinstance(font, dict):
        if font.get("path"):
            return font.get("path")

        identity = font.get("identity")
        if isinstance(identity, dict):
            return identity.get("file")

    return None


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


# TODO(#0): classification rule table will grow;
# refactor to data-driven mapping when script set expands
def infer_scripts(  # noqa: C901, PLR0912
    coverage: dict[str, Any], level: str = "medium"
) -> list[str]:
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
            # medium - default
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
# Core processing with helpers
# ============================================================

# ============================================================
# Helper: optional debug dump for inference (env-controlled)
# ============================================================


def _debug_dump_inference(
    font: dict[str, Any],
    coverage: dict[str, Any],
    inferred_languages_map: dict[str, "LanguageInferenceInfo"],
    inferred_languages: list[str],
) -> None:
    """
    Emit detailed inference diagnostics when FONTSHOW_DEBUG_INFERENCE=1.

    Debug-only helper isolated from core parsing logic.
    No-op unless the debug environment variable is enabled.
    """
    import os
    import pprint

    if os.environ.get("FONTSHOW_DEBUG_INFERENCE") != "1":
        return

    identity = font.get("identity", {})
    inferred_scripts = font.get("inference", {}).get("scripts", [])
    font_scripts = set(inferred_scripts)

    log_info("\n[DEBUG] Font inference diagnostics")
    log_info(f"  font identity: {identity.get('family')}, {identity.get('style')}")

    log_info("  unicode blocks:")
    for block, count in coverage.get("unicode_blocks", {}).items():
        log_info(f"    {block}: {count}")

    log_info("  inferred_languages_map:")
    for lang, info in inferred_languages_map.items():
        log_info(f"    {lang}: {info}")

    log_info("  language primary script matching:")
    for lang in inferred_languages_map:
        primary_script = LANGUAGE_PRIMARY_SCRIPT.get(lang)
        matches = primary_script in font_scripts if primary_script else False
        log_info(f"    {lang}: primary_script={primary_script}, matches_font={matches}")

    log_info(f"  inferred_scripts (normalized): {inferred_scripts}")

    log_info("  inferred_languages_map (pretty):")
    for line in pprint.pformat(inferred_languages_map).splitlines():
        log_info(line)

    log_info("  language primary scripts:")
    for lang in inferred_languages_map:
        ps = LANGUAGE_PRIMARY_SCRIPT.get(lang)
        match = ps in font_scripts if ps else False
        log_info(f"    - {lang}: primary_script={ps}, matches_font={match}")

    log_info(f"  final language order: {inferred_languages}")


# ============================================================
# Helper: schema validation + warning injection
# ============================================================


def _apply_schema_validation(data: dict[str, Any]) -> None:
    """Validate schema and inject structured warnings into inventory."""

    logger.info(
        "inventory schema validation requested",
        extra={"schema_version": data.get("schema_version")},
    )
    logger.debug("inventory schema validation started")

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


# ============================================================
# Helper: normalize & process language metadata
# ============================================================


def _process_language_metadata(
    font: dict[str, Any],
    coverage: dict[str, Any],
    *,
    strict_bcp47: bool,
) -> None:
    """Normalize languages and inject normalization warnings."""

    if "languages_raw" not in coverage:
        coverage["languages_raw"] = list(coverage.get("languages", []) or [])

    result = normalize_languages(
        coverage["languages_raw"],
        strict_bcp47=strict_bcp47,
    )

    coverage["languages"] = result["normalized"]

    # --- deprecated
    for item in result.get("deprecated", []):
        font.setdefault("warnings", []).append(
            {
                "code": "language_deprecated",
                "message": (
                    f"Deprecated language '{item['from_']}' "
                    f"from '{item['raw']}' -> '{item['to']}'"
                ),
                "severity": "info",
                "source": "language_normalization",
                "extra": item,
            }
        )

    # --- dropped / normalized / duplicate
    for dropped_item in result["dropped"]:
        raw: str = dropped_item["raw"]
        reason: str = dropped_item["reason"]

        if reason == "variant_stripped":
            base = _language_base_tag(raw)
            if base != raw:
                font.setdefault("warnings", []).append(
                    {
                        "code": "language_normalized",
                        "message": f"Normalized language '{raw}' -> '{base}'",
                        "severity": "info",
                        "source": "language_normalization",
                        "extra": {"raw": raw, "normalized": base},
                    }
                )
            continue

        if reason == "duplicate_normalized":
            base = (
                cast("str", dropped_item.get("normalized"))
                if dropped_item.get("normalized")
                else _language_base_tag(raw)
            )
            font.setdefault("warnings", []).append(
                {
                    "code": "language_duplicate",
                    "message": f"Duplicate language '{raw}' (base '{base}')",
                    "severity": "info",
                    "source": "language_normalization",
                    "extra": {"raw": raw, "normalized": base},
                }
            )
            continue

        font.setdefault("warnings", []).append(
            {
                "code": "language_dropped",
                "message": f"Dropped language '{raw}'",
                "severity": "warning",
                "source": "language_normalization",
                "extra": {"raw": raw, "reason": reason},
            }
        )


# ============================================================
# Helper: FontConfig charset decode + normalization
# ============================================================


def _process_charset(
    font: dict[str, Any], coverage: dict[str, Any], font_path: str | None
) -> None:
    """Decode and normalize FontConfig charset metadata."""

    charset = coverage.get("charset")

    if isinstance(charset, dict):
        raw = charset.get("raw")
        if isinstance(raw, str) and raw.strip():
            try:
                ranges = decode_fc_charset_bitmap(raw)
                charset["ranges"] = ranges

                logger.debug(
                    "fontconfig charset bitmap decoded",
                    extra={"font_path": font_path, "ranges_count": len(ranges)},
                )

            except (ValueError, TypeError, IndexError) as exc:
                charset["ranges"] = []

                font.setdefault("warnings", []).append(
                    {
                        "code": "charset_decode_failed",
                        "message": "Fontconfig charset bitmap decoding failed",
                        "severity": "warning",
                        "source": "fontconfig_charset",
                        "extra": {
                            "font_path": font_path,
                            "error_type": type(exc).__name__,
                            "error_reason": str(exc),
                        },
                    }
                )

    charset = coverage.get("charset")
    if not isinstance(charset, dict) or not charset.get("ranges"):
        return

    normalized = normalize_charset_ranges(charset["ranges"])
    coverage["normalized_charset"] = normalized

    log_trace_cat(
        log,
        "infer",
        "charset normalized",
        extra={
            "ranges_count": len(normalized.get("ranges", [])),
            "codepoints_count": normalized.get("codepoints_count"),
        },
    )

    logger.debug(
        "charset normalized",
        extra={
            "font_path": font_path,
            "ranges_count": len(normalized["ranges"]),
            "codepoints_count": normalized["codepoints_count"],
        },
    )

    blocks = unicode_blocks_from_charset_ranges(normalized["ranges"])
    if blocks:
        coverage["unicode_blocks_from_charset"] = blocks
        log_trace_cat(
            log,
            "infer",
            "unicode blocks derived",
            extra={
                "blocks": sorted(blocks.keys()),
                "blocks_count": len(blocks),
            },
        )
        logger.debug(
            "unicode blocks derived from charset",
            extra={"font_path": font_path, "blocks_count": len(blocks)},
        )

    script_cov = script_coverage_from_unicode_blocks(
        blocks,
        UNICODE_SCRIPT_RANGES,
        normalized["codepoints_count"],
    )

    if script_cov:
        coverage["script_coverage_from_charset"] = script_cov
        log_trace_cat(
            log,
            "infer",
            "script coverage from charset",
            extra={
                "scripts": sorted(script_cov.keys()),
                "scripts_count": len(script_cov),
            },
        )
        logger.debug(
            "script coverage derived from charset",
            extra={"font_path": font_path, "scripts_count": len(script_cov)},
        )


# ============================================================
# Helper: inference -> scripts and languages
# ============================================================


def _infer_and_attach_metadata(
    font: dict[str, Any],
    coverage: dict[str, Any],
    *,
    level: str,
    font_path: str | None,
) -> None:
    """Run script & language inference and attach structured result."""

    identity = font.get("identity", {})
    family = identity.get("family")
    style = identity.get("style")

    log_trace_cat(
        log,
        "infer",
        "inference started",
        extra={
            "font_path": font_path,
            "family": family,
            "style": style,
            "coverage_keys": sorted(list(coverage.keys())),
        },
    )

    declared_scripts = list(coverage.get("scripts", []) or [])
    declared_languages = list(coverage.get("languages", []) or [])

    log_trace_cat(
        log,
        "infer",
        "declared metadata",
        extra={
            "declared_scripts": declared_scripts,
            "declared_languages": declared_languages,
        },
    )

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

    inferred_scripts = list(infer_scripts(coverage, level) or [])

    log_trace_cat(
        log,
        "infer",
        "scripts inferred",
        extra={
            "raw_inferred_scripts": inferred_scripts,
            "level": level,
        },
    )

    inferred_languages_map = infer_languages(coverage, policy="permissive")

    log_trace_cat(
        log,
        "infer",
        "language candidates inferred",
        extra={
            "candidates": sorted(inferred_languages_map.keys()),
            "candidates_count": len(inferred_languages_map),
        },
    )

    normalized_scripts = [str(s).upper() for s in inferred_scripts]

    log_trace_cat(
        log,
        "infer",
        "scripts normalized",
        extra={
            "normalized_scripts": normalized_scripts,
        },
    )

    font_scripts = set(normalized_scripts)

    def _language_sort_key(lang: str) -> tuple[int, str]:
        primary_script = LANGUAGE_PRIMARY_SCRIPT.get(lang)
        return (
            0 if primary_script and primary_script in font_scripts else 1,
            lang,
        )

    inferred_languages = sorted(
        inferred_languages_map.keys(),
        key=_language_sort_key,
    )

    log_trace_cat(
        log,
        "infer",
        "languages ranked",
        extra={
            "ordered_languages": inferred_languages,
        },
    )

    _debug_dump_inference(
        font,
        coverage,
        inferred_languages_map,
        inferred_languages,
    )

    font["inference"] = {
        "level": level,
        "scripts": normalized_scripts,
        "languages": inferred_languages,
        "declared_scripts": declared_scripts,
        "declared_languages": declared_languages,
        "unicode_blocks": coverage.get("unicode_blocks", {}),
    }

    log_trace_cat(
        log,
        "infer",
        "inference completed",
        extra={
            "final_scripts": normalized_scripts,
            "final_languages": inferred_languages,
            "declared_scripts": declared_scripts,
            "declared_languages": declared_languages,
        },
    )

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

    Refactored version:
    - reduced complexity
    - separated concerns
    - behavior unchanged
    """

    _apply_schema_validation(data)

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
            extra={"font_path": font_path, "family": family, "style": style},
        )

        coverage: dict[str, Any] = font.get("coverage", {}) or {}

        _process_language_metadata(
            font,
            coverage,
            strict_bcp47=strict_bcp47,
        )

        _process_charset(font, coverage, font_path)

        _infer_and_attach_metadata(
            font,
            coverage,
            level=level,
            font_path=font_path,
        )

    metadata = data.setdefault("metadata", {})
    metadata["schema_version"] = "1.1"
    metadata["inference_level"] = level
    metadata.setdefault("input_inventory_tool", "parse_font_inventory")
    metadata.setdefault("input_inventory_tool_version", __version__)

    logger.info(
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
    parser.add_argument(
        "-s",
        "--strict-bcp47",
        action="store_true",
        help="Reject non-compliant BCP-47 language tags",
    )
    add_common_arguments(parser)


def register_cli(parser) -> None:
    """
    Register parse-inventory CLI arguments.

    This function is used by the top-level fontshow dispatcher.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


# ============================================================
# Helper: default I/O adapters (test-friendly)
# ============================================================


def _default_read_text(p: Path) -> str:
    """Default file reader used when no injectable I/O is provided."""
    return p.read_text(encoding="utf-8")


def _default_write_text(p: Path, s: str) -> None:
    """Default file writer used when no injectable I/O is provided."""
    p.write_text(s, encoding="utf-8")


# ============================================================
# Helper: schema sanity guard (non-fatal)
# ============================================================


def _soft_schema_guard(data: dict[str, Any]) -> None:
    """
    Ensure inventory has a schema_version without failing.

    This preserves legacy behavior and never raises.
    """

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
        return

    if schema_version != "1.0":
        add_structured_warning(
            data,
            code="unsupported_schema_version",
            message=f"Unsupported schema_version '{schema_version}'",
            severity="warning",
        )


# ============================================================
# Helper: validate fonts container
# ============================================================


def _validate_fonts_container(data: dict[str, Any]) -> list[Any] | None:
    """Ensure 'fonts' exists and is a list, otherwise return None."""
    fonts = data.get("fonts")
    if not isinstance(fonts, list):
        log_err("Invalid inventory JSON: 'fonts' must be a list")
        return None
    return fonts


# ============================================================
# Helper: extract language warning aggregates
# ============================================================


def _collect_language_warnings(
    font: FontRef,
) -> tuple[list[str], list[str], list[str], list[tuple[str, str, str]]]:
    """
    Aggregate warnings for grouped CLI display.

    Returns:
        normalized, duplicates, dropped, other_warnings
    """

    lang_norm_pairs: list[str] = []
    lang_dups: list[str] = []
    lang_dropped: list[str] = []
    other_warnings: list[tuple[str, str, str]] = []

    raw_warnings = font.get("warnings")
    warnings_list: list[WarningInfo] = (
        raw_warnings if isinstance(raw_warnings, list) else []
    )

    for warning in warnings_list:
        if not isinstance(warning, dict):
            continue

        severity = warning.get("severity", "warning")
        code = warning.get("code", "unknown_warning")
        message = warning.get("message", "")
        extra_raw = warning.get("extra")
        extra: dict[str, Any] = extra_raw if isinstance(extra_raw, dict) else {}

        def _extract_lang(msg: str) -> str:
            if not msg:
                return ""
            m = re.search(r"'([^']+)'", msg)
            return m.group(1) if m else ""

        if code == "language_normalized":
            raw = extra.get("raw") or _extract_lang(message)
            norm = extra.get("normalized")
            if raw and norm:
                lang_norm_pairs.append(f"{raw} -> {norm}")
            elif raw:
                lang_norm_pairs.append(raw)
            continue

        if code == "language_duplicate":
            raw = extra.get("raw") or _extract_lang(message)
            if raw:
                lang_dups.append(raw)
            continue

        if code == "language_dropped":
            raw = extra.get("raw") or _extract_lang(message)
            if raw:
                lang_dropped.append(raw)
            continue

        if code in {"normalized_languages", "duplicate_languages", "dropped_languages"}:
            continue

        if severity in ("warning", "error"):
            other_warnings.append((severity, code, message))

    return lang_norm_pairs, lang_dups, lang_dropped, other_warnings


# ============================================================
# Helper: verbose warning emitter
# ============================================================


def _emit_verbose_warnings(enriched: dict[str, Any]) -> None:
    """Emit grouped warnings for verbose CLI mode."""

    fonts = enriched.get("fonts", [])
    if not isinstance(fonts, list):
        return

    for idx, font in enumerate(fonts):
        if not isinstance(font, dict):
            continue

        ident = _format_font_identity(font, idx)

        norm, dups, dropped, other = _collect_language_warnings(cast("FontRef", font))

        if norm:
            log_info(f"{ident} normalized_languages: {', '.join(sorted(set(norm)))}")

        if dups:
            log_info(f"{ident} duplicate_languages: {', '.join(sorted(set(dups)))}")

        if dropped:
            log_warn(f"{ident} dropped_languages: {', '.join(sorted(set(dropped)))}")

        for _severity, code, message in other:
            log_warn(f"{ident} {code}: {message}")


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
    Internal runner for parse-font-inventory CLI.

    Refactored version:
    - reduced complexity
    - helpers extracted
    - behavior unchanged
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
        },
    )

    read_text_fn = read_text_fn or _default_read_text
    write_text_fn = write_text_fn or _default_write_text

    input_path = args.input
    if not input_path.exists():
        log_err(f"input file not found: {input_path}")
        log_err("Hint: run dump_fonts.py first to generate the inventory.")
        return 1

    logger.debug("inference level enabled", extra={"infer_level": args.infer_level})

    data: dict[str, Any] = json.loads(read_text_fn(input_path))
    log_trace_cat(
        log,
        "io",
        "inventory JSON loaded",
        extra={
            "fonts": len(data.get("fonts", [])),
            "schema_version": data.get("schema_version"),
        },
    )

    _soft_schema_guard(data)

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
        return int(
            validate_inventory_fn(
                data,
                verbose=args.verbose,
                quiet=args.quiet,
            )
        )

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

    log_ok(f"Inventory written to {args.output}" if args.verbose else "Done.")
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
