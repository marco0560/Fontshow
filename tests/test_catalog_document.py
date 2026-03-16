"""
Exercise catalog document rendering helpers.

Responsibilities
----------------
- Cover path normalization and render-branch selection.
- Verify document generation deduplicates families and handles missing markers.
- Keep rendering deterministic via helper monkeypatching.
"""

from __future__ import annotations

from fontshow.catalog import document
from fontshow.core.types import ScriptISO


def test_normalize_path_for_latex_handles_windows_and_bare_filenames():
    """
    Ensure path normalization produces forward slashes and a default directory.
    """
    assert document._normalize_path_for_latex(r"C:\Fonts\Alpha.ttf") == (
        "C:/Fonts/",
        "Alpha.ttf",
    )
    assert document._normalize_path_for_latex("Alpha.ttf") == ("./", "Alpha.ttf")


def test_render_font_entry_returns_empty_for_unsupported_extension():
    """
    Ensure non-font paths do not render specimen blocks.
    """
    render, options = document._render_font_entry(
        font={"path": "/tmp/alpha.txt"},
        safe_specimen="sample",
        script0_iso=ScriptISO("LATN"),
        fullpath="/tmp/alpha.txt",
    )

    assert render == ""
    assert options == ""


def test_render_font_entry_uses_non_latin_template_when_language_is_available(
    monkeypatch,
):
    """
    Ensure non-Latin scripts with a language emit explicit per-entry font setup.
    """
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "Renderer=1,")
    monkeypatch.setattr(
        document, "_get_render_policy", lambda _script: ("arabic", "Script=Arabic")
    )

    render, options = document._render_font_entry(
        font={"path": "/tmp/arabic.ttf"},
        safe_specimen="abc",
        script0_iso=ScriptISO("ARAB"),
        fullpath="/tmp/arabic.ttf",
    )

    assert "\\TestNonLatin" not in render
    assert "\\ifcsname" not in render
    assert "\\newfontfamily" not in render
    assert "\\renewfontfamily\\arabicfont" in render
    assert "\\foreignlanguage{arabic}" in render
    assert "\\arabicfont" in render
    assert options == "Renderer=1,Path=/tmp/,File=arabic.ttf,Script=Arabic"


def test_render_font_entry_falls_back_to_fontspec_without_language(monkeypatch):
    """
    Ensure non-Latin scripts without a language still render through ``\\fontspec``.
    """
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "")
    monkeypatch.setattr(
        document, "_get_render_policy", lambda _script: ("", "Script=Foo")
    )

    render, options = document._render_font_entry(
        font={"path": "/tmp/foo.otf"},
        safe_specimen="abc",
        script0_iso=ScriptISO("FOOO"),
        fullpath="/tmp/foo.otf",
    )

    assert "\\fontspec[" in render
    assert "\\TestNonLatin" not in render
    assert options == "Path=/tmp/,File=foo.otf,Script=Foo"


def test_generate_latex_warns_on_missing_marker_and_deduplicates_families(monkeypatch):
    """
    Ensure generation deduplicates by family and warns when the language marker is absent.
    """
    infos: list[str] = []
    warnings: list[str] = []

    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE")
    monkeypatch.setattr(document, "EXCLUDED_FONTS", {"Zed"})
    monkeypatch.setattr(document, "log_info", infos.append)
    monkeypatch.setattr(document, "log_warn", warnings.append)
    monkeypatch.setattr(document, "as_font_desc_list", lambda fonts: list(fonts))
    monkeypatch.setattr(
        document, "_collect_polyglossia_other_languages", lambda fonts: "LANGDEF"
    )
    monkeypatch.setattr(
        document, "_collect_polyglossia_font_setup", lambda fonts: "FONTDEF"
    )
    monkeypatch.setattr(document, "_strip_ascii_control_chars", lambda value: value)
    monkeypatch.setattr(document, "escape_latex", lambda value: value)
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_format_script_display", lambda value: value.upper())
    monkeypatch.setattr(document, "primary_script", lambda font: font.get("script"))
    monkeypatch.setattr(
        document,
        "_render_font_entry",
        lambda **kwargs: (
            (f"<rendered>{kwargs['safe_specimen']}", "Path=/tmp/,File=alpha.ttf")
            if kwargs["font"]["path"].endswith(".ttf")
            else ("", "")
        ),
    )

    latex = document.generate_latex(
        [
            {
                "family": "Alpha",
                "path": "/tmp/alpha.ttf",
                "specimen_text": "A" * 40,
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            },
            {
                "family": "Alpha",
                "path": "/tmp/ignored.ttf",
                "specimen_text": "ignored",
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            },
            {
                "family": "Beta",
                "path": "/tmp/beta.bin",
                "specimen_text": "Beta sample",
                "inference": {"scripts": [], "languages": []},
                "script": "",
            },
        ]
    )

    assert infos == [
        "Generating LaTeX file for 2 fonts...",
        "  ... processed 2/2",
    ]
    assert warnings == ["LaTeX template marker %%FONTSHOW_OTHER_LANGUAGES%% not found"]
    assert latex.count("\\item Alpha --- ") == 1
    assert latex.count("\\item Beta --- ") == 1
    assert "LANGDEF" not in latex
    assert "FONTDEF" not in latex
    assert "\\allowbreak{}" in latex
    assert "{[MISSING]}" in latex
    assert "\\LogExcluded{Zed}" in latex
    assert latex.endswith("\nEND:2:DONE")
