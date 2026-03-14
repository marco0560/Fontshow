"""
Exercise specimen generation helper branches.

Responsibilities
----------------
- Cover internal, script, cmap, and semantic-validation fallbacks.
- Verify visible-output hardening and rejection reasons remain deterministic.
"""

from __future__ import annotations

from fontshow.core.types import Severity
from fontshow.inventory import specimens


def test_specimen_from_internal_reports_rejection_reasons():
    """
    Ensure internal samples report absent, unsupported, short, and success states.
    """
    cps = {ord(ch) for ch in "AlphaBetaGammaDeltaOmega"}

    assert specimens._specimen_from_internal({}, cps) == (None, "no_internal_sample")
    assert specimens._specimen_from_internal({"sample_text": "!!!"}, cps) == (
        None,
        "internal_sample_no_supported_glyphs",
    )
    assert specimens._specimen_from_internal({"sample_text": "Alpha"}, cps) == (
        None,
        "internal_sample_too_short",
    )

    text, strategy = specimens._specimen_from_internal(
        {"sample_text": "AlphaBetaGammaDeltaOmega"},
        cps,
    )
    assert strategy == "internal"
    assert text == "AlphaBetaGammaDeltaOmega"


def test_specimen_from_script_prefers_charset_dominance_and_rejects_sparse(monkeypatch):
    """
    Ensure script-derived samples use dominant script coverage and density guards.
    """
    monkeypatch.setattr(
        specimens,
        "SCRIPT_INFO",
        {
            "LATN": {"specimen": "AlphabetSoupAlphabetSoup"},
            "ARAB": {"specimen": "اب"},
        },
    )

    cps = {ord(ch) for ch in "AlphabetSoupAlphabetSoup"}
    result = specimens._specimen_from_script(
        {
            "scripts": ["arab", "latn"],
            "script_coverage_from_charset": {"arab": 1, "latn": 5},
        },
        cps,
    )
    assert result == ("AlphabetSoupAlphabetSoup", "script")

    sparse = specimens._specimen_from_script(
        {"scripts": ["arab"]},
        set(range(1000, 1300)),
    )
    assert sparse == (None, "script_sample_no_supported_glyphs")


def test_specimen_from_cmap_adds_structured_warning():
    """
    Ensure cmap fallback uses preference ordering and records a warning.
    """
    font: dict[str, object] = {}
    specimen, strategy = specimens._specimen_from_cmap(
        font,
        {ord("B"), ord("1"), ord("!"), ord("A")},
    )

    assert specimen == "AB1!"
    assert strategy == "cmap"
    assert font["warnings"] == [
        {
            "code": "specimen_cmap_fallback",
            "message": "Specimen generated via cmap fallback",
            "severity": Severity.INFO,
        }
    ]


def test_specimen_apply_semantic_validation_uses_language_sample_then_ascii(
    monkeypatch,
):
    """
    Ensure semantic validation first tries language-aware replacement, then ASCII.
    """
    cps = {ord("A"), ord("B"), ord("C")}
    font = {"inference": {"languages": ["en"], "scripts": ["latn"]}}

    monkeypatch.setattr(
        specimens, "choose_language_sample", lambda langs, scripts: "ABC"
    )
    assert specimens._specimen_apply_semantic_validation(font, "Ω", 1, cps) == (
        "ABC",
        3,
        "validated-language-sample",
    )

    monkeypatch.setattr(specimens, "choose_language_sample", lambda langs, scripts: "Ω")
    assert specimens._specimen_apply_semantic_validation(font, "Ω", 1, cps) == (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        52,
        "validated-fallback",
    )


def test_specimen_generate_for_font_uses_visible_replacement_and_semantic_fallback(
    monkeypatch,
):
    """
    Ensure generation never leaves whitespace-only output and records fallback reasons.
    """
    font = {"identity": {"ttc_index": 0}, "sample_text": "   ", "inference": {}}
    coverage = {"scripts": []}

    monkeypatch.setattr(
        specimens, "_specimen_collect_cmap", lambda path, idx: {ord("X")}
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_internal",
        lambda font, cps: (None, "no_internal_sample"),
    )
    monkeypatch.setattr(
        specimens, "_specimen_from_script", lambda coverage, cps: (None, "no_scripts")
    )
    monkeypatch.setattr(
        specimens, "_specimen_from_cmap", lambda font, cps: (" ", "cmap")
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_apply_semantic_validation",
        lambda font, filtered, g, cps: ("XYZ", 3, "validated-language-sample"),
    )
    trace_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        specimens,
        "log_trace_cat",
        lambda _log, _cat, _msg, extra: trace_calls.append(extra),
    )

    specimens._specimen_generate_for_font(font, coverage, "/tmp/font.ttf")

    assert font["specimen_text"] == "XYZ"
    assert font["specimen_strategy"] == "validated-language-sample"
    assert font["specimen_rejection_reason"] == "specimen_not_in_cmap"
    assert font["specimen_glyph_count"] == 3
    assert trace_calls == [
        {
            "strategy": "validated-language-sample",
            "glyph_count": 3,
            "fallback_depth": 3,
            "rejection": "specimen_not_in_cmap",
        }
    ]


def test_specimen_collect_cmap_returns_empty_for_malformed_subtables(monkeypatch):
    """
    Ensure malformed cmap subtables do not escape as attribute errors.
    """

    class FakeTTFont(dict):
        def __init__(self, *_args, **_kwargs) -> None:
            super().__init__(cmap=type("Cmap", (), {"tables": [object()]})())

    monkeypatch.setattr(specimens, "TTFont", FakeTTFont)

    assert specimens._specimen_collect_cmap("/tmp/font.ttf", None) == set()
