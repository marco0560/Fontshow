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

from typing import Literal

from fontshow.catalog.labels import primary_script
from fontshow.catalog.loadability import LoadabilityExclusion
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
from fontshow.inventory.schema_accessors import get_specimen_text
from fontshow.inventory.specimens import (
    MIN_SAMPLE_GLYPHS,
    _specimen_collect_cmap,
    _specimen_filter_text,
)
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
from fontshow.ontology.language_tables import SCRIPT_INFO

_SUPPORTED_PATH_BASED_EXTENSIONS = (".ttf", ".otf", ".ttc")
_MULTI_SPECIMEN_LIMIT = 4

CatalogDetailLevel = Literal["compact", "extended"]


def _ordered_script_candidates(font: CatalogFontEntryV12) -> list[ScriptISO]:
    """
    Return deterministic script candidates for multi-specimen rendering.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose inferred and fallback scripts are inspected.

    Returns
    -------
    list[ScriptISO]
        Ordered script candidates capped for renderer-side specimen
        expansion.
    """
    primary = primary_script(font) or ""
    ordered_raw: list[str] = []
    if primary:
        ordered_raw.append(primary)

    inference_raw = font.get("inference")
    inference = inference_raw if isinstance(inference_raw, dict) else {}
    scripts_raw = inference.get("scripts")
    if isinstance(scripts_raw, list):
        ordered_raw.extend(str(script) for script in scripts_raw)

    coverage_raw = font.get("coverage")
    coverage = coverage_raw if isinstance(coverage_raw, dict) else {}
    cov_scripts_raw = coverage.get("scripts")
    if isinstance(cov_scripts_raw, list):
        ordered_raw.extend(str(script) for script in cov_scripts_raw)

    seen: set[str] = set()
    normalized: list[ScriptISO] = []
    for raw in ordered_raw:
        cleaned = raw.strip().upper()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(ScriptISO(cleaned))

    def _sort_key(script_iso: ScriptISO) -> tuple[int, str]:
        info: dict[str, object] = dict(SCRIPT_INFO.get(script_iso, {}))
        if str(script_iso) == "LATN":
            return (0, str(script_iso))
        if bool(info.get("rtl", False)):
            return (1, str(script_iso))
        return (2, str(script_iso))

    return sorted(normalized, key=_sort_key)[:_MULTI_SPECIMEN_LIMIT]


def _specimen_for_rendered_script(
    font: CatalogFontEntryV12,
    script_iso: ScriptISO,
) -> str:
    """
    Resolve the specimen text used to render a specific script block.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor being rendered.
    script_iso : ScriptISO
        Script rendered for the current specimen block.

    Returns
    -------
    str
        Deterministic specimen text for the script, or an empty string
        when no script-appropriate sample can be resolved.
    """
    primary = (primary_script(font) or "").upper()
    if str(script_iso) == primary:
        return _strip_ascii_control_chars(get_specimen_text(font) or "")

    script_info = SCRIPT_INFO.get(script_iso)
    if not isinstance(script_info, dict):
        return ""
    specimen = script_info.get("specimen")
    if not isinstance(specimen, str):
        return ""
    return _filter_renderer_script_specimen(font, specimen)


def _filter_renderer_script_specimen(
    font: CatalogFontEntryV12,
    specimen: str,
) -> str:
    """
    Filter a renderer-added specimen against the font cmap.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose file-backed cmap is consulted.
    specimen : str
        Candidate ontology specimen selected for renderer-only output.

    Returns
    -------
    str
        Cmap-filtered specimen text, or an empty string when too few
        supported glyphs remain to render a meaningful sample.
    """
    variant_path = str(font.get("path", "")).strip()
    if not variant_path or not specimen:
        return ""

    cps = _specimen_collect_cmap(variant_path, None)
    if not cps:
        return ""

    filtered, glyphs = _specimen_filter_text(specimen, cps)
    if glyphs < MIN_SAMPLE_GLYPHS:
        return ""

    return _strip_ascii_control_chars(filtered)


def _render_script_label(
    script_iso: ScriptISO,
    *,
    catalog_detail: CatalogDetailLevel,
) -> str:
    """
    Render the visible label attached to a specimen block.

    Parameters
    ----------
    script_iso : ScriptISO
        Script code rendered by the current specimen block.
    catalog_detail : {"compact", "extended"}
        Requested catalog metadata detail level.

    Returns
    -------
    str
        Short compact label or extended metadata label.
    """
    display = escape_latex(_format_script_display(str(script_iso)))
    if catalog_detail == "compact":
        return r"{\footnotesize\ttfamily " + display + "}"
    return r"{\footnotesize\ttfamily SPEC  : " + display + "}"


def _render_family_debug_block(
    *,
    scripts_pretty: str,
    languages_pretty: str,
    options_pretty: str,
    catalog_detail: CatalogDetailLevel,
) -> str:
    """
    Render the family-level metadata block for the selected detail mode.

    Parameters
    ----------
    scripts_pretty : str
        Human-readable script summary for the family.
    languages_pretty : str
        Human-readable language summary for the family.
    options_pretty : str
        Deterministic plain-text rendering options.
    catalog_detail : {"compact", "extended"}
        Requested catalog metadata detail level.

    Returns
    -------
    str
        Extended metadata block or an empty string in compact mode.
    """
    if catalog_detail == "compact":
        return ""
    return (
        "{\\footnotesize\\ttfamily SCRIPT: " + escape_latex(scripts_pretty) + "}\n\n"
        "{\\footnotesize\\ttfamily LANGS : " + escape_latex(languages_pretty) + "}\n\n"
        "{\\footnotesize\\ttfamily OPTS  : " + options_pretty + "}"
    )


def _render_variant_specimen_blocks(
    variant: CatalogFontEntryV12,
    *,
    family_name: str,
    catalog_detail: CatalogDetailLevel,
) -> str:
    """
    Render one or more specimen blocks for a family variant.

    Parameters
    ----------
    variant : CatalogFontEntryV12
        Variant entry belonging to the current family group.
    family_name : str
        Family label used for deterministic log identifiers.
    catalog_detail : {"compact", "extended"}
        Requested catalog metadata detail level.

    Returns
    -------
    str
        LaTeX fragment containing the file header plus one or more
        rendered specimen blocks.
    """
    variant_path = str(variant.get("path", ""))
    _, variant_file = _normalize_path_for_latex(variant_path)
    variant_label = variant_file or str(variant.get("family", "")).strip() or "UNKNOWN"

    script_candidates = _ordered_script_candidates(variant)
    rendered_blocks: list[str] = []
    for script_iso in script_candidates:
        specimen = _specimen_for_rendered_script(variant, script_iso)
        if not specimen:
            continue
        safe_specimen = _format_specimen_for_latex(specimen, script_iso)
        variant_render, _ = _render_font_entry(
            font=variant,
            safe_specimen=safe_specimen,
            script0_iso=script_iso,
            fullpath=variant_path,
        )
        if not variant_render:
            continue
        show_script_label = catalog_detail == "compact" or len(script_candidates) > 1
        if show_script_label:
            rendered_blocks.append(
                _render_script_label(script_iso, catalog_detail=catalog_detail)
                + "\n\n"
                + "\\LogWorking{"
                + escape_latex(
                    family_name + " / " + variant_label + " / " + str(script_iso)
                )
                + "}"
                + variant_render
            )
        else:
            rendered_blocks.append(
                "\\LogWorking{"
                + escape_latex(family_name + " / " + variant_label)
                + "}"
                + variant_render
            )

    variant_renderable = bool(rendered_blocks)
    return (
        r"{\footnotesize\ttfamily FILE  : "
        + escape_latex(variant_label)
        + (" [OK]}" if variant_renderable else " [MISSING]}")
        + "\n\n"
        + (
            "\n\n".join(rendered_blocks)
            if variant_renderable
            else "\\LogBroken{"
            + escape_latex(family_name + " / " + variant_label)
            + "}[MISSING]"
        )
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


def _use_inline_fontspec_for_script(script0_iso: ScriptISO) -> bool:
    r"""
    Return whether a script-only entry should use inline ``\\fontspec``.

    Parameters
    ----------
    script0_iso : ScriptISO
        Primary script driving the specimen rendering branch.

    Returns
    -------
    bool
        ``True`` when the script should use the inline ``\\fontspec``
        fallback instead of a temporary ``\\newfontfamily`` command.

    Notes
    -----
    Deprecated compatibility scaffolding. The current renderer already
    uses the compact inline form unconditionally, so this helper
    always returns ``False``.
    """
    _ = script0_iso
    return False


def _use_inline_fontspec_for_font(
    font: CatalogFontEntryV12, script0_iso: ScriptISO
) -> bool:
    r"""
    Return whether a font should force the inline ``\\fontspec`` path.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor being rendered.
    script0_iso : ScriptISO
        Primary script driving the specimen rendering branch.

    Returns
    -------
    bool
        ``True`` when the specimen should use the inline file-oriented
        ``\\fontspec`` path instead of ``\\newfontfamily`` or
        ``\\renewfontfamily``.

    Notes
    -----
    Deprecated compatibility scaffolding. The current renderer already
    uses the compact inline form unconditionally, so this helper
    always returns ``False``.
    """
    _ = font
    _ = script0_iso
    return False


def _omit_script_option_for_script(script0_iso: ScriptISO) -> bool:
    """
    TODO: Deprecated and to be deleted.

    Return whether a script should skip the explicit ``Script=`` option.

    Parameters
    ----------
    script0_iso : ScriptISO
        Primary script driving the specimen rendering branch.

    Returns
    -------
    bool
        ``True`` when the render path should omit the explicit script
        option from the fontspec argument list.

    Notes
    -----
    Script-option omission is no longer used as a per-script exception
    policy. The helper remains only as compatibility scaffolding while
    the old policy layer is being removed.
    """
    _ = script0_iso
    return False


def _omit_script_option_for_font(
    font: CatalogFontEntryV12, script0_iso: ScriptISO
) -> bool:
    """
    TODO: Deprecated and to be deleted.

    Return whether a font should skip the explicit ``Script=`` option.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor being rendered.
    script0_iso : ScriptISO
        Primary script driving the specimen rendering branch.

    Returns
    -------
    bool
        ``True`` when the render path should omit the explicit script
        option from the fontspec argument list.

    Notes
    -----
    Script-option omission is no longer used as a per-font exception
    policy. The helper remains only as compatibility scaffolding while
    the old policy layer is being removed.
    """
    _ = font
    _ = script0_iso
    return False


def _use_language_wrapper_for_font(font: CatalogFontEntryV12) -> bool:
    r"""
    Return whether a font should be wrapped in ``\\foreignlanguage``.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor being rendered.

    Returns
    -------
    bool
        ``True`` when the specimen should remain wrapped in a
        Polyglossia language command.

    Notes
    -----
    Deprecated compatibility scaffolding. The current renderer no
    longer carries per-font or per-script language-wrapper exceptions,
    so this helper always returns ``True``.
    """
    _ = font
    return True


def _use_fontconfig_family_resolution(font: CatalogFontEntryV12) -> bool:
    """
    Return whether a font should be resolved by family name.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor being rendered.

    Returns
    -------
    bool
        ``True`` when the specimen should use a fontconfig-resolved
        family name instead of the inventory file path.

    Notes
    -----
    Family-based resolution is a conservative fallback used only when
    the inventory entry does not carry a usable filesystem path and a
    non-empty family name is available. File-backed fonts continue to
    use deterministic path-based loading.
    """
    path = str(font.get("path", "")).strip()
    family = str(font.get("family", "")).strip()
    return not path and bool(family)


def _format_specimen_for_latex(specimen: str, script0_iso: ScriptISO) -> str:
    """
    Format specimen text with conservative LaTeX break hints.

    Parameters
    ----------
    specimen : str
        Raw specimen text after ASCII control characters are stripped.
    script0_iso : ScriptISO
        Primary script retained for call-site compatibility.

    Returns
    -------
    str
        LaTeX-escaped specimen text, optionally augmented with
        ``llowbreak{}`` markers.

    Notes
    -----
    Long specimens without whitespace receive a break opportunity every
    5 characters, including CJK runs. The explicit markers keep line
    breaking deterministic across specimen scripts.
    """
    if not specimen:
        return ""

    if any(ch.isspace() for ch in specimen) or len(specimen) < 40:
        return escape_latex(specimen)

    _ = script0_iso
    chunks = [specimen[idx : idx + 5] for idx in range(0, len(specimen), 5)]
    return r"\allowbreak{}".join(escape_latex(chunk) for chunk in chunks)


def _render_font_entry(
    *,
    font: CatalogFontEntryV12,
    safe_specimen: str,
    script0_iso: ScriptISO,
    fullpath: str,
) -> tuple[str, str]:
    r"""
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
        ``("", "")`` when neither a supported file-backed path nor a
        safe family-name fallback is available.

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
    path = str(font.get("path", "")).strip()
    use_path_based_loading = path.lower().endswith(_SUPPORTED_PATH_BASED_EXTENSIONS)
    use_family_resolution = _use_fontconfig_family_resolution(font)
    if not use_path_based_loading and not use_family_resolution:
        return "", ""

    renderer_prefix = _renderer_option_prefix()

    lang, script_opt = _get_render_policy(script0_iso)

    render_options: list[str] = []
    if renderer_prefix:
        render_options.append(renderer_prefix.rstrip(","))
    if use_path_based_loading:
        _dir, _file = _normalize_path_for_latex(fullpath)
        detok_dir = "\\detokenize{" + _dir + "}"
        detok_file = "\\detokenize{" + _latex_detokenize_safe(_file) + "}"
        render_options.append("Path=" + detok_dir)
        inline_font = detok_file
        options_plain = renderer_prefix + "Path=" + _dir + ",File=" + _file
    else:
        family_name = str(font.get("family", "")).strip()
        render_options.append("UprightFont=*")
        inline_font = "\\detokenize{" + _latex_detokenize_safe(family_name) + "}"
        options_plain = renderer_prefix + "Family=" + family_name + ",UprightFont=*"

    if script_opt and not _omit_script_option_for_font(font, script0_iso):
        render_options.append(script_opt)
    opts = ",".join(render_options)

    if script_opt and not _omit_script_option_for_font(font, script0_iso):
        options_plain += "," + script_opt

    if script0_iso == ScriptISO("LATN"):
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{\\fontspec["
            + opts
            + "]{"
            + inline_font
            + "}"
            + safe_specimen
            + "}\\endgroup}"
        )
    elif lang:
        inline_options = opts
        if _use_language_wrapper_for_font(font):
            render = (
                " {\\begingroup\\sloppy\\emergencystretch=2em"
                "\\foreignlanguage{"
                + lang
                + "}{\\parbox{\\linewidth}{\\fontspec["
                + inline_options
                + "]{"
                + inline_font
                + "}"
                + safe_specimen
                + "}}"
                + "\\endgroup}"
            )
        else:
            render = (
                " {\\begingroup\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{\\fontspec["
                + inline_options
                + "]{"
                + inline_font
                + "}"
                + safe_specimen
                + "}\\endgroup}"
            )
    elif script_opt:
        render = (
            " {\\begingroup\\sloppy\\emergencystretch=2em\\parbox{\\linewidth}{\\fontspec["
            + opts
            + "]{"
            + detok_file
            + "}"
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


def generate_latex(
    font_list: list[CatalogFontEntryV12],
    *,
    catalog_detail: CatalogDetailLevel = "compact",
) -> str:
    """
    Generate the full LaTeX document for the provided font descriptors.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        List of normalized catalog font entries used to assemble the
        final document.
    catalog_detail : {"compact", "extended"}, optional
        Family and specimen metadata detail level used in the rendered
        catalog body.

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
    family. Fonts without a usable path can still render through the
    conservative family-name fallback, while unsupported file-backed
    entries continue to produce an empty render block.
    """
    return generate_latex_with_report(
        font_list,
        excluded_fonts=[],
        catalog_detail=catalog_detail,
    )


def _render_excluded_fonts_section(excluded_fonts: list[LoadabilityExclusion]) -> str:
    """
    Render a deterministic unloadable-font report section.

    Parameters
    ----------
    excluded_fonts : list[LoadabilityExclusion]
        Structured unloadable-font records.

    Returns
    -------
    str
        LaTeX section text, or an empty string when no exclusions exist.
    """
    if not excluded_fonts:
        return ""

    ordered = sorted(
        excluded_fonts,
        key=lambda item: (item.family, item.path, item.identity, item.detail or ""),
    )
    lines = [
        "\\section{Unloadable Fonts}",
        f"Excluded fonts: {len(ordered)}\\\\",
        "\\begin{itemize}",
    ]
    for item in ordered:
        family = escape_latex(item.family or "N/A")
        path = escape_latex(item.path or "N/A")
        detail = escape_latex(item.detail or "LuaLaTeX load failure")
        lines.append("\\item " + family + " | " + path + " | " + detail)
    lines.append("\\end{itemize}")
    return "\n".join(lines) + "\n"


def generate_latex_with_report(
    font_list: list[CatalogFontEntryV12],
    *,
    excluded_fonts: list[LoadabilityExclusion],
    catalog_detail: CatalogDetailLevel = "compact",
) -> str:
    """
    Generate the full LaTeX document with unloadable-font reporting.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        List of normalized catalog font entries used to assemble the
        final document.
    excluded_fonts : list[LoadabilityExclusion]
        Structured skipped-font records to include in the report.
    catalog_detail : {"compact", "extended"}, optional
        Family and specimen metadata detail level used in the rendered
        catalog body.

    Returns
    -------
    str
        Complete LaTeX document as a string.
    """
    font_list = as_font_desc_list(font_list)

    # --- GROUP BY FAMILY, PRESERVING FIRST-SEEN ORDER ---
    seen_families: set[str] = set()
    family_order: list[str] = []
    fonts_by_family: dict[str, list[CatalogFontEntryV12]] = {}
    for font in font_list:
        fam = font_family(font)
        if fam in EXCLUDED_FONTS:
            continue
        if fam not in fonts_by_family:
            fonts_by_family[fam] = []
        fonts_by_family[fam].append(font)
        if fam not in seen_families:
            seen_families.add(fam)
            family_order.append(fam)

    log_info(f"Generating LaTeX file for {len(family_order)} families...")

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
        specimen = _strip_ascii_control_chars(get_specimen_text(font) or "")
        safe_specimen = _format_specimen_for_latex(specimen, script0_iso)
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

        debug_block = _render_family_debug_block(
            scripts_pretty=scripts_pretty,
            languages_pretty=languages_pretty,
            options_pretty=options_pretty,
            catalog_detail=catalog_detail,
        )

        variant_blocks: list[str] = []
        for variant in family_fonts:
            variant_blocks.append(
                _render_variant_specimen_blocks(
                    variant,
                    family_name=fam,
                    catalog_detail=catalog_detail,
                )
            )
        family_intro = "\\item " + safe_name
        if debug_block:
            family_intro += " --- " + debug_block

        latex_code += family_intro + "\n\n" + "\n\n".join(variant_blocks) + "\n\n"

    latex_code += "\\end{itemize}\n"

    latex_code += "\n\n"
    for excluded_font in sorted(list(EXCLUDED_FONTS)):
        excluded_block: str = r"\LogExcluded{" + excluded_font + "}\n"
        latex_code += excluded_block

    # Closing document and printing indices
    latex_code += _render_excluded_fonts_section(excluded_fonts)
    latex_code += LATEX_END_CODE_1 + str(total) + LATEX_END_CODE_2
    return latex_code
