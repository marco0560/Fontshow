"""
Exercise script analysis branch-heavy logic.
"""

from __future__ import annotations

from fontshow.inventory.script_analysis import (
    infer_scripts,
    script_coverage_from_unicode_blocks,
)


def test_script_coverage_from_unicode_blocks_ignores_unknown_blocks_and_zero_totals():
    """
    Ensure empty totals and unknown blocks produce safe output.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert (
        script_coverage_from_unicode_blocks({"Unknown": 10}, {"latn": [(0, 1)]}, 0)
        == {}
    )
    assert (
        script_coverage_from_unicode_blocks({"Unknown": 10}, {"latn": [(0, 1)]}, 10)
        == {}
    )


def test_infer_scripts_uses_charset_scores_as_tiebreaker() -> None:
    """
    Ensure charset-derived script scores can break canonical score ties.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Greek and Coptic": 20,
            "Latin Extended-A": 20,
        },
        "script_coverage_from_charset": {
            "GREK": 0.9,
            "LATN": 0.1,
        },
    }

    assert infer_scripts(coverage) == ["grek", "latn"]


def test_infer_scripts_uses_charset_scores_as_fallback() -> None:
    """
    Ensure charset-derived script scores act as fallback evidence.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    coverage = {
        "script_coverage_from_charset": {
            "CYRL": 0.8,
            "LATN": 0.2,
        }
    }

    assert infer_scripts(coverage) == ["cyrl", "latn"]


def test_infer_scripts_keeps_canonical_blocks_authoritative() -> None:
    """
    Ensure charset-derived scores do not override stronger canonical evidence.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Arabic": 40,
        },
        "script_coverage_from_charset": {
            "HEBR": 1.0,
            "ARAB": 0.1,
        },
    }

    assert infer_scripts(coverage) == ["arab"]


def test_infer_scripts_cjk_and_threshold_branches():
    """
    Ensure CJK disambiguation and threshold branches behave deterministically.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts(
        {"unicode_blocks": {"CJK Unified Ideographs Extension A": 100, "Hiragana": 30}},
        level="medium",
    ) == ["jpan"]
    assert infer_scripts(
        {"unicode_blocks": {"Hangul Syllables": 50, "CJK Unified Ideographs": 100}},
        level="medium",
    ) == ["hang"]
    assert infer_scripts(
        {"unicode_blocks": {"Latin Extended-A": 4}}, level="medium"
    ) == ["latn"]
    assert infer_scripts({"unicode_blocks": {"Buginese": 2}}, level="aggressive") == [
        "bugi"
    ]


def test_infer_scripts_uses_unicode_max_fallbacks():
    """
    Ensure unicode.max fallback ranges map to the documented scripts.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x024F}}) == ["latn"]
    assert infer_scripts({"unicode": {"max": 0x05FF}}) == ["hebr"]
    assert infer_scripts({"unicode": {"max": 0x4E00}}) == ["hani"]


def test_infer_scripts_prefers_dedicated_blocks_over_broader_neighbors():
    """
    Ensure dedicated script blocks win over legacy neighboring scripts.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts(
        {"unicode_blocks": {"Coptic": 15, "Greek and Coptic": 10}}
    ) == [
        "copt",
        "grek",
    ]
    assert infer_scripts({"unicode_blocks": {"Hanifi Rohingya": 12, "Arabic": 9}}) == [
        "rohg",
        "arab",
    ]
    assert infer_scripts({"unicode_blocks": {"Kaithi": 10, "Devanagari": 8}}) == [
        "kthi",
        "deva",
    ]
