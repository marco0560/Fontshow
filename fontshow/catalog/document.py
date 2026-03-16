"""
Catalog document rendering helpers.

This module contains the LaTeX document assembly logic used by the
catalog generation pipeline.

Responsibilities
----------------
- Normalize font file paths for LaTeX/fontspec usage.
- Select the primary script used for rendering decisions.
- Render individual catalog font entries.
- Assemble the final LaTeX document for a list of font descriptors.

Design principles
-----------------
The functions in this module operate on normalized inventory metadata
and produce catalog-level LaTeX structures. Low-level LaTeX escaping
and rendering primitives belong to the `fontshow.latex` subsystem,
while metadata extraction, labeling, and sample selection belong to
the `fontshow.catalog` domain helpers.

Architectural role
------------------
This module belongs to the **catalog domain layer** and implements the
document assembly stage between inventory-derived font metadata and the
final LaTeX output written by the create-catalog pipeline.
"""

from pathlib import Path

from fontshow.catalog.labels import primary_script
from fontshow.constants.catalog import EXCLUDED_FONTS
from fontshow.core.cli_utils import (
    log_info,
    log_warn,
)
from fontshow.core.types import (
    CatalogFontEntryV12,
    ScriptISO,
)
from fontshow.inventory.io import as_font_desc_list
from fontshow.inventory.metadata_processing import font_family
from fontshow.latex.policy import (
    _collect_polyglossia_font_setup,
    _collect_polyglossia_other_languages,
    _format_language_display,
    _format_script_display,
    _get_render_policy,
)
from fontshow.latex.render import (
    _latex_debug_literal,
    _latex_detokenize_safe,
    _renderer_option_prefix,
    _strip_ascii_control_chars,
    escape_latex,
)
from fontshow.latex.templates import (
    LATEX_END_CODE_1,
    LATEX_END_CODE_2,
    LATEX_INITIAL_CODE,
)


def _normalize_path_for_latex(fullpath: str) -> tuple[str, str]:
    """
    Normalize a font file path for LaTeX/fontspec usage.

    Parameters
    ----------
    fullpath : str
        Original font file path, possibly using platform-specific
        separators.

    Returns
    -------
    tuple[str, str]
        Two-element tuple ``(dir_with_trailing_slash, filename)``.

    Notes
    -----
    Uses forward slashes regardless of platform and guarantees a
    non-empty directory component, defaulting to ``"./"``.
    """
    norm = fullpath.replace("\\", "/")
    if "/" in norm:
        d, f = norm.rsplit("/", 1)
        d = (d + "/") if d else "./"
        return d, f
    return "./", norm


def _render_font_entry(
    *,
    font: CatalogFontEntryV12,
    safe_specimen: str,
    script0_iso: ScriptISO,
    fullpath: str,
) -> tuple[str, str]:
    """
    Render a single catalog entry specimen block and plain option string.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Normalized catalog font entry being rendered.
    safe_specimen : str
        Already-sanitized specimen text ready to be inserted into LaTeX.
    script0_iso : ScriptISO
        Primary ISO script code used to choose the rendering policy.
    fullpath : str
        Font file path used to build fontspec path and file options.

    Returns
    -------
    tuple[str, str]
        Two-element tuple ``(render_block, options_plain)``. Returns
        ``("", "")`` when the font path does not refer to a supported
        font file extension.

    Raises
    ------
    KeyError
        May propagate if downstream rendering-policy or script metadata
        lookups yield incomplete entries.

    Notes
    -----
    The rendering path depends on the selected script policy. Latin
    entries use a direct ``\\fontspec`` block, while eligible non-Latin
    entries emit a fully expanded Polyglossia/fontspec block with a
    per-entry font command generated in Python. The helper also returns
    a plain-text option string so the caller can include debugging
    information alongside the rendered specimen block.
    """

    path = str(font.get("path", "")).lower()
    if not path.endswith((".ttf", ".otf", ".ttc")):
        return "", ""

    _dir, _file = _normalize_path_for_latex(fullpath)
    detok_dir = "\\detokenize{" + _dir + "}"
    detok_file = "\\detokenize{" + _latex_detokenize_safe(_file) + "}"
    renderer_prefix = _renderer_option_prefix()

    lang, script_opt = _get_render_policy(script0_iso)

    render_options: list[str] = []
    if renderer_prefix:
        render_options.append(renderer_prefix.rstrip(","))
    render_options.append("Path=" + detok_dir)
    if script_opt:
        render_options.append(script_opt)
    opts = ",".join(render_options)

    options_plain = renderer_prefix + "Path=" + _dir + ",File=" + _file
    if script_opt:
        options_plain += "," + script_opt

    if script0_iso == ScriptISO("LATN"):
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{\\fontspec["
            + opts
            + "]{"
            + detok_file
            + "}"
            + safe_specimen
            + "}\\endgroup}"
        )
    elif lang:
        font_cmd = "\\" + lang + "font"
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em"
            "\\renewfontfamily"
            + font_cmd
            + "[BoldFont={},ItalicFont={},BoldItalicFont={},"
            + opts
            + "]{"
            + detok_file
            + "}"
            "\\foreignlanguage{"
            + lang
            + "}{"
            + font_cmd
            + "\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{"
            + safe_specimen
            + "}}"
            + "\\endgroup}"
        )
    elif script_opt:
        font_cmd = "\\fontshowentryfont"
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em"
            "\\newfontfamily"
            + font_cmd
            + "[BoldFont={},ItalicFont={},BoldItalicFont={},"
            + opts
            + "]{"
            + detok_file
            + "}"
            + font_cmd
            + "\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{"
            + safe_specimen
            + "}"
            + "\\endgroup}"
        )
    else:
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{\\fontspec["
            + opts
            + "]{"
            + detok_file
            + "}"
            + safe_specimen
            + "}\\endgroup}"
        )

    return render, options_plain


def generate_latex(font_list: list[CatalogFontEntryV12]) -> str:
    """
    Generate the full LaTeX document for the provided font descriptors.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        List of normalized catalog font entries used to assemble the
        final document.

    Returns
    -------
    str
        Complete LaTeX document as a string.

    Raises
    ------
    KeyError
        May propagate if downstream rendering helpers require metadata
        fields that are absent from an entry after normalization.

    Notes
    -----
    The function first normalizes the input list, groups entries by
    family while preserving first-seen order, injects auxiliary
    Polyglossia language declarations, and then renders one catalog
    block per family. Each family entry includes one debugging metadata
    header plus one specimen block per font file belonging to that
    family. Fonts with unsupported file extensions produce an empty
    render block while still contributing to the itemized catalog list.
    """
    font_list = as_font_desc_list(font_list)

    # --- GROUP BY FAMILY, PRESERVING FIRST-SEEN ORDER ---
    seen_families: set[str] = set()
    family_order: list[str] = []
    fonts_by_family: dict[str, list[CatalogFontEntryV12]] = {}
    for font in font_list:
        fam = font_family(font)
        if fam not in fonts_by_family:
            fonts_by_family[fam] = []
        fonts_by_family[fam].append(font)
        if fam not in seen_families:
            seen_families.add(fam)
            family_order.append(fam)

    log_info(f"Generating LaTeX file for {len(family_order)} fonts...")

    latex_code: str = LATEX_INITIAL_CODE

    other_langs = _strip_ascii_control_chars(
        _collect_polyglossia_other_languages(font_list)
    )
    lang_font_setup = _strip_ascii_control_chars(
        _collect_polyglossia_font_setup(font_list)
    )
    if "%%FONTSHOW_OTHER_LANGUAGES%%" in latex_code:
        latex_code = latex_code.replace(
            "%%FONTSHOW_OTHER_LANGUAGES%%",
            other_langs + lang_font_setup,
        )
    else:
        log_warn("LaTeX template marker %%FONTSHOW_OTHER_LANGUAGES%% not found")

    total = len(family_order)
    latex_code += "\\section{Font List}\n"
    latex_code += "\\begin{itemize}\n"

    for idx, fam in enumerate(family_order, start=1):
        family_fonts = fonts_by_family[fam]
        font = family_fonts[0]
        safe_name = escape_latex(fam)

        if idx % 500 == 0 or idx == total:
            log_info(f"  ... processed {idx}/{total}")

        specimen = _strip_ascii_control_chars(str(font.get("specimen_text", "")))

        # If the specimen has no whitespace and is long, TeX cannot line-break it
        # even inside \parbox{\linewidth}. Insert safe break opportunities.
        if (
            specimen
            and (not any(ch.isspace() for ch in specimen))
            and len(specimen) >= 40
        ):
            safe_specimen = r"\allowbreak{}".join(escape_latex(ch) for ch in specimen)
        else:
            safe_specimen = escape_latex(specimen)

        inference_raw = font.get("inference") or {}
        inference = inference_raw if isinstance(inference_raw, dict) else {}

        scripts_raw_obj = inference.get("scripts")
        scripts_raw: list[str] = (
            scripts_raw_obj if isinstance(scripts_raw_obj, list) else []
        )

        script0 = primary_script(font) or ""

        languages_raw_obj = inference.get("languages")
        inferred_languages: list[str] = (
            languages_raw_obj if isinstance(languages_raw_obj, list) else []
        )

        scripts_pretty = (
            ", ".join(_format_script_display(str(s)) for s in scripts_raw)
            if scripts_raw
            else "N/A"
        )

        languages_pretty = (
            ", ".join(
                _format_language_display(str(lang)) for lang in inferred_languages
            )
            if inferred_languages
            else "N/A"
        )

        fullpath = str(font.get("path", ""))
        script0_iso = ScriptISO(script0.upper()) if script0 else ScriptISO("")
        _, options_plain = _render_font_entry(
            font=font,
            safe_specimen=safe_specimen,
            script0_iso=script0_iso,
            fullpath=fullpath,
        )

        options_pretty = (
            _latex_debug_literal(options_plain.replace(",", ", "))
            if options_plain
            else "N/A"
        )

        debug_block = (
            "{\\footnotesize\\ttfamily SCRIPT: "
            + escape_latex(scripts_pretty)
            + "}\\newline"
            "{\\footnotesize\\ttfamily LANGS : "
            + escape_latex(languages_pretty)
            + "}\\newline"
            "{\\footnotesize\\ttfamily OPTS  : " + options_pretty + "}"
        )

        variant_blocks: list[str] = []
        for variant in family_fonts:
            variant_path = str(variant.get("path", ""))
            _, variant_file = _normalize_path_for_latex(variant_path)
            variant_exists = Path(variant_path).is_file()

            variant_script = primary_script(variant) or ""
            variant_script_iso = (
                ScriptISO(variant_script.upper()) if variant_script else ScriptISO("")
            )
            variant_render, _ = _render_font_entry(
                font=variant,
                safe_specimen=safe_specimen,
                script0_iso=variant_script_iso,
                fullpath=variant_path,
            )
            variant_blocks.append(
                "{\\footnotesize\\ttfamily FILE  : "
                + escape_latex(variant_file)
                + " [OK]}"
                + "\\newline"
                + (
                    "\\LogWorking{"
                    + escape_latex(fam + " / " + variant_file)
                    + "}"
                    + variant_render
                    if variant_exists
                    else "\\LogBroken{"
                    + escape_latex(fam + " / " + variant_file)
                    + "}[MISSING]"
                )
            )

        latex_code += (
            "\\item "
            + safe_name
            + " --- "
            + debug_block
            + "\\newline"
            + "\\newline".join(variant_blocks)
            + "\n"
        )

    latex_code += "\\end{itemize}\n"

    latex_code += "\n\n"
    for excluded_font in sorted(list(EXCLUDED_FONTS)):
        excluded_block: str = r"\LogExcluded{" + excluded_font + "}\n"
        latex_code += excluded_block

    # Closing document and printing indices
    latex_code += LATEX_END_CODE_1 + str(total) + LATEX_END_CODE_2
    return latex_code
