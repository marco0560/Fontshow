"""
Inventory metadata enrichment helpers.

This module implements deterministic metadata enrichment stages used
during the inventory parsing pipeline.

Responsibilities
----------------
- Derive script coverage from Unicode block information.
- Perform language inference based on coverage statistics.
- Normalize language and script metadata.
- Attach derived metadata and structured warnings to inventory entries.

Design principles
-----------------
Metadata enrichment operates exclusively on normalized inventory
structures produced by earlier pipeline stages. The module performs
pure data transformations and must not implement CLI orchestration or
external tool interaction.

Architectural role
------------------
This module belongs to the **inventory subsystem** and performs the
metadata enrichment stage used during the `parse-inventory` workflow.
"""

from typing import Any, TypedDict, cast

from fontshow.core.cli_utils import log_info
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import (
    CatalogFontEntryV12,
    FontRef,
    JSONDict,
    LanguageInferenceInfo,
    Severity,
    normalize_script_iso,
)
from fontshow.inventory.infer_languages import infer_languages
from fontshow.inventory.script_analysis import (
    infer_scripts,
    script_coverage_from_unicode_blocks,
)
from fontshow.inventory.semantic_validation import normalize_languages
from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO
from fontshow.ontology.unicode_tables import UNICODE_SCRIPT_RANGES
from fontshow.unicode.charset_ranges import (
    decode_fc_charset_bitmap,
    normalize_charset_ranges,
    unicode_blocks_from_charset_ranges,
)


class CharsetBlockCountMismatch(TypedDict):
    """
    Count mismatch for one Unicode block.

    Parameters
    ----------
    block : str
        Unicode block name whose counts differ.
    canonical_count : int
        Count from canonical Unicode block coverage.
    charset_count : int
        Count from charset-derived Unicode block coverage.
    """

    block: str
    canonical_count: int
    charset_count: int


class CharsetBlockMismatchDetails(TypedDict):
    """
    Structured mismatch details for canonical and charset-derived blocks.

    Parameters
    ----------
    canonical_only_blocks : list[str]
        Blocks present only in canonical Unicode block coverage.
    charset_only_blocks : list[str]
        Blocks present only in charset-derived Unicode block coverage.
    differing_counts : list[CharsetBlockCountMismatch]
        Blocks present in both sources with different counts.
    """

    canonical_only_blocks: list[str]
    charset_only_blocks: list[str]
    differing_counts: list[CharsetBlockCountMismatch]


# ============================================================
# Helper: normalize & process language metadata
# ============================================================


def _process_language_metadata(
    font: FontRef,
    coverage: JSONDict,
    *,
    strict_bcp47: bool,
) -> None:
    """
    Normalize language metadata and attach normalization warnings.

    Parameters
    ----------
    font : FontRef
        Inventory entry being enriched with warning records.
    coverage : JSONDict
        Coverage block whose language and script fields are normalized in
        place.
    strict_bcp47 : bool
        Whether invalid BCP-47 tags must be rejected strictly during
        normalization.

    Returns
    -------
    None

    Notes
    -----
    The helper copies inferred languages and scripts into coverage when
    those fields are missing, preserves the original raw language list
    in ``languages_raw``, and injects structured warnings for
    deprecated, normalized, duplicate, and dropped language tags.
    """
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
        raw = dropped_item.get("raw")
        reason = dropped_item.get("reason")
        if raw is None or reason is None:
            continue

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
    font: FontRef,
    coverage: JSONDict,
    inferred_languages_map: dict[str, "LanguageInferenceInfo"],
    inferred_languages: list[str],
) -> None:
    """
    Emit detailed inference diagnostics when FONTSHOW_DEBUG_INFERENCE=1.

    Parameters
    ----------
    font : FontRef
        Inventory entry whose inference state is being inspected.
    coverage : JSONDict
        Coverage block used during inference.
    inferred_languages_map : dict[str, LanguageInferenceInfo]
        Mapping of inferred language candidates and their evidence.
    inferred_languages : list[str]
        Final ordered language list attached to the font.

    Returns
    -------
    None

    Notes
    -----
    Debug-only helper isolated from core parsing logic.
    No-op unless the debug environment variable is enabled.

    The emitted output is intended for developer diagnostics and is not
    part of the stable CLI contract.
    """
    import os
    import pprint

    if os.environ.get("FONTSHOW_DEBUG_INFERENCE") != "1":
        return

    inferred_scripts = font.get("inference", {}).get("scripts", [])
    font_scripts = set(inferred_scripts)

    log_info("\n[DEBUG] Font inference diagnostics")
    log_info(f"  font identity: {font.get('family')}, {font.get('subfamily')}")

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


def _charset_block_mismatch_details(
    canonical_blocks: dict[str, int],
    charset_blocks: dict[str, int],
) -> CharsetBlockMismatchDetails:
    """
    Compute deterministic mismatch details between two block-coverage maps.

    Parameters
    ----------
    canonical_blocks : dict[str, int]
        Canonical Unicode block coverage attached to the font.
    charset_blocks : dict[str, int]
        Unicode block coverage derived from charset ranges.

    Returns
    -------
    CharsetBlockMismatchDetails
        Structured mismatch summary containing blocks present only in one
        source and blocks whose counts differ between sources.

    Notes
    -----
    The result is deterministic:
    - block-name lists are sorted lexically
    - differing-count entries are sorted by block name
    """
    canonical_names = set(canonical_blocks)
    charset_names = set(charset_blocks)

    differing_counts: list[CharsetBlockCountMismatch] = [
        {
            "block": block,
            "canonical_count": canonical_blocks[block],
            "charset_count": charset_blocks[block],
        }
        for block in sorted(canonical_names & charset_names)
        if canonical_blocks[block] != charset_blocks[block]
    ]

    return {
        "canonical_only_blocks": sorted(canonical_names - charset_names),
        "charset_only_blocks": sorted(charset_names - canonical_names),
        "differing_counts": differing_counts,
    }


def _warn_on_charset_block_mismatch(
    font: FontRef,
    coverage: JSONDict,
    *,
    font_path: str | None,
) -> None:
    """
    Attach diagnostics when canonical and charset-derived blocks diverge.

    Parameters
    ----------
    font : FontRef
        Inventory entry updated with structured warnings.
    coverage : JSONDict
        Coverage block containing canonical and charset-derived block maps.
    font_path : str | None
        Filesystem path included in diagnostic payloads.

    Returns
    -------
    None
    """
    canonical_blocks = coverage.get("unicode_blocks")
    charset_blocks = coverage.get("unicode_blocks_from_charset")

    if not isinstance(canonical_blocks, dict) or not isinstance(charset_blocks, dict):
        return
    if not canonical_blocks or not charset_blocks:
        return

    details = _charset_block_mismatch_details(canonical_blocks, charset_blocks)
    if (
        not details["canonical_only_blocks"]
        and not details["charset_only_blocks"]
        and not details["differing_counts"]
    ):
        return

    font.setdefault("warnings", []).append(
        {
            "code": "charset_block_mismatch",
            "message": (
                "Canonical Unicode blocks differ from charset-derived block coverage"
            ),
            "severity": Severity.WARN,
            "source": "fontconfig_charset",
            "extra": {
                "font_path": font_path,
                **details,
            },
        }
    )

    log_trace_cat(
        log,
        "infer",
        "charset block mismatch",
        extra={
            "font_path": font_path,
            "canonical_only_count": len(details["canonical_only_blocks"]),
            "charset_only_count": len(details["charset_only_blocks"]),
            "differing_count_blocks": len(details["differing_counts"]),
        },
    )


def _warn_on_charset_script_mismatch(
    font: FontRef,
    coverage: JSONDict,
    inferred_scripts: list[str],
    *,
    font_path: str | None,
) -> None:
    """
    Attach diagnostics when charset-derived and canonical script leaders diverge.

    Parameters
    ----------
    font : FontRef
        Inventory entry updated with structured warnings.
    coverage : JSONDict
        Coverage block that may contain charset-derived script coverage.
    inferred_scripts : list[str]
        Canonical inferred scripts ordered by confidence.
    font_path : str | None
        Filesystem path included in diagnostic payloads.

    Returns
    -------
    None
    """
    if not inferred_scripts:
        return

    raw_charset_scores = coverage.get("script_coverage_from_charset")
    if not isinstance(raw_charset_scores, dict) or not raw_charset_scores:
        return

    comparable_scores = {
        str(script).upper(): float(score)
        for script, score in raw_charset_scores.items()
        if isinstance(script, str) and script.strip() and isinstance(score, int | float)
    }
    if not comparable_scores:
        return

    charset_primary = max(
        sorted(comparable_scores.items()),
        key=lambda item: item[1],
    )[0]
    canonical_primary = str(inferred_scripts[0]).upper()

    if charset_primary == canonical_primary:
        return

    font.setdefault("warnings", []).append(
        {
            "code": "charset_script_mismatch",
            "message": (
                "Charset-derived primary script differs from canonical inferred script"
            ),
            "severity": Severity.INFO,
            "source": "fontconfig_charset",
            "extra": {
                "font_path": font_path,
                "canonical_primary_script": canonical_primary,
                "charset_primary_script": charset_primary,
            },
        }
    )

    log_trace_cat(
        log,
        "infer",
        "charset script mismatch",
        extra={
            "font_path": font_path,
            "canonical_primary_script": canonical_primary,
            "charset_primary_script": charset_primary,
        },
    )


def _process_charset(font: FontRef, coverage: JSONDict, font_path: str | None) -> None:
    """
    Decode and normalize Fontconfig charset metadata.

    Parameters
    ----------
    font : FontRef
        Inventory entry being enriched with charset-derived warnings.
    coverage : JSONDict
        Coverage block updated in place with normalized charset,
        Unicode-block, and script-coverage information.
    font_path : str | None
        Filesystem path used only for diagnostics and warning payloads.

    Returns
    -------
    None

    Notes
    -----
    The helper is best-effort. Charset decode failures emit structured
    warnings, while successful decodes populate normalized charset
    ranges, Unicode blocks, and script coverage derived from those
    ranges.

    The input structures are updated in place and existing non-charset
    metadata is otherwise preserved.
    """
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
        _warn_on_charset_block_mismatch(font, coverage, font_path=font_path)

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
    font: FontRef,
    coverage: JSONDict,
    *,
    level: str,
    font_path: str | None,
) -> None:
    """
    Run script and language inference and attach the normalized result.

    Parameters
    ----------
    font : FontRef
        Inventory entry updated in place with inference results.
    coverage : JSONDict
        Coverage block supplying declared metadata and derived Unicode
        statistics.
    level : str
        Inference aggressiveness level forwarded to script inference.
    font_path : str | None
        Filesystem path used for diagnostics only.

    Returns
    -------
    None

    Notes
    -----
    This helper normalizes declared scripts, infers scripts and
    languages, ranks candidate languages by script affinity, attaches
    the final inference block, and optionally emits debug diagnostics.
    """
    family = font.get("family")
    style = font.get("subfamily")

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

    inferred_scripts = list(infer_scripts(coverage, level) or [])

    normalized_scripts = [str(normalize_script_iso(s)) for s in inferred_scripts]
    _warn_on_charset_script_mismatch(
        font,
        coverage,
        normalized_scripts,
        font_path=font_path,
    )

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
        """
        Rank inferred languages by script affinity and lexical stability.

        Parameters
        ----------
        lang : str
            Candidate language code to rank.

        Returns
        -------
        tuple[int, str]
            Sort key that prioritizes languages whose primary script is
            present in the font, then falls back to lexical ordering.
        """
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
    blocks_present = set((coverage.get("unicode_blocks", {}) or {}).keys())

    # ensure script language exists
    if (
        script_primary_lang
        and script_primary_lang not in candidates
        and not (font_scripts == {"LATN"} and blocks_present == {"Basic Latin"})
    ):
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

    Examples
    --------
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


def font_family(font: CatalogFontEntryV12 | dict[str, object]) -> str:
    """
    Return a best-effort font family name for rendering and sorting.

    Parameters
    ----------
    font : dict[str, object]
        Inventory font descriptor dictionary.

    Returns
    -------
    str
        Resolved family name if available, otherwise "Unknown Font".
    """
    fam = font.get("family") or font.get("postscript_name") or font.get("full_name")

    return fam if isinstance(fam, str) and fam else "Unknown Font"
