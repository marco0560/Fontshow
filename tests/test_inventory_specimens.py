"""
Exercise specimen generation helper branches.

Responsibilities
----------------
- Cover internal, script, cmap, and semantic-validation fallbacks.
- Verify visible-output hardening and rejection reasons remain deterministic.
"""

from __future__ import annotations

from fontshow.inventory import specimens


def test_specimen_from_internal_reports_rejection_reasons():
    """
    Ensure internal samples report absent, unsupported, short, and success states.

    Parameters
    ----------
    None

    Returns
    -------
    None
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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace script ontology entries.

    Returns
    -------
    None
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


def test_specimen_from_script_keeps_substantial_sample_for_large_cmap(monkeypatch):
    """
    Ensure large cmaps do not force curated script samples to fall back spuriously.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace script ontology entries.

    Returns
    -------
    None
    """
    hangul_specimen = "가나다라마바사아자차카타파하거너더러머버서어저처커터퍼허"
    monkeypatch.setattr(
        specimens,
        "SCRIPT_INFO",
        {
            "HANG": {"specimen": hangul_specimen},
        },
    )

    cps = {ord(ch) for ch in hangul_specimen}
    cps.update(range(0xAC00, 0xAC00 + 12000))

    result = specimens._specimen_from_script({"scripts": ["hang"]}, cps)

    assert result == (hangul_specimen, "script")


def test_specimen_from_cmap_returns_fallback_without_warning_record():
    """
    Ensure cmap fallback uses preference ordering without adding a warning record.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    font: dict[str, object] = {}
    specimen, strategy = specimens._specimen_from_cmap(
        font,
        {ord("B"), ord("1"), ord("!"), ord("A")},
    )

    assert specimen == "AB1!"
    assert strategy == "cmap"
    assert "warnings" not in font


def test_specimen_from_private_use_returns_visible_pua_sample():
    """
    Ensure substantial private-use coverage produces a PUA specimen strip.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    cps = {0xE000 + index for index in range(specimens.MIN_SAMPLE_GLYPHS + 4)}
    font = {
        "coverage": {
            "unicode_blocks": {
                "Private Use Area": specimens.MIN_SAMPLE_GLYPHS + 4,
            }
        }
    }

    specimen, strategy = specimens._specimen_from_private_use(font, cps)

    assert isinstance(specimen, str)
    assert len(specimen) == specimens.MIN_SAMPLE_GLYPHS + 4
    assert strategy == "pua"
    assert all(0xE000 <= ord(ch) <= 0xF8FF for ch in specimen)


def test_specimen_filter_text_preserves_separator_spaces_without_counting_them():
    """
    Ensure supported whitespace is preserved only between accepted glyphs.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    filtered, glyphs = specimens._specimen_filter_text(
        "AB CD",
        {ord("A"), ord("B"), ord("C"), ord("D"), ord(" ")},
    )

    assert filtered == "AB CD"
    assert glyphs == 4


def test_specimen_filter_text_drops_whitespace_only_support():
    """
    Ensure whitespace-only cmap support does not count as a specimen.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    filtered, glyphs = specimens._specimen_filter_text(
        "The quick brown fox",
        {ord(" ")},
    )

    assert filtered == ""
    assert glyphs == 0


def test_specimen_apply_semantic_validation_uses_language_sample_then_ascii(
    monkeypatch,
):
    """
    Ensure semantic validation first tries language-aware replacement, then ASCII.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace language-sample lookup.

    Returns
    -------
    None
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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace specimen-generation helpers and tracing.

    Returns
    -------
    None
    """
    font = {"path": "/tmp/font.ttf", "sample_text": "   ", "inference": {}}
    coverage: dict[str, object] = {"scripts": []}

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

    typography = font["typography"]
    assert typography["specimen_text"] == "XYZ"
    assert typography["specimen_strategy"] == "validated-language-sample"
    assert typography["specimen_rejection_reason"] == "specimen_not_in_cmap"
    assert typography["specimen_glyph_count"] == 3
    assert trace_calls == [
        {
            "strategy": "validated-language-sample",
            "glyph_count": 3,
            "fallback_depth": 4,
            "rejection": "specimen_not_in_cmap",
        }
    ]


def test_specimen_generate_for_font_keeps_private_use_specimen(monkeypatch):
    """
    Ensure PUA fallback survives final filtering when coverage is substantial.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace cmap extraction and tracing.

    Returns
    -------
    None
    """
    pua_chars = "".join(
        chr(0xE000 + index) for index in range(specimens.MIN_SAMPLE_GLYPHS)
    )
    font = {
        "path": "/tmp/font.ttf",
        "coverage": {
            "unicode_blocks": {"Private Use Area": specimens.MIN_SAMPLE_GLYPHS}
        },
        "inference": {},
    }
    coverage = font["coverage"]

    monkeypatch.setattr(
        specimens,
        "_specimen_collect_cmap",
        lambda path, idx: {ord(ch) for ch in pua_chars},
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_internal",
        lambda font, cps: (None, "no_internal_sample"),
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_script",
        lambda coverage, cps: (None, "no_scripts"),
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_language",
        lambda font, cps: (None, "no_language_sample"),
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_apply_semantic_validation",
        lambda font, filtered, g, cps: (filtered, g, None),
    )
    monkeypatch.setattr(specimens, "log_trace_cat", lambda *args, **kwargs: None)

    specimens._specimen_generate_for_font(font, coverage, "/tmp/font.ttf")

    assert font["typography"]["specimen_text"] == pua_chars
    assert font["typography"]["specimen_strategy"] == "pua"
    assert font["typography"]["specimen_glyph_count"] == specimens.MIN_SAMPLE_GLYPHS


def test_specimen_upgrade_low_information_sample_falls_back_to_cmap(monkeypatch):
    """
    Ensure weak accepted samples can be upgraded from the font cmap.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace language and cmap fallback helpers.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        specimens,
        "_specimen_from_language",
        lambda _font, _cps: (None, "no_language_sample"),
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_cmap",
        lambda _font, _cps: ("ABCDEFGH", "cmap"),
    )

    upgraded = specimens._specimen_upgrade_low_information_sample(
        {},
        "A",
        1,
        {ord(ch) for ch in "ABCDEFGH"},
        current_strategy="script",
    )

    assert upgraded == ("ABCDEFGH", 8, "cmap")


def test_specimen_generate_for_font_uses_language_sample_before_cmap(monkeypatch):
    """
    Ensure language-aware samples are preferred before falling back to cmap.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace specimen-generation helpers and tracing.

    Returns
    -------
    None
    """
    font = {
        "path": "/tmp/font.ttf",
        "sample_text": "A",
        "inference": {"languages": ["en"], "scripts": ["latn"]},
    }
    coverage: dict[str, object] = {"scripts": ["latn"]}

    monkeypatch.setattr(
        specimens,
        "_specimen_collect_cmap",
        lambda path, idx: {ord(ch) for ch in "Hello there General Kenobi"},
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_internal",
        lambda font, cps: (None, "internal_sample_too_short"),
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_script",
        lambda coverage, cps: (None, "script_sample_too_sparse"),
    )
    monkeypatch.setattr(
        specimens,
        "choose_language_sample",
        lambda langs, scripts: "Hello there General Kenobi",
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_cmap",
        lambda font, cps: ("SHOULD NOT HAPPEN", "cmap"),
    )
    monkeypatch.setattr(
        specimens,
        "log_trace_cat",
        lambda *_args, **_kwargs: None,
    )

    specimens._specimen_generate_for_font(font, coverage, "/tmp/font.ttf")

    typography = font["typography"]
    assert typography["specimen_text"] == "Hello there General Kenobi"
    assert typography["specimen_strategy"] == "language"
    assert typography["specimen_glyph_count"] == 23
    assert typography["specimen_rejection_reason"] == "fallback_to_language"


def test_specimen_generate_for_font_upgrades_overshort_visible_sample(monkeypatch):
    """
    Ensure short visible samples are upgraded with a stronger language sample.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace specimen-generation helpers and tracing.

    Returns
    -------
    None
    """
    font = {
        "path": "/tmp/font.ttf",
        "sample_text": "T",
        "inference": {"languages": ["en"], "scripts": ["latn"]},
    }
    coverage: dict[str, object] = {"scripts": ["latn"]}

    monkeypatch.setattr(
        specimens,
        "_specimen_collect_cmap",
        lambda path, idx: {
            ord(ch) for ch in "The quick brown fox jumps over the lazy dog"
        },
    )
    monkeypatch.setattr(
        specimens,
        "_specimen_from_internal",
        lambda font, cps: ("T", "internal"),
    )
    monkeypatch.setattr(
        specimens,
        "choose_language_sample",
        lambda langs, scripts: "The quick brown fox jumps over the lazy dog",
    )
    monkeypatch.setattr(
        specimens,
        "log_trace_cat",
        lambda *_args, **_kwargs: None,
    )

    specimens._specimen_generate_for_font(font, coverage, "/tmp/font.ttf")

    typography = font["typography"]
    assert typography["specimen_text"] == "The quick brown fox jumps over the lazy dog"
    assert typography["specimen_strategy"] == "language"
    assert typography["specimen_rejection_reason"] == "specimen_too_short"


def test_specimen_collect_cmap_returns_empty_for_malformed_subtables(monkeypatch):
    """
    Ensure malformed cmap subtables do not escape as attribute errors.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace ``TTFont`` with a malformed test double.

    Returns
    -------
    None
    """

    class FakeTTFont(dict):
        def __init__(self, *_args, **_kwargs) -> None:
            """
            Build a minimal cmap container with malformed subtables.

            Returns
            -------
            None
            """
            super().__init__(cmap=type("Cmap", (), {"tables": [object()]})())

    monkeypatch.setattr(specimens, "TTFont", FakeTTFont)

    assert specimens._specimen_collect_cmap("/tmp/font.ttf", None) == set()
