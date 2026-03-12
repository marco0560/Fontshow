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

from fontshow.constants.catalog import EXCLUDED_FONTS
from fontshow.core.cli_utils import (
    log_info,
    log_warn,
)
from fontshow.core.types import (
    CatalogFontEntryV12,
    InferenceV12,
    ScriptISO,
)
from fontshow.inventory.io import as_font_desc_list
from fontshow.inventory.metadata_processing import font_family
from fontshow.latex.policy import (
    _collect_polyglossia_other_languages,
    _format_script_display,
    _get_render_policy,
)
from fontshow.latex.render import (
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
from fontshow.ontology.unicode_tables import NON_WRITING_SCRIPTS


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


def _select_primary_script(inference: InferenceV12) -> str:
    """
    Deterministically select the primary script used for rendering.

    Parameters
    ----------
    inference : InferenceV12
        Inference mapping that may contain charset-derived script
        coverage and ordered script guesses.

    Returns
    -------
    str
        Selected primary script identifier, or an empty string if no
        usable script information is available.

    Notes
    -----
    Selection priority is: dominant charset coverage excluding
    ``NON_WRITING_SCRIPTS``, then the first inferred script. Any
    malformed coverage data falls back safely to the remaining sources.
    """
    script0 = ""

    script_cov = inference.get("script_coverage_from_charset")
    if isinstance(script_cov, dict) and script_cov:
        try:
            filtered = {
                k: v
                for k, v in script_cov.items()
                if k.lower() not in NON_WRITING_SCRIPTS
            }
            source = filtered or script_cov
            script0 = max(source.items(), key=lambda kv: kv[1])[0]
        except (TypeError, ValueError):
            script0 = ""

    if not script0:
        scripts_raw = inference.get("scripts")
        if isinstance(scripts_raw, list) and scripts_raw:
            script0 = str(scripts_raw[0])

    return script0


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

    Notes
    -----
    The rendering path depends on the selected script policy. Latin
    entries use a direct ``\\fontspec`` block, while eligible non-Latin
    entries may use ``\\TestNonLatin`` with language and script options.
    The helper also returns a plain-text option string so the caller can
    include debugging information alongside the rendered specimen block.
    """

    path = str(font.get("path", "")).lower()
    if not path.endswith((".ttf", ".otf", ".ttc")):
        return "", ""

    _dir, _file = _normalize_path_for_latex(fullpath)
    detok_dir = "\\detokenize{" + _dir + "}"
    detok_file = "\\detokenize{" + _latex_detokenize_safe(_file) + "}"
    renderer_prefix = _renderer_option_prefix()

    lang, script_opt = _get_render_policy(script0_iso)

    opts = renderer_prefix + "Path=" + detok_dir
    if script_opt:
        opts += "," + script_opt

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
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em\\TestNonLatin{"
            + detok_file
            + "}{"
            + lang
            + "}{"
            + opts
            + "}{"
            + safe_specimen
            + "}\\endgroup}"
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

    Notes
    -----
    The function first normalizes the input list, deduplicates entries
    by family name, injects auxiliary Polyglossia language declarations,
    and then renders one catalog block per surviving font entry.
    Each entry includes debugging metadata about inferred scripts,
    inferred languages, and the effective fontspec options used for
    rendering. Fonts with unsupported file extensions produce an empty
    render block while still contributing to the itemized catalog list.
    """
    font_list = as_font_desc_list(font_list)

    # --- DEDUPLICATION BY FAMILY ---
    seen_families: set[str] = set()
    unique_fonts: list[CatalogFontEntryV12] = []
    for font in font_list:
        fam = font_family(font)
        if fam not in seen_families:
            seen_families.add(fam)
            unique_fonts.append(font)

    font_list = unique_fonts

    log_info(f"Generating LaTeX file for {len(font_list)} fonts...")

    latex_code: str = LATEX_INITIAL_CODE

    other_langs = _strip_ascii_control_chars(
        _collect_polyglossia_other_languages(font_list)
    )
    if "%%FONTSHOW_OTHER_LANGUAGES%%" in latex_code:
        latex_code = latex_code.replace("%%FONTSHOW_OTHER_LANGUAGES%%", other_langs)
    else:
        log_warn("LaTeX template marker %%FONTSHOW_OTHER_LANGUAGES%% not found")

    total = len(font_list)
    latex_code += "\\section{Font List (Stage 0)}\n"
    latex_code += "\\begin{itemize}\n"

    typed_font_list: list[CatalogFontEntryV12] = font_list
    for idx, font in enumerate(typed_font_list, start=1):
        fam = font_family(font)
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

        script0 = _select_primary_script(inference)

        languages_raw_obj = inference.get("languages")
        inferred_languages: list[str] = (
            languages_raw_obj if isinstance(languages_raw_obj, list) else []
        )

        fullpath = str(font.get("path", ""))
        fullpath_norm = fullpath.replace("\\", "/")
        detok_fullpath = "\\detokenize{" + _latex_detokenize_safe(fullpath_norm) + "}"

        script0_iso = ScriptISO(script0.upper()) if script0 else ScriptISO("")

        scripts_pretty = (
            ", ".join(_format_script_display(str(s)) for s in scripts_raw)
            if scripts_raw
            else "N/A"
        )

        languages_pretty = (
            ", ".join(str(lang) for lang in inferred_languages)
            if inferred_languages
            else "N/A"
        )

        options_plain = ""
        render = ""

        render, options_plain = _render_font_entry(
            font=font,
            safe_specimen=safe_specimen,
            script0_iso=script0_iso,
            fullpath=fullpath,
        )

        options_pretty = (
            "\\detokenize{" + _latex_detokenize_safe(options_plain) + "}"
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

        latex_code += (
            "\\item "
            + safe_name
            + " --- "
            + "\\IfFileExists{"
            + detok_fullpath
            + "}{[OK]\\newline"
            + debug_block
            + "\\newline"
            + render
            + "}{[MISSING]}"
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
