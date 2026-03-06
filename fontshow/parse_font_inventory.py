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
import unicodedata
from pathlib import Path
from typing import Any, cast

from fontTools.ttLib import TTFont, TTLibError

from fontshow import __version__
from fontshow.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.common.specimens import choose_language_sample
from fontshow.global_constants import SCHEMA_VERSION
from fontshow.infer_languages import infer_languages
from fontshow.inventory.entry_validation import validate_font_entry
from fontshow.inventory.script_analysis import (
    infer_scripts,
    script_coverage_from_unicode_blocks,
)
from fontshow.inventory.semantic_validation import normalize_languages
from fontshow.json_boundary import normalize_loaded_enums
from fontshow.json_format import dumps_pretty
from fontshow.language_tables import (
    LANGUAGE_INFO,
    SCRIPT_INFO,
)
from fontshow.logging_utils import log, log_trace_cat
from fontshow.platform_metadata import collect_platform_metadata
from fontshow.schema_validation import (
    _validate_inventory_schema_strict,
    validate_inventory_schema,
)
from fontshow.types import (
    FontRef,
    LanguageInferenceInfo,
    ScriptISO,
    Severity,
    WarningInfo,
    normalize_script_iso,
)
from fontshow.unicode.charset_ranges import (
    decode_fc_charset_bitmap,
    normalize_charset_ranges,
    unicode_blocks_from_charset_ranges,
)
from fontshow.unicode_tables import UNICODE_SCRIPT_RANGES
from fontshow.warnings import add_structured_warning

# ============================================================
# Set up logger
# ============================================================
logger = logging.getLogger("fontshow")


def validate_inventory(
    data: object,
) -> int:
    """
    Validate a Fontshow font inventory structure.

     Parameters
     ----------
     data : dict[str, Any]
         Parsed inventory JSON object.

     Returns
     -------
     int
         Number of font entries with fatal validation errors.
         Zero indicates a valid inventory.

     Notes
     -----
     - Performs both fatal validation and non-fatal consistency checks.
     - Validation is exhaustive: all entries are inspected in one pass.
     - Function never raises and does not mutate inference results.
     - Structured warnings may be injected into the inventory.

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
    """
    fatal_errors = 0
    warnings = 0

    from collections.abc import Mapping

    if not isinstance(data, Mapping):
        log_err("Inventory root is not a JSON object")
        return 1

    data = dict(data)  # defensive copy to allow safe normalization
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        log_err("'metadata' field missing or not an object (schema 1.2 required)")
        return 1

    schema_version = metadata.get("schema_version")
    if schema_version != "1.2":
        log_err(
            f"Unsupported schema_version '{schema_version}': only '1.2' is accepted"
        )
        return 1

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
    for idx, font in enumerate(fonts):
        ident = _format_font_identity(font, index=idx)
        for warning in font.get("warnings", []):
            log_warn(f"Warning [{ident}]: {warning['code']} - {warning['message']}")

    if fatal_errors == 0:
        # NOTE:
        # Do NOT replace this with a generic "OK" message.
        # Unlike preflight or dump-fonts, parse-inventory is a
        # user-facing diagnostic command and must emit a
        # human-readable success message.
        #
        # See: docs/decisions/0009-cli-verbosity-contract.md
        log_ok(
            "Inventory validation completed (no fatal errors)",
            f"Validation completed for {len(fonts)} font entries",
        )
    else:
        log_info(
            "Inventory validation completed with fatal errors",
            f"Validation completed for {len(fonts)} font entries"
            f" with {fatal_errors} fatal errors and {warnings} warnings",
        )

    return fatal_errors


def _format_font_identity(font: dict, index: int) -> str:
    """
    Build a human-readable identifier for a font entry.

    Parameters
    ----------
    font : dict
        Font entry object.
    index : int
        Index of the font entry in the inventory.

    Returns
    -------
    str
        Human-readable identifier in the form:
        "font[<index>] <filename>[:<face_index>]".

    Notes
    -----
    - Compatible with schema 1.0 and 1.1 layouts.
    - Intended for diagnostics and CLI output only.
    - Does not modify the font entry.
    """
    label = f"font[{index}]"

    path = _get_font_path_for_diagnostics(font)
    family = font.get("family")
    subfamily = font.get("subfamily")

    if path:
        name = Path(path).name
        if family is not None:
            if subfamily is not None:
                name += f" ({family} {subfamily})"
            else:
                name += f" ({family})"
        return f"{label} {name}"

    return label


def _language_base_tag(raw: Any) -> str:
    """
    Extract a conservative base language tag for normalization.

    Parameters
    ----------
    raw : Any
        Raw language tag value (expected to be a string; other types yield "").

    Returns
    -------
    str
        Lowercased base language tag with:
        - any parenthesized suffix stripped,
        - any region/script/variant portion stripped (split on "-" or "_").

    Notes
    -----
    Examples:
    - "yuw(s)" -> "yuw"
    - "az-az"  -> "az"
    - "pt_BR"  -> "pt"
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
    Return the best-available font file path for diagnostics.

    Parameters
    ----------
    font : dict
        Font entry dictionary from the inventory.

    Returns
    -------
    str | None
        Resolved path string according to preference order:
        1. font["path"] (schema >= 1.1)
        2. font["identity"]["file"] (schema 1.0)
        Returns None if no usable path is found.

    Notes
    -----
    - This function is read-only and MUST NOT mutate the input.
    - Used exclusively for human-readable diagnostics.
    """
    if isinstance(font, dict):
        if font.get("path"):
            return font.get("path")

        identity = font.get("identity")
        if isinstance(identity, dict):
            return identity.get("file")

    return None


# ============================================================
# Specimen Engine — Deterministic (Issue #54)
# ============================================================

MIN_SAMPLE_GLYPHS = 20
CMAP_FALLBACK_GLYPHS = 50


def _specimen_is_variation_selector(cp: int) -> bool:
    """
    Check whether a Unicode codepoint is a variation selector.

    Parameters
    ----------
    cp : int
        Unicode codepoint.

    Returns
    -------
    bool
        True if the codepoint is a Unicode variation selector, otherwise False.

    Notes
    -----
    - Variation selectors modify glyph appearance and are not counted as
      standalone printable glyphs in specimen generation.
    - Covers both standard and supplementary variation selector ranges.
    """
    return (0xFE00 <= cp <= 0xFE0F) or (0xE0100 <= cp <= 0xE01EF)


def _specimen_is_control_like(cp: int) -> bool:
    return unicodedata.category(chr(cp)) in {"Cc", "Cf", "Cs", "Co", "Cn"}


def _specimen_is_mark(cp: int) -> bool:
    return unicodedata.category(chr(cp)) in {"Mn", "Mc"}


def _specimen_skip(cp: int) -> bool:
    return (
        _specimen_is_control_like(cp)
        or _specimen_is_variation_selector(cp)
        or _specimen_is_mark(cp)
    )


def _specimen_preference(cp: int) -> int:
    import unicodedata

    cat = unicodedata.category(chr(cp))
    if cat.startswith("L"):
        return 0
    if cat == "Nd":
        return 1
    return 2


def _specimen_filter_text(text: str, cps: set[int]) -> tuple[str, int]:
    out: list[str] = []
    glyphs = 0
    prev_base = False

    for ch in text:
        cp = ord(ch)

        if (
            cp not in cps
            or _specimen_is_control_like(cp)
            or _specimen_is_variation_selector(cp)
        ):
            prev_base = False
            continue

        if _specimen_is_mark(cp):
            if not prev_base:
                continue
            out.append(ch)
            continue

        out.append(ch)
        glyphs += 1
        prev_base = True

    return "".join(out), glyphs


def _specimen_collect_cmap(path: str | None, ttc_index: int | None) -> set[int]:
    if not isinstance(path, str) or not path:
        return set()
    try:
        tt = TTFont(
            path,
            fontNumber=ttc_index if isinstance(ttc_index, int) else 0,
            lazy=True,
            recalcBBoxes=False,
            recalcTimestamp=False,
        )
    except (OSError, ValueError, TTLibError):
        return set()

    cps: set[int] = set()
    if "cmap" not in tt:
        return cps
    for sub in tt["cmap"].tables:
        if not sub.isUnicode():
            continue
        for cp in sub.cmap:
            cps.add(int(cp))
            if len(cps) >= 200_000:
                return cps
    return cps


def _specimen_from_internal(
    font: dict[str, Any],
    cps: set[int],
) -> tuple[str | None, str | None]:
    """
    Level 1 — Use internal sample text if present and usable.
    """

    text = font.get("sample_text")

    if not isinstance(text, str) or not text.strip():
        return None, "no_internal_sample"

    filtered, glyphs = _specimen_filter_text(text, cps)

    if glyphs == 0:
        return None, "internal_sample_no_supported_glyphs"

    if glyphs < MIN_SAMPLE_GLYPHS:
        return None, "internal_sample_too_short"

    return filtered, "internal"


def _specimen_from_script(
    coverage: dict[str, Any],
    cps: set[int],
) -> tuple[str | None, str | None]:
    """
    Level 2 — Use script-derived fallback sample.

    Deterministic selection:
    1) Use dominant script by coverage ratio if available
    2) Otherwise fallback to first declared script
    """

    scripts = coverage.get("scripts")

    if not isinstance(scripts, list) or not scripts:
        return None, "no_scripts"

    # --- Select dominant script by coverage if available ---
    script: str | None = None
    script_cov = coverage.get("script_coverage_from_charset")

    if isinstance(script_cov, dict) and script_cov:
        try:
            script = max(script_cov.items(), key=lambda kv: kv[1])[0]
        except (TypeError, ValueError):
            script = None

    # --- Fallback to declared order ---
    if not script:
        script_raw = scripts[0]
        if not isinstance(script_raw, str):
            return None, "no_scripts"
        script = script_raw.strip()
        if not script:
            return None, "no_scripts"

    # --- Canonical ISO script lookup (Phase 5) ---
    script_iso = cast("ScriptISO", normalize_script_iso(script))

    info = SCRIPT_INFO.get(script_iso)
    text = info["specimen"] if info else None

    if not isinstance(text, str) or not text.strip():
        return None, "no_script_sample"

    filtered, glyphs = _specimen_filter_text(text, cps)

    if glyphs == 0:
        return None, "script_sample_no_supported_glyphs"

    # Reject weak script sample when density too low vs cmap
    if cps:
        try:
            density = glyphs / max(len(cps), 1)
        except (TypeError, ZeroDivisionError):
            density = 0.0

        # empirical safe floor — prevents misleading tiny samples
        if density < 0.01:
            return None, "script_sample_too_sparse"

    return filtered, "script"


def _specimen_from_cmap(
    font: dict[str, Any],
    cps: set[int],
) -> tuple[str, str]:
    ordered = sorted(cps, key=_specimen_preference)
    chosen: list[int] = []

    for cp in ordered:
        if _specimen_skip(cp):
            continue
        chosen.append(cp)
        if len(chosen) >= CMAP_FALLBACK_GLYPHS:
            break

    add_structured_warning(
        font,
        code="specimen_cmap_fallback",
        message="Specimen generated via cmap fallback",
        severity=Severity.INFO,
    )

    return "".join(chr(cp) for cp in chosen), "cmap"


def _specimen_apply_semantic_validation(
    font: dict[str, Any],
    filtered: str,
    g: int,
    cps: set[int] | None,
) -> tuple[str, int, str | None]:
    """
    Ensure specimen characters belong to the font cmap.
    Returns possibly modified (filtered, glyph_count, strategy).
    """
    if not cps:
        return filtered, g, None

    invalid = [c for c in filtered if ord(c) not in cps]
    if not invalid:
        return filtered, g, None

    inference_raw = font.get("inference") or {}
    inference = inference_raw if isinstance(inference_raw, dict) else {}
    langs_raw = inference.get("languages")
    inferred_languages: list[str] = langs_raw if isinstance(langs_raw, list) else []

    scripts_raw = inference.get("scripts")
    inferred_scripts: list[str] = scripts_raw if isinstance(scripts_raw, list) else []

    sample = choose_language_sample(inferred_languages, inferred_scripts)

    if isinstance(sample, str) and sample:
        candidate, cand_g = _specimen_filter_text(sample, cps)
        if candidate and cand_g > 0:
            return candidate, int(cand_g), "validated-language-sample"

    fallback = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return fallback, len(fallback), "validated-fallback"


def _specimen_generate_for_font(
    font: dict[str, Any],
    coverage: dict[str, Any],
    font_path: str | None,
) -> None:
    """
    Deterministic specimen generator (3-level fallback).

    Writes:
        specimen_text
        specimen_strategy
        specimen_glyph_count
        specimen_rejection_reason
    """
    identity = font.get("identity", {})
    ttc_index = identity.get("ttc_index")

    cps = _specimen_collect_cmap(font_path, ttc_index)

    specimen_text: str | None = None
    strategy: str | None = None
    rejection: str | None = None
    fallback_depth = 0

    # Level 1
    specimen_text, strategy = _specimen_from_internal(font, cps)
    if specimen_text is None:
        rejection = strategy
        strategy = None
        fallback_depth = 1

    # Level 2
    if specimen_text is None:
        specimen_text, strategy = _specimen_from_script(coverage, cps)
        if specimen_text is not None:
            fallback_depth = 2

    # Level 3
    if specimen_text is None and cps:
        specimen_text, strategy = _specimen_from_cmap(font, cps)
        rejection = rejection or "fallback_to_cmap"
        if specimen_text is not None:
            fallback_depth = 3

    if not specimen_text:
        specimen_text = " "
        strategy = "cmap"
        rejection = rejection or "no_printable_glyphs"

    filtered, g = (
        _specimen_filter_text(specimen_text, cps)
        if cps
        else (specimen_text, len(specimen_text))
    )

    # --- FINAL SAFETY GUARD ---
    if not filtered or g == 0:
        filtered = " "
        g = 1
        rejection = rejection or "no_printable_glyphs"
        strategy = strategy or "cmap"

    # HARDEN-E — ensure visible printable output (no whitespace-only specimen)
    if not filtered.strip():
        replacement = None
        if cps:
            for cp in sorted(cps):
                ch = chr(cp)
                if ch.strip():
                    replacement = ch
                    break

        if replacement is None:
            replacement = "?"

        filtered = replacement
        g = 1
        rejection = rejection or "no_visible_glyphs"

    # --- SPECIMEN SEMANTIC VALIDATION ---
    new_filtered, new_g, new_strategy = _specimen_apply_semantic_validation(
        font,
        filtered,
        g,
        cps,
    )

    if new_strategy is not None:
        filtered = new_filtered
        g = new_g
        strategy = new_strategy
        rejection = "specimen_not_in_cmap"

    font["specimen_text"] = filtered
    font["specimen_strategy"] = strategy or "cmap"
    font["specimen_rejection_reason"] = rejection
    font["specimen_glyph_count"] = int(g)

    log_trace_cat(
        log,
        "specimen",
        "specimen generated",
        extra={
            "strategy": font["specimen_strategy"],
            "glyph_count": font["specimen_glyph_count"],
            "fallback_depth": fallback_depth,
            "rejection": font["specimen_rejection_reason"],
        },
    )


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
        profile = LANGUAGE_INFO.get(lang)
        primary_script = (
            str(profile["scripts"][0]) if profile and profile.get("scripts") else None
        )
        matches = primary_script in font_scripts if primary_script else False
        log_info(f"    {lang}: primary_script={primary_script}, matches_font={matches}")

    log_info(f"  inferred_scripts (normalized): {inferred_scripts}")

    log_info("  inferred_languages_map (pretty):")
    for line in pprint.pformat(inferred_languages_map).splitlines():
        log_info(line)

    log_info("  language primary scripts:")
    for lang in inferred_languages_map:
        profile = LANGUAGE_INFO.get(lang)
        ps = str(profile["scripts"][0]) if profile and profile.get("scripts") else None
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
        severity_counts: dict[Severity, int] = {}
        for w in schema_warnings:
            sev = w.get("severity", Severity.WARN)
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

    inference = font.get("inference")
    if isinstance(inference, dict):
        if not coverage.get("languages"):
            inferred_languages = inference.get("languages")
            if isinstance(inferred_languages, list) and inferred_languages:
                coverage["languages"] = inferred_languages

        if not coverage.get("scripts"):
            inferred_scripts = inference.get("scripts")
            if isinstance(inferred_scripts, list) and inferred_scripts:
                coverage["scripts"] = inferred_scripts

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
                "severity": Severity.INFO,
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
                        "severity": Severity.INFO,
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
                    "severity": Severity.INFO,
                    "source": "language_normalization",
                    "extra": {"raw": raw, "normalized": base},
                }
            )
            continue

        font.setdefault("warnings", []).append(
            {
                "code": "language_dropped",
                "message": f"Dropped language '{raw}'",
                "severity": Severity.WARN,
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

    charset = font.get("charset")

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
                        "severity": Severity.WARN,
                        "source": "fontconfig_charset",
                        "extra": {
                            "font_path": font_path,
                            "error_type": type(exc).__name__,
                            "error_reason": str(exc),
                        },
                    }
                )

    charset = font.get("charset")
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
        coverage["script_coverage_from_charset"] = {
            str(normalize_script_iso(script)): value
            for script, value in script_cov.items()
        }
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
            severity=Severity.INFO,
        )

    inferred_scripts = list(infer_scripts(coverage, level) or [])

    normalized_scripts = [str(normalize_script_iso(s)) for s in inferred_scripts]

    # ------------------------------------------------------------------
    # Canonical script field (Step 2 alignment)
    # ------------------------------------------------------------------
    if normalized_scripts:
        coverage["scripts"] = normalized_scripts
        coverage["primary_script"] = normalized_scripts[0]
    else:
        coverage["primary_script"] = "UNKNOWN"

    log_trace_cat(
        log,
        "infer",
        "scripts inferred",
        extra={
            "raw_inferred_scripts": inferred_scripts,
            "level": level,
        },
    )

    inferred_languages_map = infer_languages(
        coverage,
        policy="permissive",
        scripts_list=normalized_scripts,
    )

    log_trace_cat(
        log,
        "infer",
        "language candidates inferred",
        extra={
            "candidates": sorted(inferred_languages_map.keys()),
            "candidates_count": len(inferred_languages_map),
        },
    )

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
        profile = LANGUAGE_INFO.get(lang)
        primary_script = (
            str(profile["scripts"][0]) if profile and profile.get("scripts") else None
        )
        return (
            0 if primary_script and primary_script in font_scripts else 1,
            lang,
        )

    # -------------------------------------------------
    # Script-driven primary language selection
    # -------------------------------------------------

    script_primary_lang = None
    if inferred_scripts:
        primary_script = normalize_script_iso(inferred_scripts[0])
        if primary_script is not None:
            info = SCRIPT_INFO.get(primary_script)
            script_primary_lang = info["display_language"] if info else None
        else:
            script_primary_lang = None

    candidates = list(inferred_languages_map.keys())

    # ensure script language exists
    if script_primary_lang and script_primary_lang not in candidates:
        candidates.insert(0, script_primary_lang)

    inferred_languages = sorted(
        candidates,
        key=_language_sort_key,
    )

    # force canonical script language to front
    if script_primary_lang and script_primary_lang in inferred_languages:
        inferred_languages.remove(script_primary_lang)
        inferred_languages.insert(0, script_primary_lang)

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
        "primary_script": (normalized_scripts[0] if normalized_scripts else "UNKNOWN"),
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

    metadata = data.setdefault("metadata", {})
    metadata["schema_version"] = SCHEMA_VERSION
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
    add_common_arguments(
        parser,
        include_output=True,
        output_default=Path("font_inventory_enriched.json"),
        output_help="Output enriched JSON file",
    )


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
        severity = warning.get("severity", Severity.WARN)

        code = str(warning.get("code", "unknown_warning"))
        message = str(warning.get("message", ""))

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
            if isinstance(norm, str):
                if raw:
                    lang_norm_pairs.append(f"{raw} -> {norm}")
                else:
                    lang_norm_pairs.append(norm)
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

        if severity in (Severity.WARN, Severity.ERROR):
            other_warnings.append((severity.name.lower(), code, message))

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

        if rc == 0:
            log_ok(
                "Inventory validation completed (no fatal errors)",
                f"Validation completed for {len(data.get('fonts', []))} font entries",
            )
        else:
            log_info("Inventory validation failed with errors")

        return rc

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
