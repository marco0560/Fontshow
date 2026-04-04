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
from fontshow.catalog.loadability import LoadabilityExclusion
from fontshow.core.types import ScriptISO


def test_normalize_path_for_latex_handles_windows_and_bare_filenames():
    """
    Ensure path normalization produces forward slashes and a default directory.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert document._normalize_path_for_latex(r"C:\Fonts\Alpha.ttf") == (
        "C:/Fonts/",
        "Alpha.ttf",
    )
    assert document._normalize_path_for_latex("Alpha.ttf") == ("./", "Alpha.ttf")


def test_normalize_path_for_latex_preserves_wsl_mount_paths():
    """
    Ensure WSL-style mount-backed font paths remain absolute and normalized.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert document._normalize_path_for_latex("/mnt/c/Windows/Fonts/Arial.ttf") == (
        "/mnt/c/Windows/Fonts/",
        "Arial.ttf",
    )


def test_render_font_entry_returns_empty_for_unsupported_extension():
    """
    Ensure non-font paths do not render specimen blocks.

    Parameters
    ----------
    None

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
    assert "\\begingroup" in render
    assert "\\foreignlanguage{arabic}" not in render
    assert "\\fontspec[" in render
    assert render.count("\\emergencystretch=2em") == 1
    assert "Extension=.ttf" not in render
    assert "Path=\\detokenize{/tmp/}" in render
    assert "{\\detokenize{arabic.ttf}}" in render
    assert "\b" not in render
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
    assert "Path=\\detokenize{/tmp/}" in render
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
    assert "\\foreignlanguage{bengali}" not in render
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
    assert options == "Renderer=1,Path=/tmp/,File=unknown.ttf"


def test_ordered_script_candidates_prioritizes_latn_then_rtl(monkeypatch):
    """
    Ensure multi-specimen script ordering follows the renderer policy.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace ontology script metadata.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Latin"},
            ScriptISO("ARAB"): {"rtl": True, "specimen": "Arabic"},
            ScriptISO("KHMR"): {"rtl": False, "specimen": "Khmer"},
            ScriptISO("CYRL"): {"rtl": False, "specimen": "Cyrillic"},
            ScriptISO("GREK"): {"rtl": False, "specimen": "Greek"},
        },
    )
    monkeypatch.setattr(document, "primary_script", lambda font: font.get("script"))

    scripts = document._ordered_script_candidates(
        {
            "script": "khmr",
            "inference": {"scripts": ["arab", "latn", "cyrl", "grek"]},
            "coverage": {"scripts": ["khmr"]},
        }
    )

    assert scripts == [
        ScriptISO("LATN"),
        ScriptISO("ARAB"),
        ScriptISO("CYRL"),
        ScriptISO("GREK"),
    ]


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

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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
        "Generating LaTeX file for 2 families...",
        "  ... processed 2/2",
    ]
    assert warnings == ["LaTeX template marker %%FONTSHOW_OTHER_LANGUAGES%% not found"]
    assert latex.count("\\item Alpha") == 1
    assert "\n\n\\item Beta\n" not in latex
    assert "---" not in latex
    assert "alpha.ttf [OK]" in latex
    assert "ignored.ttf [OK]" in latex
    assert "LANGDEF" not in latex
    assert "FONTDEF" not in latex
    assert "LANGS : EN" not in latex
    assert "OPTS  : Path=/tmp/, File=alpha.ttf" not in latex
    assert "}\\newline" not in latex
    assert latex.count("\\allowbreak{}") == 7
    assert "[MISSING]" not in latex
    assert "\\section{Unrendered Variants}" in latex
    assert "\\item Beta | beta.bin | /tmp/beta.bin" in latex
    assert latex.endswith("\nEND:2:DONE")


def test_generate_latex_moves_duplicate_variants_to_appendix(monkeypatch):
    """
    Ensure duplicate variants are collapsed from the main body to an appendix.

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
    monkeypatch.setattr(
        document, "_format_language_display", lambda value: value.upper()
    )
    monkeypatch.setattr(document, "_format_script_display", lambda value: value.upper())
    monkeypatch.setattr(document, "primary_script", lambda font: font.get("script"))
    monkeypatch.setattr(
        document,
        "_render_font_entry",
        lambda **kwargs: (f"<{kwargs['font']['path']}>", "Path=/tmp/,File=alpha.ttf"),
    )

    latex = document.generate_latex(
        [
            {
                "family": "Alpha",
                "path": "/tmp/alpha-1.ttf",
                "full_name": "Alpha Regular",
                "subfamily": "Regular",
                "postscript_name": "Alpha-Regular",
                "version_string": "1.0",
                "specimen_text": "Alpha sample",
                "typography": {
                    "specimen_text": "Alpha sample",
                    "specimen_strategy": "language",
                    "specimen_glyph_count": 12,
                },
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            },
            {
                "family": "Alpha",
                "path": "/tmp/alpha-2.ttf",
                "full_name": "Alpha Regular",
                "subfamily": "Regular",
                "postscript_name": "Alpha-Regular",
                "version_string": "1.0",
                "specimen_text": "Alpha sample",
                "typography": {
                    "specimen_text": "Alpha sample",
                    "specimen_strategy": "language",
                    "specimen_glyph_count": 12,
                },
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            },
        ]
    )

    assert "alpha-1.ttf [OK]" in latex
    assert "alpha-2.ttf [OK]" not in latex
    assert "\\section{Duplicate Sources}" in latex
    assert "\\item Alpha | alpha-2.ttf | /tmp/alpha-2.ttf | alpha-1.ttf" in latex


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

    assert "\\item Skip Me" not in latex
    assert "\\item Keep Me" in latex
    assert latex.endswith("\nEND:1:DONE")


def test_generate_latex_with_report_includes_unloadable_font_section(monkeypatch):
    """
    Ensure structured unloadable-font reporting is rendered deterministically.

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

    latex = document.generate_latex_with_report(
        [
            {
                "family": "Keep Me",
                "path": "/tmp/keep.ttf",
                "specimen_text": "sample",
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "script": "latn",
            }
        ],
        excluded_fonts=[
            LoadabilityExclusion(
                identity="bad-2",
                family="Zulu",
                path="/tmp/zulu.ttf",
                detail="timeout",
            ),
            LoadabilityExclusion(
                identity="bad-1",
                family="Alpha",
                path="/tmp/alpha.ttf",
                detail="subset-empty",
            ),
        ],
    )

    assert "\\section{Unloadable Fonts}" in latex
    assert "Excluded fonts: 2\\\\" in latex
    assert "\\item Alpha | /tmp/alpha.ttf | subset-empty" in latex
    assert "\\item Zulu | /tmp/zulu.ttf | timeout" in latex
    assert latex.index("Alpha | /tmp/alpha.ttf | subset-empty") < latex.index(
        "Zulu | /tmp/zulu.ttf | timeout"
    )


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

    assert "ETbb [OK]" in latex
    assert "OPTS  : Family=ETbb, UprightFont=*" not in latex
    assert r"{\footnotesize\ttfamily LATN}" in latex
    assert "[MISSING]" not in latex


def test_filter_renderer_script_specimen_rejects_sparse_results(monkeypatch):
    """
    Ensure renderer-added specimens are skipped when too few glyphs survive.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace cmap and filtering helpers.

    Returns
    -------
    None
    """
    monkeypatch.setattr(document, "_specimen_collect_cmap", lambda _path, _idx: {1, 2})
    monkeypatch.setattr(
        document, "_specimen_filter_text", lambda _text, _cps: ("ab", 2)
    )
    monkeypatch.setattr(document, "MIN_SAMPLE_GLYPHS", 3)

    filtered = document._filter_renderer_script_specimen(
        {"path": "/tmp/font.ttf"},
        "Greek sample",
    )

    assert filtered == ""


def test_generate_document_skips_sparse_renderer_added_specimens(monkeypatch, tmp_path):
    """
    Ensure sparse renderer-added script specimens are omitted from output.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and filtering behavior.
    tmp_path : pathlib.Path
        Temporary directory used to create a placeholder font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "FreeSans.ttf"
    font_path.write_text("", encoding="utf-8")

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
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Latin sample"},
            ScriptISO("GREK"): {"rtl": False, "specimen": "Greek sample"},
            ScriptISO("KHMR"): {"rtl": False, "specimen": "Khmer sample"},
        },
    )
    monkeypatch.setattr(
        document,
        "_filter_renderer_script_specimen",
        lambda _font, specimen: "" if specimen == "Greek sample" else specimen,
    )

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
        """
        Return a deterministic marker for rendered script variants.

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
        _ = font, fullpath
        return f"<{script0_iso}|{safe_specimen}>", f"Path={script0_iso}"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    latex = document.generate_latex(
        [
            {
                "family": "FreeSans",
                "path": str(font_path),
                "style": "Regular",
                "script": "khmr",
                "specimen_text": "Original Khmer",
                "inference": {"scripts": ["khmr", "grek", "latn"], "languages": ["km"]},
                "coverage": {"scripts": ["khmr", "grek", "latn"]},
            },
        ]
    )

    assert r"{\footnotesize\ttfamily LATN}" in latex
    assert r"{\footnotesize\ttfamily KHMR}" in latex
    assert r"{\footnotesize\ttfamily GREK}" not in latex
    assert "<LATN|Latin sample>" in latex
    assert "<KHMR|Original Khmer>" in latex
    assert "<GREK|Greek sample>" not in latex


def test_generate_document_adds_multi_script_specimens_from_ontology(
    monkeypatch, tmp_path
):
    """
    Ensure renderer-only specimen expansion adds extra script blocks.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and ontology data.
    tmp_path : pathlib.Path
        Temporary directory used to create placeholder font files.

    Returns
    -------
    None
    """
    font_path = tmp_path / "FreeSans.ttf"
    font_path.write_text("", encoding="utf-8")

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
    monkeypatch.setattr(
        document, "_filter_renderer_script_specimen", lambda _font, specimen: specimen
    )
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Latin sample"},
            ScriptISO("ARAB"): {"rtl": True, "specimen": "Arabic sample"},
            ScriptISO("KHMR"): {"rtl": False, "specimen": "Khmer sample"},
        },
    )

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
        """
        Return a deterministic marker for rendered script variants.

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
        _ = font, fullpath
        return f"<{script0_iso}|{safe_specimen}>", f"Path={script0_iso}"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    latex = document.generate_latex(
        [
            {
                "family": "FreeSans",
                "path": str(font_path),
                "style": "Regular",
                "script": "khmr",
                "specimen_text": "Original Khmer",
                "inference": {"scripts": ["khmr", "arab", "latn"], "languages": ["km"]},
                "coverage": {"scripts": ["khmr", "arab", "latn"]},
            },
        ],
        catalog_detail="extended",
    )

    assert "SPEC  : LATN" in latex
    assert "SPEC  : ARAB" in latex
    assert "SPEC  : KHMR" in latex
    assert "<LATN|Latin sample>" in latex
    assert "<ARAB|Arabic sample>" in latex
    assert "<KHMR|Original Khmer>" in latex
    assert (
        latex.index("SPEC  : LATN")
        < latex.index("SPEC  : ARAB")
        < latex.index("SPEC  : KHMR")
    )


def test_generate_document_escapes_tex_size_and_family_commands(monkeypatch, tmp_path):
    """
    Ensure FILE and SPEC labels preserve literal TeX control sequences.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and ontology data.
    tmp_path : pathlib.Path
        Temporary directory used to create a placeholder font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "FreeSans.ttf"
    font_path.write_text("", encoding="utf-8")

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
    monkeypatch.setattr(
        document, "_filter_renderer_script_specimen", lambda _font, specimen: specimen
    )
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Latin sample"},
            ScriptISO("KHMR"): {"rtl": False, "specimen": "Khmer sample"},
        },
    )

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
        """
        Return a deterministic marker for rendered script variants.

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
        _ = font, safe_specimen, script0_iso, fullpath
        return "<render>", "Path=/tmp/,File=FreeSans.ttf"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    latex = document.generate_latex(
        [
            {
                "family": "FreeSans",
                "path": str(font_path),
                "style": "Regular",
                "script": "khmr",
                "specimen_text": "Original Khmer",
                "inference": {"scripts": ["khmr", "latn"], "languages": ["km"]},
                "coverage": {"scripts": ["khmr", "latn"]},
            },
        ],
        catalog_detail="extended",
    )

    assert "{\\footnotesize\\ttfamily FILE  : FreeSans.ttf [OK]}" in latex
    assert "{\\footnotesize\\ttfamily SPEC  : LATN}" in latex
    assert "{\\footnotesize\\ttfamily SPEC  : KHMR}" in latex
    assert "\x0c" not in latex
    assert "\t" not in latex


def test_generate_latex_compact_layout_includes_frontmatter_and_tighter_blocks(
    monkeypatch, tmp_path
):
    """
    Ensure compact catalogs include first-page metadata and compact labels.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and ontology data.
    tmp_path : pathlib.Path
        Temporary directory used to create a placeholder font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "FreeSans.ttf"
    font_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        document,
        "LATEX_INITIAL_CODE",
        (
            "HEADER %%FONTSHOW_GENERATED_AT%% %%FONTSHOW_SYSTEM_NAME%% "
            "%%FONTSHOW_HOSTNAME%% %%FONTSHOW_COMMAND_LINE%%\n"
        ),
    )
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
    monkeypatch.setattr(
        document, "_filter_renderer_script_specimen", lambda _font, specimen: specimen
    )
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Latin sample"},
            ScriptISO("CYRL"): {"rtl": False, "specimen": "Cyrillic sample"},
        },
    )

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
        """
        Return a deterministic compact marker for rendered script variants.

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
        _ = font, fullpath
        return f"<{script0_iso}|{safe_specimen}>", f"Path={script0_iso}"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    latex = document.generate_latex(
        [
            {
                "family": "FreeSans",
                "path": str(font_path),
                "style": "Regular",
                "script": "latn",
                "specimen_text": "Original Latin",
                "inference": {"scripts": ["latn", "cyrl"], "languages": ["en"]},
                "coverage": {"scripts": ["latn", "cyrl"]},
            },
        ],
        catalog_detail="compact",
        generation_metadata={
            "generation_timestamp": "April 02, 2026 18:15:13 CEST",
            "command_line": "fontshow create-catalog --inventory inv.json",
            "system_name": "Linux",
            "hostname": "atlas",
        },
    )

    assert (
        "April 02, 2026 18:15:13 CEST Linux atlas "
        "fontshow create-catalog --inventory inv.json" in latex
    )
    assert "\\setlength{\\itemsep}{0.25em}" in latex
    assert "\\setlength{\\parsep}{0pt}" in latex
    assert "\\setlength{\\parskip}{0.1em}" in latex
    assert "{\\footnotesize\\ttfamily FreeSans.ttf [OK]}" in latex
    assert "{\\footnotesize\\ttfamily LATN} <LATN|Original Latin>" in latex
    assert "{\\footnotesize\\ttfamily CYRL} <CYRL|Cyrillic sample>" in latex


def test_generate_latex_indexed_navigation_adds_toc_anchors_and_end_index(
    monkeypatch, tmp_path
):
    """
    Ensure indexed catalogs include TOC, family anchors, and end index.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers and ontology data.
    tmp_path : pathlib.Path
        Temporary directory used to create a placeholder font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "FreeSans.ttf"
    font_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE\n\\end{document}\n")
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
    monkeypatch.setattr(
        document, "_filter_renderer_script_specimen", lambda _font, specimen: specimen
    )
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Latin sample"},
        },
    )

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
        """
        Return a deterministic indexed marker for rendered script variants.

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
        _ = font, fullpath
        return f"<{script0_iso}|{safe_specimen}>", f"Path={script0_iso}"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    latex = document.generate_latex(
        [
            {
                "family": "FreeSans",
                "path": str(font_path),
                "style": "Regular",
                "script": "latn",
                "specimen_text": "Original Latin",
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "coverage": {"scripts": ["latn"]},
            },
        ],
        indexed_navigation=True,
    )

    assert "\\tableofcontents" in latex
    assert "\\hypertarget{fontshow-family-0001}{}" in latex
    assert "\\subsection{FreeSans}" in latex
    assert "\\section{Navigation Index}" in latex
    assert "\\hyperlink{fontshow-family-0001}{FreeSans}" in latex
    assert "END:1:DONE" in latex
    assert latex.endswith("\\end{document}\n")


def test_generate_latex_replaces_low_information_primary_specimen_with_curated_script(
    monkeypatch, tmp_path
):
    """
    Ensure low-information text specimens fall back to curated script samples.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers.
    tmp_path : pathlib.Path
        Temporary directory used to create a placeholder font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE\n\\end{document}\n")
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
    monkeypatch.setattr(document, "primary_script", lambda font: "latn")
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "Curated Latin sample"},
        },
    )
    monkeypatch.setattr(
        document,
        "_specimen_collect_cmap",
        lambda _path, _idx: {ord(ch) for ch in "Curated Latin sample"},
    )

    def render_stub(font, safe_specimen, script0_iso, fullpath, catalog_detail=None):
        """
        Return a deterministic marker for the selected specimen text.

        Parameters
        ----------
        font : dict[str, object]
            Font descriptor forwarded by the document generator.
        safe_specimen : str
            Specimen string selected for rendering.
        script0_iso : ScriptISO
            Script code chosen for rendering.
        fullpath : str
            Absolute font path.

        Returns
        -------
        tuple[str, str]
            Fake LaTeX render block and plain option string.
        """
        _ = font, fullpath
        return f"<{script0_iso}|{safe_specimen}>", "Path=LATN"

    monkeypatch.setattr(document, "_render_font_entry", render_stub)

    latex = document.generate_latex(
        [
            {
                "family": "Alpha",
                "path": str(font_path),
                "specimen_text": "A",
                "typography": {
                    "specimen_text": "A",
                    "specimen_strategy": "cmap",
                    "specimen_glyph_count": 1,
                },
                "inference": {"scripts": ["latn"], "languages": ["en"]},
                "coverage": {"scripts": ["latn"], "languages": ["en"]},
            }
        ]
    )

    assert "Curated Latin sample" in latex
    assert "<LATN|A>" not in latex


def test_generate_latex_marks_specialized_low_information_variant(
    monkeypatch, tmp_path
):
    """
    Ensure low-information specialized fonts are labeled instead of faking text.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace document helpers.
    tmp_path : pathlib.Path
        Temporary directory used to create a placeholder font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Icons.ttf"
    font_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(document, "LATEX_INITIAL_CODE", "HEADER\n")
    monkeypatch.setattr(document, "LATEX_END_CODE_1", "\nEND:")
    monkeypatch.setattr(document, "LATEX_END_CODE_2", ":DONE\n\\end{document}\n")
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
    monkeypatch.setattr(document, "primary_script", lambda font: "latn")
    monkeypatch.setattr(
        document,
        "SCRIPT_INFO",
        {
            ScriptISO("LATN"): {"rtl": False, "specimen": "xy"},
        },
    )
    monkeypatch.setattr(
        document,
        "_specimen_collect_cmap",
        lambda _path, _idx: {ord("x"), ord("y")},
    )
    monkeypatch.setattr(
        document,
        "_render_font_entry",
        lambda font, safe_specimen, script0_iso, fullpath, catalog_detail=None: (
            f"<{script0_iso}|{safe_specimen}>",
            "Path=LATN",
        ),
    )

    latex = document.generate_latex(
        [
            {
                "family": "Icons",
                "path": str(font_path),
                "specimen_text": "q",
                "typography": {
                    "specimen_text": "q",
                    "specimen_strategy": "cmap",
                    "specimen_glyph_count": 1,
                },
                "inference": {"scripts": ["latn"], "languages": []},
                "coverage": {"scripts": ["latn"], "languages": []},
            }
        ]
    )

    assert "[GLYPH SAMPLE]" in latex
    assert "Glyph sample" in latex
    assert "<|" in latex
