"""
Specimen generation engine for font inventory entries.

This module implements the deterministic specimen generation pipeline used
during inventory parsing. A specimen is a representative string of characters
that can be rendered later in the catalog to demonstrate a font's glyph
coverage.

Design principles
-----------------
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
from collections.abc import Callable, Mapping
from typing import Any, cast

from fontTools.ttLib import TTFont, TTLibError

from fontshow.common.specimens import choose_language_sample
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import FontRef, JSONDict, ScriptISO, normalize_script_iso
from fontshow.inventory.schema_accessors import (
    get_sample_text_value,
    set_specimen_fields,
)
from fontshow.ontology.language_tables import SCRIPT_INFO

# ============================================================
# Specimen Engine — Deterministic (Issue #54)
# ============================================================

MIN_SAMPLE_GLYPHS = 20
CMAP_FALLBACK_GLYPHS = 40
_PRIVATE_USE_BLOCK_NAMES = {
    "Private Use Area",
    "Supplementary Private Use Area-A",
    "Supplementary Private Use Area-B",
}
_LATIN_BLOCK_NAMES = {
    "Basic Latin",
    "Latin-1 Supplement",
    "Latin Extended-A",
    "Latin Extended-B",
    "Latin Extended Additional",
    "Latin Extended-C",
    "Latin Extended-D",
    "Latin Extended-E",
    "Latin Extended-F",
    "Latin Extended-G",
}
_SCRIPT_CORE_SPECIMENS: dict[ScriptISO, str] = {
    ScriptISO("ARAB"): "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئىة",
    ScriptISO("BOPO"): "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄚㄛㄜ",
    ScriptISO("CYRL"): "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩабвгдежзийклмнопрстуфхцчшщ",
    ScriptISO("GREK"): "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥαβγδεζηθικλμνξοπρστυ",
    ScriptISO("HANI"): "天地玄黃宇宙洪荒日月盈昃辰宿列張寒來暑往秋收冬藏",
    ScriptISO(
        "JPAN"
    ): "あいうえおかきくけこさしすせそたちつてとアイウエオカキクケコサシスセソ",
    ScriptISO("LATN"): "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
}


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
    """
    Check whether a codepoint belongs to a control-like Unicode category.

    Parameters
    ----------
    cp : int
        Unicode codepoint.

    Returns
    -------
    bool
        True if the character category is one of ``Cc``, ``Cf``, ``Cs``,
        ``Co``, or ``Cn``.
    """
    return unicodedata.category(chr(cp)) in {"Cc", "Cf", "Cs", "Co", "Cn"}


def _specimen_is_private_use(cp: int) -> bool:
    """
    Check whether a codepoint belongs to a Unicode private-use range.

    Parameters
    ----------
    cp : int
        Unicode codepoint.

    Returns
    -------
    bool
        True when the codepoint is inside one of the Unicode private
        use areas.
    """
    return (
        0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFF or 0x100000 <= cp <= 0x10FFFF
    )


def _specimen_is_mark(cp: int) -> bool:
    """
    Check whether a codepoint is a combining mark used in specimen filtering.

    Parameters
    ----------
    cp : int
        Unicode codepoint.

    Returns
    -------
    bool
        True if the character category is ``Mn`` or ``Mc``.
    """
    return unicodedata.category(chr(cp)) in {"Mn", "Mc"}


def _specimen_skip(cp: int) -> bool:
    """
    Decide whether a codepoint must be skipped during specimen selection.

    Parameters
    ----------
    cp : int
        Unicode codepoint.

    Returns
    -------
    bool
        True if the codepoint is control-like, a variation selector, or
        a combining mark.
    """
    return (
        _specimen_is_control_like(cp)
        or _specimen_is_variation_selector(cp)
        or _specimen_is_mark(cp)
    )


def _specimen_preference(cp: int) -> int:
    """
    Compute a stable ordering priority for cmap fallback glyph selection.

    Parameters
    ----------
    cp : int
        Unicode codepoint.

    Returns
    -------
    int
        Preference bucket where letters sort first, decimal digits
        second, and all other categories last.
    """
    import unicodedata

    cat = unicodedata.category(chr(cp))
    if cat.startswith("L"):
        return 0
    if cat == "Nd":
        return 1
    return 2


def _specimen_is_latin_block(block_name: str) -> bool:
    """
    Return whether a Unicode block should count as Latin-family evidence.

    Parameters
    ----------
    block_name : str
        Unicode block name extracted from specimen text.

    Returns
    -------
    bool
        True when the block is one of the Latin-family Unicode blocks
        used by specimen reconciliation heuristics.
    """
    return block_name in _LATIN_BLOCK_NAMES


def _normalize_top_level_specimen_strategy(strategy: str | None) -> str | None:
    """
    Normalize detailed specimen strategies to schema-approved top-level values.

    Parameters
    ----------
    strategy : str | None
        Detailed strategy emitted by internal helper stages.

    Returns
    -------
    str | None
        Schema-approved top-level specimen strategy.
    """
    if not isinstance(strategy, str) or not strategy:
        return strategy
    if strategy.startswith("script"):
        return "script"
    return strategy


def _specimen_filter_text(
    text: str, cps: set[int], *, allow_private_use: bool = False
) -> tuple[str, int]:
    """
    Filter specimen text against cmap support and rendering-safety rules.

    Parameters
    ----------
    text : str
        Candidate specimen text.
    cps : set[int]
        Supported Unicode codepoints for the font.
    allow_private_use : bool, optional
        Whether private-use codepoints should be retained instead of
        being treated as control-like placeholders.

    Returns
    -------
    tuple[str, int]
        Two-element tuple ``(filtered_text, glyph_count)`` where
        `glyph_count` counts accepted base glyphs.

    Notes
    -----
    Combining marks are retained only when they follow an accepted base
    glyph. Unsupported, control-like, and variation-selector codepoints
    are discarded.
    """
    out: list[str] = []
    glyphs = 0
    prev_base = False
    pending_space = False

    for ch in text:
        cp = ord(ch)

        if ch.isspace():
            if out and prev_base:
                pending_space = True
            prev_base = False
            continue

        if (
            cp not in cps
            or (
                _specimen_is_control_like(cp)
                and not (allow_private_use and _specimen_is_private_use(cp))
            )
            or _specimen_is_variation_selector(cp)
        ):
            pending_space = False
            prev_base = False
            continue

        if _specimen_is_mark(cp):
            if not prev_base:
                continue
            out.append(ch)
            continue

        if pending_space and out:
            out.append(" ")
            pending_space = False

        out.append(ch)
        glyphs += 1
        prev_base = True

    return "".join(out), glyphs


def _specimen_repeat_once(text: str, glyphs: int) -> tuple[str | None, int]:
    """
    Duplicate a short specimen once when that reaches the acceptance floor.

    Parameters
    ----------
    text : str
        Filtered specimen candidate.
    glyphs : int
        Accepted base-glyph count for ``text``.

    Returns
    -------
    tuple[str | None, int]
        Doubled specimen text and doubled glyph count, or ``(None, glyphs)``
        when repetition should not be used.
    """
    if not text or glyphs <= 0:
        return None, glyphs
    if glyphs >= MIN_SAMPLE_GLYPHS:
        return text, glyphs
    if glyphs * 2 < MIN_SAMPLE_GLYPHS:
        return None, glyphs
    return f"{text} {text}", glyphs * 2


def _specimen_collect_cmap(path: str | None, ttc_index: int | None) -> set[int]:
    """
    Collect supported Unicode codepoints from the font cmap.

    Parameters
    ----------
    path : str | None
        Filesystem path to the font binary.
    ttc_index : int | None
        Face index for TrueType collections.

    Returns
    -------
    set[int]
        Set of supported Unicode codepoints, capped defensively for very
        large cmaps.

    Notes
    -----
    Extraction is best-effort. Errors while opening or reading the font
    return an empty set rather than raising.
    """
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
        try:
            is_unicode = sub.isUnicode()
            cmap = sub.cmap
        except (AttributeError, TypeError, ValueError):
            continue
        if not is_unicode:
            continue
        try:
            for cp in cmap:
                cps.add(int(cp))
                if len(cps) >= 200_000:
                    return cps
        except (TypeError, ValueError):
            continue
    return cps


class CmapCache:
    """
    Cache font cmap extraction results within one pipeline operation.

    Parameters
    ----------
    collector : Callable[[str | None, int | None], set[int]], optional
        Function used to collect cmap codepoints on cache misses.

    Returns
    -------
    None

    Notes
    -----
    The cache is intentionally process-local and caller-scoped. It avoids
    reopening the same font file repeatedly while keeping each command
    invocation independent.
    """

    def __init__(
        self,
        collector: Callable[
            [str | None, int | None], set[int]
        ] = _specimen_collect_cmap,
    ) -> None:
        self._collector = collector
        self._cache: dict[tuple[str, int | None], set[int]] = {}

    def get(self, path: str | None, ttc_index: int | None = None) -> set[int]:
        """
        Return cached cmap codepoints for one font face.

        Parameters
        ----------
        path : str | None
            Filesystem path to the font binary.
        ttc_index : int | None, optional
            Face index for TrueType collections.

        Returns
        -------
        set[int]
            Supported Unicode codepoints returned by the configured
            collector.
        """
        key = (path or "", ttc_index)
        if key not in self._cache:
            self._cache[key] = self._collector(path, ttc_index)
        return self._cache[key]


def _script_core_specimen_seed(script_iso: ScriptISO) -> str:
    """
    Return the deterministic core-glyph seed for one script.

    Parameters
    ----------
    script_iso : ScriptISO
        Canonical script identifier.

    Returns
    -------
    str
        Script-specific core glyph seed, or an empty string when none is
        defined.
    """
    seed = _SCRIPT_CORE_SPECIMENS.get(script_iso)
    return seed if isinstance(seed, str) else ""


def _script_fallback_specimen(
    script_iso: ScriptISO,
    cps: set[int],
) -> tuple[str | None, int, str | None]:
    """
    Build the best deterministic specimen available for one script.

    Parameters
    ----------
    script_iso : ScriptISO
        Script whose specimen should be resolved.
    cps : set[int]
        Supported Unicode codepoints for the font.

    Returns
    -------
    tuple[str | None, int, str | None]
        ``(specimen_text, glyph_count, strategy)`` for the best script-aware
        sample, or ``(None, 0, None)`` when no meaningful sample can be built.

    Notes
    -----
    Ordered fallback:
    1. curated ontology specimen as-is
    2. one doubled copy of the curated result if that reaches the floor
    3. deterministic script-core seed
    4. one doubled copy of the core-seed result if that reaches the floor
    """
    info = SCRIPT_INFO.get(script_iso)
    curated = info.get("specimen") if isinstance(info, dict) else None
    if isinstance(curated, str) and curated.strip():
        filtered, glyphs = _specimen_filter_text(curated, cps)
        if glyphs >= MIN_SAMPLE_GLYPHS:
            return filtered, glyphs, "script"
        doubled, doubled_glyphs = _specimen_repeat_once(filtered, glyphs)
        if doubled is not None:
            return doubled, doubled_glyphs, "script-doubled"

    seed = _script_core_specimen_seed(script_iso)
    if seed:
        filtered, glyphs = _specimen_filter_text(seed, cps)
        if glyphs >= MIN_SAMPLE_GLYPHS:
            return filtered, glyphs, "script-core"
        doubled, doubled_glyphs = _specimen_repeat_once(filtered, glyphs)
        if doubled is not None:
            return doubled, doubled_glyphs, "script-core-doubled"

    return None, 0, None


def _specimen_from_internal(
    font: FontRef,
    cps: set[int],
) -> tuple[str | None, str | None]:
    """
    Level 1 — Use internal sample text if present and usable.

    Parameters
    ----------
    font : FontRef
        Inventory entry that may carry an embedded sample text.
    cps : set[int]
        Supported Unicode codepoints for the font.

    Returns
    -------
    tuple[str | None, str | None]
        Either ``(filtered_sample, "internal")`` on success or
        ``(None, rejection_reason)`` when the internal sample is absent,
        unsupported, or too short.
    """
    text = get_sample_text_value(font)

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

    Parameters
    ----------
    coverage : dict[str, Any]
        Coverage block containing script metadata and optional
        charset-derived script coverage.
    cps : set[int]
        Supported Unicode codepoints for the font.

    Returns
    -------
    tuple[str | None, str | None]
        Either ``(filtered_sample, "script")`` on success or
        ``(None, rejection_reason)`` when no suitable script sample can
        be produced.

    Notes
    -----
    Deterministic selection:
    1. Use dominant script by coverage ratio if available.
    2. Otherwise fall back to the first declared script.
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

    filtered, glyphs, strategy = _script_fallback_specimen(script_iso, cps)
    if filtered is not None and strategy is not None:
        return filtered, strategy

    seed = _script_core_specimen_seed(script_iso)
    if seed:
        core_filtered, core_glyphs = _specimen_filter_text(seed, cps)
        if core_glyphs == 0:
            return None, "script_sample_no_supported_glyphs"
        return None, "script_sample_too_short"

    filtered, glyphs = _specimen_filter_text(text, cps)
    if glyphs == 0:
        return None, "script_sample_no_supported_glyphs"
    return None, "script_sample_too_short"


def _specimen_from_cmap(
    font: FontRef,
    cps: set[int],
) -> tuple[str, str]:
    """
    Build a deterministic specimen from cmap coverage as the final fallback.

    Parameters
    ----------
    font : FontRef
        Inventory entry being enriched.
    cps : set[int]
        Supported Unicode codepoints extracted from the font cmap.

    Returns
    -------
    tuple[str, str]
        Two-element tuple ``(specimen_text, "cmap")``.

    Notes
    -----
    Candidate codepoints are ordered with `_specimen_preference()` and
    filtered through `_specimen_skip()`.
    """
    ordered = sorted(cps, key=_specimen_preference)
    chosen: list[int] = []

    for cp in ordered:
        if _specimen_skip(cp):
            continue
        chosen.append(cp)
        if len(chosen) >= CMAP_FALLBACK_GLYPHS:
            break

    return "".join(chr(cp) for cp in chosen), "cmap"


def _specimen_from_private_use(
    font: Mapping[str, object],
    cps: set[int],
) -> tuple[str | None, str | None]:
    """
    Build a specimen from private-use glyph coverage when it is substantial.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Inventory entry being enriched.
    cps : set[int]
        Supported Unicode codepoints extracted from the font cmap.

    Returns
    -------
    tuple[str | None, str | None]
        Either ``(specimen_text, "pua")`` on success or
        ``(None, rejection_reason)`` when private-use coverage is too
        small or absent.
    """
    pua_total = _significant_private_use_count(font)
    if pua_total < MIN_SAMPLE_GLYPHS:
        return None, "private_use_not_significant"

    chosen: list[int] = []
    for cp in sorted(cps):
        if not _specimen_is_private_use(cp):
            continue
        if _specimen_is_variation_selector(cp):
            continue
        chosen.append(cp)
        if len(chosen) >= CMAP_FALLBACK_GLYPHS:
            break

    if not chosen:
        return None, "private_use_no_supported_glyphs"

    return "".join(chr(cp) for cp in chosen), "pua"


def _significant_private_use_count(font: Mapping[str, object]) -> int:
    """
    Return the persisted count of private-use coverage for one font.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Inventory entry whose coverage block is inspected.

    Returns
    -------
    int
        Total number of covered codepoints in Unicode private-use blocks.
    """
    coverage_raw = font.get("coverage")
    coverage = coverage_raw if isinstance(coverage_raw, dict) else {}
    blocks_raw = coverage.get("unicode_blocks")
    blocks = blocks_raw if isinstance(blocks_raw, dict) else {}
    return sum(
        int(blocks.get(block_name, 0))
        for block_name in _PRIVATE_USE_BLOCK_NAMES
        if isinstance(blocks.get(block_name, 0), int)
    )


def _has_significant_private_use(font: Mapping[str, object]) -> bool:
    """
    Return whether one font covers a meaningful amount of private-use glyphs.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Inventory entry whose coverage block is inspected.

    Returns
    -------
    bool
        True when the persisted private-use coverage reaches the specimen floor.
    """
    return _significant_private_use_count(font) >= MIN_SAMPLE_GLYPHS


def _specimen_apply_semantic_validation(
    font: FontRef,
    filtered: str,
    g: int,
    cps: set[int] | None,
) -> tuple[str, int, str | None]:
    """
    Ensure specimen characters belong to the font cmap.

    Parameters
    ----------
    font : FontRef
        Inventory entry whose inference metadata may be used for fallback.
    filtered : str
        Current specimen candidate.
    g : int
        Glyph count associated with `filtered`.
    cps : set[int] | None
        Supported Unicode codepoints for the font, if known.

    Returns
    -------
    tuple[str, int, str | None]
        Possibly updated ``(filtered_text, glyph_count, strategy)``
        triple. The strategy is None when no replacement was needed.

    Notes
    -----
    When unsupported characters are detected, the helper first attempts
    a language-based replacement sample and finally falls back to a
    fixed ASCII alphabet specimen.
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


def _specimen_from_language(
    font: FontRef,
    cps: set[int],
) -> tuple[str | None, str | None]:
    """
    Build a specimen from inferred language metadata.

    Parameters
    ----------
    font : FontRef
        Inventory entry whose inference metadata is consulted.
    cps : set[int]
        Supported Unicode codepoints for the font.

    Returns
    -------
    tuple[str | None, str | None]
        Either ``(filtered_sample, "language")`` on success or
        ``(None, rejection_reason)`` when no usable language-aware
        sample can be resolved.
    """
    inference_raw = font.get("inference") or {}
    inference = inference_raw if isinstance(inference_raw, dict) else {}

    langs_raw = inference.get("languages")
    inferred_languages: list[str] = langs_raw if isinstance(langs_raw, list) else []

    scripts_raw = inference.get("scripts")
    inferred_scripts: list[str] = scripts_raw if isinstance(scripts_raw, list) else []

    sample = choose_language_sample(inferred_languages, inferred_scripts)
    if not isinstance(sample, str) or not sample.strip():
        return None, "no_language_sample"

    filtered, glyphs = _specimen_filter_text(sample, cps)
    if glyphs == 0:
        return None, "language_sample_no_supported_glyphs"
    if glyphs < MIN_SAMPLE_GLYPHS:
        return None, "language_sample_too_short"

    return filtered, "language"


def _specimen_upgrade_low_information_sample(
    font: FontRef,
    filtered: str,
    glyph_count: int,
    cps: set[int],
    *,
    current_strategy: str | None = None,
) -> tuple[str, int, str | None]:
    """
    Replace a low-information specimen with a stronger language sample.

    Parameters
    ----------
    font : FontRef
        Inventory entry whose inference metadata is consulted.
    filtered : str
        Current accepted specimen candidate.
    glyph_count : int
        Accepted base-glyph count for ``filtered``.
    cps : set[int]
        Supported Unicode codepoints for the font.
    current_strategy : str | None, optional
        Strategy that produced the currently accepted specimen.

    Returns
    -------
    tuple[str, int, str | None]
        Possibly upgraded ``(specimen_text, glyph_count, strategy)``
        triple. The strategy is ``None`` when no replacement is used.
    """
    if glyph_count >= MIN_SAMPLE_GLYPHS:
        return filtered, glyph_count, None

    replacement, strategy = _specimen_from_language(font, cps)
    if replacement is None:
        if cps and current_strategy != "cmap":
            cmap_replacement, cmap_strategy = _specimen_from_cmap(font, cps)
            cmap_filtered, cmap_glyphs = _specimen_filter_text(cmap_replacement, cps)
            if cmap_glyphs > glyph_count and cmap_filtered.strip():
                return cmap_filtered, cmap_glyphs, cmap_strategy
        return filtered, glyph_count, None

    return replacement, len(replacement), strategy


def _resolve_initial_specimen(
    font: FontRef,
    coverage: JSONDict,
    cps: set[int],
) -> tuple[str | None, str | None, str | None, int]:
    """
    Resolve the initial specimen candidate from the fallback chain.

    Parameters
    ----------
    font : FontRef
        Inventory entry being enriched.
    coverage : JSONDict
        Coverage block used for script-based specimen resolution.
    cps : set[int]
        Supported Unicode codepoints for the font.

    Returns
    -------
    tuple[str | None, str | None, str | None, int]
        ``(specimen_text, strategy, rejection_reason, fallback_depth)``
        after evaluating the deterministic fallback chain.
    """
    specimen_text, strategy = _specimen_from_internal(font, cps)
    rejection: str | None = None
    fallback_depth = 0

    if specimen_text is None:
        rejection = strategy
        strategy = None
        fallback_depth = 1

    if specimen_text is None:
        specimen_text, strategy = _specimen_from_script(coverage, cps)
        if specimen_text is not None:
            fallback_depth = 2

    if specimen_text is None:
        specimen_text, strategy = _specimen_from_language(font, cps)
        if specimen_text is not None:
            rejection = "fallback_to_language"
            fallback_depth = 2

    if specimen_text is None and cps:
        specimen_text, strategy = _specimen_from_private_use(font, cps)
        if specimen_text is not None:
            rejection = "fallback_to_private_use"
            fallback_depth = 3

    if specimen_text is None and cps:
        specimen_text, strategy = _specimen_from_cmap(font, cps)
        rejection = "fallback_to_cmap"
        if specimen_text is not None:
            fallback_depth = 4

    return specimen_text, strategy, rejection, fallback_depth


def _specimen_generate_for_font(
    font: FontRef,
    coverage: JSONDict,
    font_path: str | None,
) -> None:
    """
    Deterministic specimen generator with ordered specimen fallbacks.

    Parameters
    ----------
    font : dict[str, Any]
        Inventory font entry updated in place with specimen fields.
    coverage : dict[str, Any]
        Coverage block used to derive script-based fallback specimens.
    font_path : str | None
        Filesystem path to the font binary, used for cmap extraction.

    Returns
    -------
    None

    Notes
    -----
    Writes the schema v1.5 typography fields:
    - ``typography.specimen_text``
    - ``typography.specimen_strategy``
    - ``typography.specimen_glyph_count``
    - ``typography.specimen_rejection_reason``

    Fallback order:
    1. internal sample text
    2. script-derived curated sample
    3. language-derived sample
    4. private-use cmap sample when PUA coverage is significant
    5. cmap-derived fallback

    The function always leaves a visible specimen in the font record,
    even when curated and cmap-derived samples are both unusable.
    """
    cps = _specimen_collect_cmap(font_path, None)

    specimen_text, strategy, rejection, fallback_depth = _resolve_initial_specimen(
        font, coverage, cps
    )

    if not specimen_text:
        specimen_text = " "
        strategy = "cmap"
        rejection = rejection or "no_printable_glyphs"

    filtered, g = (
        _specimen_filter_text(
            specimen_text,
            cps,
            allow_private_use=(strategy == "pua"),
        )
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

    upgraded_filtered, upgraded_g, upgraded_strategy = (
        _specimen_upgrade_low_information_sample(
            font,
            filtered,
            g,
            cps,
            current_strategy=strategy,
        )
    )
    if upgraded_strategy is not None:
        filtered = upgraded_filtered
        g = upgraded_g
        strategy = upgraded_strategy
        rejection = "specimen_too_short"

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

    set_specimen_fields(
        font,
        specimen_text=filtered,
        specimen_strategy=_normalize_top_level_specimen_strategy(strategy) or "cmap",
        specimen_glyph_count=int(g),
        specimen_rejection_reason=rejection,
    )

    log_trace_cat(
        log,
        "specimen",
        "specimen generated",
        extra={
            "strategy": (font.get("typography") or {}).get("specimen_strategy"),
            "glyph_count": (font.get("typography") or {}).get("specimen_glyph_count"),
            "fallback_depth": fallback_depth,
            "rejection": (font.get("typography") or {}).get(
                "specimen_rejection_reason"
            ),
        },
    )
