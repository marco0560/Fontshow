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

    Returns
    -------
    None
    """
    assert document._normalize_path_for_latex(r"C:\Fonts\Alpha.ttf") == (
        "C:/Fonts/",
        "Alpha.ttf",
    )
    assert document._normalize_path_for_latex("Alpha.ttf") == ("./", "Alpha.ttf")


def test_render_font_entry_returns_empty_for_unsupported_extension():
    """
    Ensure non-font paths do not render specimen blocks.

    Returns
    -------
    None
    """
    render, options = document._render_font_entry(
        font={"path": "/tmp/alpha.txt"},
        safe_specimen="sample",
        script0_iso=ScriptISO("LATN"),
        fullpath="/tmp/alpha.txt",
    )

    assert render == ""
    assert options == ""


def test_render_font_entry_falls_back_to_family_name_when_path_missing(monkeypatch):
    """
    Ensure missing-path entries use safe family-based font loading.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LaTeX helper functions.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "Renderer=1,")
    monkeypatch.setattr(document, "_get_render_policy", lambda _script: ("", ""))

    render, options = document._render_font_entry(
        font={
            "family": "Noto Sans Kannada",
            "full_name": "Noto Sans Kannada SemiCondensed ExtraBold",
            "path": "",
        },
        safe_specimen="abc",
        script0_iso=ScriptISO("LATN"),
        fullpath="",
    )

    assert "\\fontspec[" in render
    assert "UprightFont=*" in render
    assert "Path=\\detokenize{" not in render
    assert "{\\detokenize{Noto Sans Kannada}}" in render
    assert "SemiCondensed ExtraBold" not in render
    assert options == "Renderer=1,Family=Noto Sans Kannada,UprightFont=*"


def test_render_font_entry_uses_non_latin_template_when_language_is_available(
    monkeypatch,
):
    """
    Ensure non-Latin scripts with a language use the compact inline form.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LaTeX helper functions.

    Returns
    -------
    None
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
    assert "\\renewfontfamily\\arabicfont" not in render
    assert "\\foreignlanguage{arabic}" in render
    assert "\\fontspec[" in render
    assert render.count("\\emergencystretch=2em") == 1
    assert "Extension=.ttf" not in render
    assert "{\\detokenize{arabic.ttf}}" in render
    assert options == "Renderer=1,Path=/tmp/,File=arabic.ttf,Script=Arabic"


def test_render_font_entry_falls_back_to_fontspec_without_language(monkeypatch):
    """
    Ensure script-tagged entries without a language use the compact inline form.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LaTeX helper functions.

    Returns
    -------
    None
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

    assert "\\newfontfamily\\fontshowentryfont" not in render
    assert "\\fontspec[" in render
    assert "Extension=.otf" not in render
    assert "Path=\\detokenize{/tmp/}" in render
    assert "{\\detokenize{foo.otf}}" in render
    assert options == "Path=/tmp/,File=foo.otf,Script=Foo"


def test_render_font_entry_uses_inline_fontspec_for_gujarati_without_language(
    monkeypatch,
):
    """
    Ensure Gujarati script-only entries follow the generic compact form.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LaTeX helper functions.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "Renderer=1,")
    monkeypatch.setattr(
        document, "_get_render_policy", lambda _script: ("", "Script=Gujarati")
    )

    render, options = document._render_font_entry(
        font={"path": "/tmp/Lohit-Gujarati.ttf"},
        safe_specimen="abc",
        script0_iso=ScriptISO("GUJR"),
        fullpath="/tmp/Lohit-Gujarati.ttf",
    )

    assert "\\fontspec[" in render
    assert "\\newfontfamily\\fontshowentryfont" not in render
    assert "Script=Gujarati" in render
    assert "{\\detokenize{Lohit-Gujarati.ttf}}" in render
    assert options == "Renderer=1,Path=/tmp/,File=Lohit-Gujarati.ttf,Script=Gujarati"


def test_render_font_entry_uses_inline_fontspec_for_bengali_with_language(
    monkeypatch,
):
    """
    Ensure Bengali entries follow the generic compact language form.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LaTeX helper functions.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "Renderer=1,")
    monkeypatch.setattr(
        document, "_get_render_policy", lambda _script: ("bengali", "Script=Bengali")
    )

    render, options = document._render_font_entry(
        font={
            "family": "Lohit Bengali",
            "path": "/tmp/Lohit-Bengali.ttf",
            "script": "beng",
        },
        safe_specimen="abc",
        script0_iso=ScriptISO("BENG"),
        fullpath="/tmp/Lohit-Bengali.ttf",
    )

    assert "\\fontspec[" in render
    assert "\\renewfontfamily\\bengalifont" not in render
    assert "\\foreignlanguage{bengali}" in render
    assert "Script=Bengali" in render
    assert "Path=\\detokenize{/tmp/}" in render
    assert "{\\detokenize{Lohit-Bengali.ttf}}" in render
    assert options == "Renderer=1,Path=/tmp/,File=Lohit-Bengali.ttf,Script=Bengali"


def test_render_font_entry_uses_path_and_file_for_unknown_scripts(monkeypatch):
    """
    Ensure unknown scripts keep the simpler ``Path`` plus filename form.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LaTeX helper functions.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "Renderer=1,")
    monkeypatch.setattr(document, "_get_render_policy", lambda _script: ("", ""))

    render, options = document._render_font_entry(
        font={"path": "/tmp/unknown.ttf"},
        safe_specimen="abc",
        script0_iso=ScriptISO(""),
        fullpath="/tmp/unknown.ttf",
    )

    assert "\\fontspec[" in render
    assert "Path=\\detokenize{/tmp/}" in render
    assert "{\\detokenize{unknown.ttf}}" in render
    assert "{\\detokenize{/tmp/unknown.ttf}}" not in render
    assert options == "Renderer=1,Path=/tmp/,File=unknown.ttf"


def test_generate_document_uses_variant_specific_specimens(monkeypatch, tmp_path):
    """
    Ensure family variants render using their own specimen metadata.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace helper functions with deterministic stubs.
    tmp_path : pathlib.Path
        Temporary directory used to create placeholder font files.

    Returns
    -------
    None
    """
    regular_path = tmp_path / "FreeSans.ttf"
    bold_path = tmp_path / "FreeSansBold.ttf"
    regular_path.write_text("", encoding="utf-8")
    bold_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE")
    monkeypatch.setattr(document, "EXCLUDED_FONTS", set())
    monkeypatch.setattr(document, "log_info", lambda _msg: None)
    monkeypatch.setattr(document, "log_warn", lambda _msg: None)
    monkeypatch.setattr(document, "as_font_desc_list", lambda fonts: list(fonts))
    monkeypatch.setattr(
        document, "_collect_polyglossia_other_languages", lambda _fonts: ""
    )
    monkeypatch.setattr(document, "_collect_polyglossia_font_setup", lambda _fonts: "")
    monkeypatch.setattr(document, "_latex_debug_literal", lambda value: value)
    monkeypatch.setattr(document, "_format_script_display", lambda value: value.upper())
    monkeypatch.setattr(
        document, "_format_language_display", lambda value: value.upper()
    )
    monkeypatch.setattr(document, "_strip_ascii_control_chars", lambda value: value)
    monkeypatch.setattr(document, "escape_latex", lambda value: value)
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "")
    monkeypatch.setattr(document, "primary_script", lambda font: font.get("script"))

    def render_stub(font, safe_specimen, script0_iso, fullpath):
        """
        Return a deterministic marker for rendered variants.

        Parameters
        ----------
        font : dict[str, object]
            Font descriptor forwarded by the document generator.
        safe_specimen : str
            Preformatted specimen string selected for this render.
        script0_iso : ScriptISO
            Script code chosen for rendering.
        fullpath : str
            Absolute font path.

        Returns
        -------
        tuple[str, str]
            Fake LaTeX render block and plain option string.
        """
        _ = script0_iso, fullpath
        marker = str(font.get("path", ""))
        return f"<{marker}|{safe_specimen}>", f"Path={marker}"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    fonts = [
        {
            "family": "FreeSans",
            "path": str(regular_path),
            "style": "Regular",
            "script": "cans",
            "specimen_text": "᐀ᐁ",
            "inference": {"scripts": ["cans"], "languages": ["cr"]},
        },
        {
            "family": "FreeSans",
            "path": str(bold_path),
            "style": "Bold",
            "script": "latn",
            "specimen_text": "The quick brown fox",
            "inference": {"scripts": ["latn"], "languages": ["en"]},
        },
    ]

    latex = document.generate_latex(fonts)

    assert f"<{regular_path}|᐀ᐁ>" in latex
    assert f"<{bold_path}|The quick brown fox>" in latex


def test_format_specimen_for_latex_chunks_non_space_runs_every_five_characters():
    """
    Ensure long runs without spaces receive explicit break hints every five characters.

    Returns
    -------
    None
    """
    specimen = "A" * 40

    formatted = document._format_specimen_for_latex(specimen, ScriptISO("LATN"))

    assert (
        formatted
        == "AAAAA\\allowbreak{}AAAAA\\allowbreak{}AAAAA\\allowbreak{}AAAAA\\allowbreak{}AAAAA\\allowbreak{}AAAAA\\allowbreak{}AAAAA\\allowbreak{}AAAAA"
    )


def test_format_specimen_for_latex_adds_break_hints_for_cjk_runs():
    """
    Ensure long CJK runs also receive explicit break hints.

    Returns
    -------
    None
    """
    specimen = "漢" * 40

    formatted = document._format_specimen_for_latex(specimen, ScriptISO("HANI"))

    assert (
        formatted
        == "漢漢漢漢漢\\allowbreak{}漢漢漢漢漢\\allowbreak{}漢漢漢漢漢\\allowbreak{}漢漢漢漢漢\\allowbreak{}漢漢漢漢漢\\allowbreak{}漢漢漢漢漢\\allowbreak{}漢漢漢漢漢\\allowbreak{}漢漢漢漢漢"
    )
    assert formatted.count("\\allowbreak{}") == 7


def test_generate_latex_warns_on_missing_marker_and_deduplicates_families(monkeypatch):
    """
    Ensure generation groups by family and emits one specimen block per file.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and logging.

    Returns
    -------
    None
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
    monkeypatch.setattr(
        document, "_format_language_display", lambda value: value.upper()
    )
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
    assert "FILE  : alpha.ttf [OK]" in latex
    assert "FILE  : ignored.ttf [OK]" in latex
    assert "LANGDEF" not in latex
    assert "FONTDEF" not in latex
    assert "LANGS : EN" in latex
    assert "OPTS  : Path=/tmp/, File=alpha.ttf" in latex
    assert "}\\newline" not in latex
    assert "\\item Beta --- " in latex.split("\\item Alpha --- ", maxsplit=1)[1]
    assert "\n\n\\item Beta --- " in latex
    assert "\\LogWorking{Alpha / alpha.ttf}" in latex
    assert "\\LogWorking{Alpha / ignored.ttf}" in latex
    assert "\\LogBroken{Beta / beta.bin}" in latex
    assert latex.count("\\allowbreak{}") == 7
    assert "FILE  : beta.bin" in latex
    assert "\\LogBroken{Beta / beta.bin}[MISSING]" in latex
    assert "\\LogExcluded{Zed}" in latex
    assert latex.endswith("\nEND:2:DONE")


def test_generate_latex_skips_excluded_families_from_catalog(monkeypatch):
    """
    Ensure excluded families do not render catalog entries.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and logging.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE")
    monkeypatch.setattr(document, "EXCLUDED_FONTS", {"Skip Me"})
    monkeypatch.setattr(document, "log_info", lambda _message: None)
    monkeypatch.setattr(document, "log_warn", lambda _message: None)
    monkeypatch.setattr(document, "as_font_desc_list", lambda fonts: list(fonts))
    monkeypatch.setattr(
        document, "_collect_polyglossia_other_languages", lambda fonts: ""
    )
    monkeypatch.setattr(document, "_collect_polyglossia_font_setup", lambda fonts: "")
    monkeypatch.setattr(document, "_strip_ascii_control_chars", lambda value: value)
    monkeypatch.setattr(document, "escape_latex", lambda value: value)
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(
        document, "_format_language_display", lambda value: value.upper()
    )
    monkeypatch.setattr(document, "_format_script_display", lambda value: value.upper())
    monkeypatch.setattr(document, "primary_script", lambda font: font.get("script"))
    monkeypatch.setattr(
        document,
        "_render_font_entry",
        lambda **kwargs: ("<rendered>", "Path=/tmp/,File=alpha.ttf"),
    )

    latex = document.generate_latex(
        [
            {
                "family": "Skip Me",
                "path": "/tmp/skip.ttf",
                "specimen_text": "ignored",
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            },
            {
                "family": "Keep Me",
                "path": "/tmp/keep.ttf",
                "specimen_text": "sample",
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            },
        ]
    )

    assert "\\item Skip Me --- " not in latex
    assert "\\item Keep Me --- " in latex
    assert "\\LogExcluded{Skip Me}" in latex
    assert latex.endswith("\nEND:1:DONE")


def test_generate_latex_marks_family_fallback_entries_as_working(monkeypatch):
    """
    Ensure family-only entries render as working fallback specimens.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and logging.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE")
    monkeypatch.setattr(document, "EXCLUDED_FONTS", set())
    monkeypatch.setattr(document, "log_info", lambda _message: None)
    monkeypatch.setattr(document, "log_warn", lambda _message: None)
    monkeypatch.setattr(document, "as_font_desc_list", lambda fonts: list(fonts))
    monkeypatch.setattr(
        document, "_collect_polyglossia_other_languages", lambda _fonts: ""
    )
    monkeypatch.setattr(document, "_collect_polyglossia_font_setup", lambda _fonts: "")
    monkeypatch.setattr(document, "_strip_ascii_control_chars", lambda value: value)
    monkeypatch.setattr(document, "escape_latex", lambda value: value)
    monkeypatch.setattr(document, "_latex_detokenize_safe", lambda value: value)
    monkeypatch.setattr(document, "_latex_debug_literal", lambda value: value)
    monkeypatch.setattr(document, "_renderer_option_prefix", lambda: "")
    monkeypatch.setattr(document, "_get_render_policy", lambda _script: ("", ""))
    monkeypatch.setattr(
        document, "_format_language_display", lambda value: value.upper()
    )
    monkeypatch.setattr(document, "_format_script_display", lambda value: value.upper())
    monkeypatch.setattr(document, "primary_script", lambda font: font.get("script"))

    latex = document.generate_latex(
        [
            {
                "family": "ETbb",
                "path": "",
                "specimen_text": "Sample",
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            }
        ]
    )

    assert "FILE  : ETbb [OK]" in latex
    assert "\\LogWorking{ETbb / ETbb}" in latex
    assert "\\LogBroken{ETbb / ETbb}[MISSING]" not in latex
    assert "OPTS  : Family=ETbb, UprightFont=*" in latex
