"""
Specimen generation engine for font inventory entries.

This module implements the deterministic specimen generation pipeline used
during inventory parsing. A specimen is a representative string of characters
that can be rendered later in the catalog to demonstrate a font's glyph
coverage.

Design goals
------------
- Deterministic: the same font always produces the same specimen.
- Script-aware: prefer internally curated samples when possible.
- Robust fallback: derive specimens from cmap coverage when no curated
  sample is available.
- Rendering-safe: filter out problematic characters (control codes,
  variation selectors, combining marks, etc.) that would break LaTeX
  rendering or produce misleading output.

Generation strategy
-------------------
Specimen generation follows a strict fallback order:

1. **Internal curated sample**
   If the font family provides an internal specimen sample, it is filtered
   and used preferentially.

2. **Script sample**
   If script inference identifies a primary writing system, a curated
   script-level sample is selected.

3. **cmap fallback**
   If no curated samples are available, a deterministic selection of glyphs
   is extracted from the font's Unicode cmap.

All candidate characters are filtered through a semantic validation layer
to avoid problematic codepoints and ensure that the resulting specimen is
safe for downstream rendering.

Architectural role
------------------
This module belongs to the **inventory domain layer** and is used during
the `parse_font_inventory` pipeline to enrich font entries with specimen
data. It does not perform rendering itself; rendering is handled later by
the catalog/LaTeX subsystem.

The functions here operate purely on font metadata and Unicode data and
must remain free of CLI or pipeline orchestration logic.
"""

import unicodedata
from typing import Any, cast

from fontTools.ttLib import TTFont, TTLibError

from fontshow.common.specimens import choose_language_sample
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import ScriptISO, Severity, normalize_script_iso
from fontshow.core.warnings import add_structured_warning
from fontshow.ontology.language_tables import SCRIPT_INFO

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
