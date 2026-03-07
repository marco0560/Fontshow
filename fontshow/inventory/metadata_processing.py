"""
Inventory metadata enrichment helpers.

This module implements the deterministic enrichment stages used by the
inventory parsing pipeline. These stages transform raw font inventory
entries by attaching derived metadata such as language information,
script coverage, and normalized charset information.

The functions here are called by the parse_inventory pipeline but do not
perform any CLI or orchestration logic themselves.
"""

from typing import Any, cast

from fontshow.cli_utils import log_info
from fontshow.infer_languages import infer_languages
from fontshow.inventory.script_analysis import (
    infer_scripts,
    script_coverage_from_unicode_blocks,
)
from fontshow.inventory.semantic_validation import normalize_languages
from fontshow.language_tables import LANGUAGE_INFO, SCRIPT_INFO
from fontshow.logging_utils import log, log_trace_cat
from fontshow.types import LanguageInferenceInfo, Severity, normalize_script_iso
from fontshow.unicode.charset_ranges import (
    decode_fc_charset_bitmap,
    normalize_charset_ranges,
    unicode_blocks_from_charset_ranges,
)
from fontshow.unicode_tables import UNICODE_SCRIPT_RANGES
from fontshow.warnings import add_structured_warning

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

                log.debug(
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

    log.debug(
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
        log.debug(
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
        log.debug(
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

    log.debug(
        "font entry parsing completed",
        extra={
            "font_path": font_path,
            "family": family,
            "style": style,
            "scripts_count": len(normalized_scripts),
            "languages_count": len(inferred_languages),
        },
    )


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
