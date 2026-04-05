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

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
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
from fontshow.inventory.schema_accessors import (
    get_font_lualatex_render_variants,
    get_specimen_glyph_count,
    get_specimen_strategy,
    get_specimen_text,
)
from fontshow.inventory.specimens import (
    MIN_SAMPLE_GLYPHS,
    _specimen_collect_cmap,
    _specimen_filter_text,
)
from fontshow.latex.policy import (
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


def _collect_polyglossia_other_languages(font_list: list[CatalogFontEntryV12]) -> str:
    """
    Return compatibility placeholder text for retired language setup.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        Catalog entries retained only for call-site compatibility.

    Returns
    -------
    str
        Empty string because specimen rendering no longer relies on
        predeclared Polyglossia secondary-language setup.
    """
    _ = font_list
    return ""


def _collect_polyglossia_font_setup(font_list: list[CatalogFontEntryV12]) -> str:
    """
    Return compatibility placeholder text for retired font setup.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        Catalog entries retained only for call-site compatibility.

    Returns
    -------
    str
        Empty string because direct specimen rendering no longer uses
        predeclared Polyglossia language-font commands.
    """
    _ = font_list
    return ""


@dataclass(frozen=True)
class _VariantRenderResult:
    """
    Structured render result for one family variant.

    Parameters
    ----------
    body_block : str
        LaTeX fragment emitted in the main catalog body.
    rendered : bool
        Whether the variant produced a visible main-body specimen block.
    missing_entry : str | None
        Appendix entry used when the variant could not be rendered.
    duplicate_entry : str | None
        Appendix entry used when the variant was collapsed as a duplicate.
    """

    body_block: str
    rendered: bool
    missing_entry: str | None = None
    duplicate_entry: str | None = None


@dataclass(frozen=True)
class _FamilyRenderResult:
    """
    Structured render result for one catalog family block.

    Parameters
    ----------
    body_block : str
        LaTeX fragment emitted in the main catalog body.
    navigation_entry : tuple[str, str] | None
        Optional indexed-navigation entry for the family.
    rendered : bool
        Whether the family produced any visible main-body output.
    missing_entries : tuple[str, ...]
        Appendix entries for variants that could not be rendered.
    duplicate_entries : tuple[str, ...]
        Appendix entries for variants collapsed as duplicates.
    """

    body_block: str
    navigation_entry: tuple[str, str] | None
    rendered: bool
    missing_entries: tuple[str, ...] = ()
    duplicate_entries: tuple[str, ...] = ()


def _catalog_family_anchor(index: int) -> str:
    """
    Build a deterministic hyperlink anchor for a rendered family block.

    Parameters
    ----------
    index : int
        One-based family index in render order.

    Returns
    -------
    str
        Stable Hyperref anchor identifier.
    """
    return f"fontshow-family-{index:04d}"


def _render_navigation_index(entries: list[tuple[str, str]]) -> str:
    """
    Render an end-of-document family navigation index.

    Parameters
    ----------
    entries : list[tuple[str, str]]
        Ordered ``(family_name, anchor_name)`` pairs from the rendered
        catalog body.

    Returns
    -------
    str
        LaTeX section text for the grouped navigation index, or an
        empty string when no entries are available.
    """
    if not entries:
        return ""

    grouped_entries: dict[str, list[tuple[str, str]]] = {}
    for family_name, anchor in entries:
        group = _navigation_group_key(family_name)
        grouped_entries.setdefault(group, []).append((family_name, anchor))

    lines = [
        "\\section{Navigation Index}",
        "\\begingroup",
        "\\small",
        "\\setlength{\\columnsep}{1.2em}",
        "\\begin{multicols}{3}",
        "\\raggedright",
    ]
    for group in sorted(grouped_entries):
        lines.append("\\textbf{" + escape_latex(group) + "}\\par")
        for family_name, anchor in grouped_entries[group]:
            lines.append(
                "\\hyperlink{" + anchor + "}{" + escape_latex(family_name) + "}\\\\"
            )
        lines.append("\\medskip")
    lines.extend(["\\end{multicols}", "\\endgroup"])
    return "\n".join(lines) + "\n"


def _navigation_group_key(family_name: str) -> str:
    """
    Return the grouped navigation bucket for a family name.

    Parameters
    ----------
    family_name : str
        Rendered family name used in the navigation index.

    Returns
    -------
    str
        Uppercase leading alphanumeric bucket, or ``"#"`` when the
        family starts with a non-alphanumeric character.
    """
    normalized = family_name.strip()
    if not normalized:
        return "#"

    first = normalized[0].upper()
    return first if first.isalnum() else "#"


def _variant_display_label(variant: CatalogFontEntryV12) -> str:
    """
    Return the visible file-oriented label for a family variant.

    Parameters
    ----------
    variant : CatalogFontEntryV12
        Variant entry being rendered.

    Returns
    -------
    str
        Basename-oriented label used in main-body and appendix output.
    """
    variant_path = str(variant.get("path", ""))
    _directory, variant_file = _normalize_path_for_latex(variant_path)
    if variant_file:
        return variant_file
    return str(variant.get("family", "")).strip() or "UNKNOWN"


def _variant_duplicate_key(variant: CatalogFontEntryV12) -> tuple[str, ...]:
    """
    Build a conservative duplicate-collapse key for a family variant.

    Parameters
    ----------
    variant : CatalogFontEntryV12
        Variant entry being considered for duplicate collapsing.

    Returns
    -------
    tuple[str, ...]
        Deterministic key built from stable inventory metadata.

    Notes
    -----
    The current renderer does not have a persisted content hash. This
    key therefore stays conservative and family-local, using stable
    identity and specimen fields rather than weak filesystem metadata
    such as timestamps.
    """
    return (
        str(variant.get("family", "")).strip(),
        str(variant.get("subfamily", "")).strip(),
        str(variant.get("full_name", "")).strip(),
        str(variant.get("postscript_name", "")).strip(),
        str(variant.get("version_string", "")).strip(),
        str(primary_script(variant) or "").strip().upper(),
        str(get_specimen_text(variant) or "").strip(),
        str(get_specimen_strategy(variant) or "").strip(),
        str(get_specimen_glyph_count(variant) or ""),
    )


def _render_missing_variants_section(entries: list[str]) -> str:
    """
    Render the appendix section for variants omitted from the main body.

    Parameters
    ----------
    entries : list[str]
        Ordered item strings for missing variants.

    Returns
    -------
    str
        LaTeX section text, or an empty string when no entries exist.
    """
    if not entries:
        return ""
    lines = [
        "\\section{Unrendered Variants}",
        "These variants were discovered in the inventory but did not produce a",
        "usable catalog specimen. They are listed here for traceability rather",
        "than being silently dropped.\\\\",
        "\\begin{itemize}",
    ]
    lines.extend("\\item " + entry for entry in entries)
    lines.append("\\end{itemize}")
    return "\n".join(lines) + "\n"


def _render_duplicate_sources_section(entries: list[str]) -> str:
    """
    Render the appendix section for collapsed duplicate font sources.

    Parameters
    ----------
    entries : list[str]
        Ordered item strings describing duplicate sources.

    Returns
    -------
    str
        LaTeX section text, or an empty string when no duplicates exist.
    """
    if not entries:
        return ""
    lines = [
        "\\section{Duplicate Sources}",
        "These sources were collapsed out of the main body because they match an",
        "already-rendered family variant on stable catalog metadata: family,",
        "subfamily, full name, PostScript name, version, primary script,",
        "specimen text, specimen strategy, and specimen glyph count.\\\\",
        "\\begin{itemize}",
    ]
    lines.extend("\\item " + entry for entry in entries)
    lines.append("\\end{itemize}")
    return "\n".join(lines) + "\n"


def _render_family_catalog_block(
    *,
    family_name: str,
    family_fonts: list[CatalogFontEntryV12],
    family_index: int,
    catalog_detail: CatalogDetailLevel,
    indexed_navigation: bool,
) -> _FamilyRenderResult:
    """
    Render one family block for the catalog body.

    Parameters
    ----------
    family_name : str
        Family label used for rendering and deterministic identifiers.
    family_fonts : list[CatalogFontEntryV12]
        Font variants grouped under the same family.
    family_index : int
        One-based family index in render order.
    catalog_detail : {"compact", "extended"}
        Requested catalog metadata detail level.
    indexed_navigation : bool
        Whether indexed navigation output is being generated.

    Returns
    -------
    _FamilyRenderResult
        Structured family render result containing the main-body block,
        optional navigation entry, and appendix data.
    """
    font = family_fonts[0]
    safe_name = escape_latex(family_name)

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
        ", ".join(_format_language_display(str(lang)) for lang in inferred_languages)
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
        catalog_detail=catalog_detail,
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
    missing_entries: list[str] = []
    duplicate_entries: list[str] = []
    duplicate_primary_by_key: dict[tuple[str, ...], str] = {}
    rendered_variants = 0

    for variant in family_fonts:
        duplicate_key = _variant_duplicate_key(variant)
        variant_label = _variant_display_label(variant)
        variant_path = str(variant.get("path", "")).strip() or "N/A"
        primary_label = duplicate_primary_by_key.get(duplicate_key)
        if primary_label is not None:
            duplicate_entries.append(
                " | ".join(
                    escape_latex(part)
                    for part in (
                        family_name,
                        variant_label,
                        variant_path,
                        primary_label,
                    )
                )
            )
            continue

        result = _render_variant_specimen_blocks(
            variant,
            family_name=family_name,
            catalog_detail=catalog_detail,
        )
        if result.rendered:
            variant_blocks.append(result.body_block)
            duplicate_primary_by_key[duplicate_key] = variant_label
            rendered_variants += 1
        elif result.missing_entry is not None:
            missing_entries.append(result.missing_entry)

    if not variant_blocks:
        return _FamilyRenderResult(
            body_block="",
            navigation_entry=None,
            rendered=False,
            missing_entries=tuple(missing_entries),
            duplicate_entries=tuple(duplicate_entries),
        )

    if indexed_navigation:
        anchor = _catalog_family_anchor(family_index)
        family_intro = (
            "\\hypertarget{"
            + anchor
            + "}{}\n\\pdfbookmark[2]{"
            + safe_name
            + "}{"
            + anchor
            + "-bookmark}\n\\subsection*{"
            + safe_name
            + "}"
        )
        if debug_block:
            family_intro += "\n\n" + debug_block
        navigation_entry = (family_name, anchor)
    else:
        family_intro = "\\item " + safe_name
        if debug_block:
            family_intro += " --- " + debug_block
        navigation_entry = None

    family_block = family_intro + "\n\n" + "\n\n".join(variant_blocks) + "\n\n"
    return _FamilyRenderResult(
        body_block=family_block,
        navigation_entry=navigation_entry,
        rendered=bool(rendered_variants),
        missing_entries=tuple(missing_entries),
        duplicate_entries=tuple(duplicate_entries),
    )


def _apply_frontmatter_metadata(
    latex_code: str,
    *,
    generation_timestamp: str,
    command_line: str,
    system_name: str,
    hostname: str,
) -> str:
    """
    Inject first-page generation metadata into the LaTeX template.

    Parameters
    ----------
    latex_code : str
        Template-derived LaTeX document containing front-matter markers.
    generation_timestamp : str
        Human-readable generation timestamp including time information.
    command_line : str
        Full CLI command line used to create the catalog.
    system_name : str
        Host operating system name rendered on the title page.
    hostname : str
        Hostname rendered on the title page.

    Returns
    -------
    str
        LaTeX document with front-matter markers replaced by escaped
        runtime metadata.
    """
    replacements = {
        "%%FONTSHOW_GENERATED_AT%%": escape_latex(generation_timestamp),
        "%%FONTSHOW_COMMAND_LINE%%": escape_latex(command_line),
        "%%FONTSHOW_SYSTEM_NAME%%": escape_latex(system_name),
        "%%FONTSHOW_HOSTNAME%%": escape_latex(hostname),
    }
    for marker, value in replacements.items():
        latex_code = latex_code.replace(marker, value)
    return latex_code


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


def _has_persisted_render_variant_success(
    font: CatalogFontEntryV12,
    script_iso: ScriptISO,
) -> bool:
    """
    Return whether a rendered script has persisted validation support.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose persisted render-variant results are read.
    script_iso : ScriptISO
        Script code about to be rendered.

    Returns
    -------
    bool
        ``True`` when the inventory either has no render-variant data
        yet or contains a matching successful render-path record.
    """
    variants = get_font_lualatex_render_variants(font)
    if not variants:
        return True

    _lang, fontspec_opts = _get_render_policy(script_iso)
    expected_script = str(script_iso)
    expected_opts = fontspec_opts or None
    for variant in variants:
        if variant.get("script") != expected_script:
            continue
        if variant.get("fontspec_opts") != expected_opts:
            continue
        return bool(variant.get("attempted")) and variant.get("loadable") is True
    return False


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
        specimen = _strip_ascii_control_chars(get_specimen_text(font) or "")
        if not _is_low_information_primary_specimen(font):
            return specimen

        curated = _curated_primary_script_specimen(font, script_iso)
        if curated:
            return curated

        if _should_suppress_specialized_primary_specimen(font):
            return ""

        return specimen

    script_info = SCRIPT_INFO.get(script_iso)
    if not isinstance(script_info, dict):
        return ""
    script_specimen = script_info.get("specimen")
    if not isinstance(script_specimen, str):
        return ""
    return _filter_renderer_script_specimen(font, script_specimen)


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


def _curated_primary_script_specimen(
    font: CatalogFontEntryV12,
    script_iso: ScriptISO,
) -> str:
    """
    Return a curated specimen fallback for a low-information primary specimen.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose primary specimen is being evaluated.
    script_iso : ScriptISO
        Primary script rendered for the current specimen block.

    Returns
    -------
    str
        Curated script specimen filtered through the font cmap, or an
        empty string when no suitable curated replacement exists.
    """
    script_info = SCRIPT_INFO.get(script_iso)
    if not isinstance(script_info, dict):
        return ""
    specimen = script_info.get("specimen")
    if not isinstance(specimen, str):
        return ""
    return _filter_renderer_script_specimen(font, specimen)


def _is_low_information_primary_specimen(font: CatalogFontEntryV12) -> bool:
    """
    Return whether the stored primary specimen is too small to be useful.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose primary specimen metadata is inspected.

    Returns
    -------
    bool
        ``True`` when the stored specimen glyph count is below the
        renderer threshold or the visible specimen is blank.
    """
    glyph_count = get_specimen_glyph_count(font)
    if glyph_count is not None:
        return glyph_count < MIN_SAMPLE_GLYPHS
    specimen = _strip_ascii_control_chars(get_specimen_text(font) or "")
    return not specimen.strip()


def _should_suppress_specialized_primary_specimen(font: CatalogFontEntryV12) -> bool:
    """
    Return whether a low-information primary specimen should be suppressed.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose specimen metadata is inspected.

    Returns
    -------
    bool
        ``True`` when the font behaves like a specialized non-text font
        and the primary specimen should be replaced by a compact notice.
    """
    if not _is_low_information_primary_specimen(font):
        return False

    coverage_raw = font.get("coverage")
    coverage = coverage_raw if isinstance(coverage_raw, Mapping) else {}
    inference_raw = font.get("inference")
    inference = inference_raw if isinstance(inference_raw, Mapping) else {}

    declared_languages = coverage.get("languages")
    inferred_languages = inference.get("languages")
    has_languages = any(
        isinstance(value, str) and value.strip()
        for values in (declared_languages, inferred_languages)
        if isinstance(values, list)
        for value in values
    )
    if has_languages:
        return False

    strategy = get_specimen_strategy(font) or ""
    return strategy in {"cmap", "validated-fallback"}


def _specialized_glyph_sample(
    font: CatalogFontEntryV12, *, max_glyphs: int = 12
) -> str:
    """
    Build a compact glyph-strip sample for a specialized non-text font.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose cmap is sampled.
    max_glyphs : int, optional
        Maximum number of glyphs to include in the strip.

    Returns
    -------
    str
        Space-separated visible glyph strip, or an empty string when no
        suitable glyphs can be found.
    """
    variant_path = str(font.get("path", "")).strip()
    if not variant_path:
        return ""

    cps = _specimen_collect_cmap(variant_path, None)
    if not cps:
        return ""

    glyphs: list[str] = []
    for cp in sorted(cps):
        ch = chr(cp)
        if not ch.strip():
            continue
        category = unicodedata.category(ch)
        if category in {"Cc", "Cf", "Cs", "Cn"} or category.startswith("M"):
            continue
        glyphs.append(ch)
        if len(glyphs) >= max_glyphs:
            break

    return " ".join(glyphs)


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
        Code-oriented compact label or extended metadata label.
    """
    code = escape_latex(str(script_iso).upper() or "UNKN")
    if catalog_detail == "compact":
        return r"{\footnotesize\ttfamily " + code + "}"
    return r"{\footnotesize\ttfamily SPEC  : " + code + "}"


def _render_variant_specimen_row(
    *,
    label: str,
    rendered_specimen: str,
) -> str:
    """
    Render one two-column specimen row.

    Parameters
    ----------
    label : str
        Narrow metadata label shown in the left column.
    rendered_specimen : str
        Pre-rendered LaTeX specimen block shown in the right column.

    Returns
    -------
    str
        Two-column LaTeX row with a narrow metadata column and a
        specimen column that can wrap independently.
    """
    return (
        "\\noindent"
        "\\begin{minipage}[t]{0.18\\linewidth}\\raggedright "
        + label
        + "\\end{minipage}\\hfill"
        + "\\begin{minipage}[t]{0.79\\linewidth}"
        + rendered_specimen.lstrip()
        + "\\end{minipage}\\par"
    )


def _render_variant_body_block(
    *,
    variant_label: str,
    rendered_blocks: list[str],
    catalog_detail: CatalogDetailLevel,
    is_glyph_sample: bool = False,
) -> str:
    """
    Render the full body block for a visible family variant.

    Parameters
    ----------
    variant_label : str
        File-oriented label for the rendered variant.
    rendered_blocks : list[str]
        Already-rendered specimen rows for the variant.
    catalog_detail : {"compact", "extended"}
        Requested catalog metadata detail level.
    is_glyph_sample : bool, optional
        Whether the variant renders a curated glyph strip instead of a
        normal text specimen.

    Returns
    -------
    str
        LaTeX body fragment for the variant.
    """
    header_prefix = "FILE  : " if catalog_detail == "extended" else ""
    header = (
        r"{\footnotesize\ttfamily " + header_prefix + escape_latex(variant_label) + "}"
    )
    if is_glyph_sample:
        note = (
            r"{\footnotesize\ttfamily "
            + ("SPEC  : " if catalog_detail == "extended" else "")
            + "GLYPH}"
        )
        rendered_blocks = [
            _render_variant_specimen_row(
                label=note,
                rendered_specimen=rendered_blocks[0],
            )
        ]
    return header + "\n" + "\n".join(rendered_blocks)


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
) -> _VariantRenderResult:
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
    _VariantRenderResult
        Structured result containing the main-body block when
        renderable, or appendix metadata when the variant is omitted.
    """
    variant_path = str(variant.get("path", ""))
    _, variant_file = _normalize_path_for_latex(variant_path)
    variant_label = variant_file or str(variant.get("family", "")).strip() or "UNKNOWN"

    script_candidates = _ordered_script_candidates(variant)
    rendered_blocks: list[str] = []
    for script_iso in script_candidates:
        if not _has_persisted_render_variant_success(variant, script_iso):
            continue
        specimen = _specimen_for_rendered_script(variant, script_iso)
        if not specimen:
            continue
        safe_specimen = _format_specimen_for_latex(specimen, script_iso)
        variant_render, _ = _render_font_entry(
            font=variant,
            safe_specimen=safe_specimen,
            script0_iso=script_iso,
            fullpath=variant_path,
            catalog_detail=catalog_detail,
        )
        if not variant_render:
            continue
        show_script_label = catalog_detail == "compact" or len(script_candidates) > 1
        if show_script_label:
            label = _render_script_label(script_iso, catalog_detail=catalog_detail)
            block = _render_variant_specimen_row(
                label=label,
                rendered_specimen=variant_render,
            )
            rendered_blocks.append(block)
        else:
            rendered_blocks.append(variant_render)

    variant_renderable = bool(rendered_blocks)
    if not variant_renderable and _should_suppress_specialized_primary_specimen(
        variant
    ):
        glyph_sample = _specialized_glyph_sample(variant)
        if glyph_sample:
            safe_glyph_sample = _format_specimen_for_latex(glyph_sample, ScriptISO(""))
            glyph_render, _ = _render_font_entry(
                font=variant,
                safe_specimen=safe_glyph_sample,
                script0_iso=ScriptISO(""),
                fullpath=variant_path,
                catalog_detail=catalog_detail,
            )
            if glyph_render:
                return _VariantRenderResult(
                    body_block=(
                        _render_variant_body_block(
                            variant_label=variant_label,
                            rendered_blocks=[glyph_render],
                            catalog_detail=catalog_detail,
                            is_glyph_sample=True,
                        )
                    ),
                    rendered=True,
                )

    if not variant_renderable:
        missing_entry = " | ".join(
            escape_latex(part)
            for part in (
                family_name,
                variant_label,
                variant_path.strip() or "N/A",
            )
        )
        return _VariantRenderResult(
            body_block="",
            rendered=False,
            missing_entry=missing_entry,
        )

    return _VariantRenderResult(
        body_block=(
            _render_variant_body_block(
                variant_label=variant_label,
                rendered_blocks=rendered_blocks,
                catalog_detail=catalog_detail,
            )
        ),
        rendered=True,
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
    longer wraps specimen blocks in ``\\foreignlanguage`` because the
    wrapper is fragile around paragraph boxes and duplicates shaping
    responsibility already covered by fontspec script options.
    """
    _ = font
    return False


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
    catalog_detail: CatalogDetailLevel = "compact",
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
    catalog_detail : {"compact", "extended"}, optional
        Requested catalog metadata detail level used to tune specimen
        density.

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
    The rendering path depends on the selected script policy. Specimens
    are rendered with direct inline ``\\fontspec`` blocks, and path-backed
    entries follow the same ``Path=...`` plus full filename contract used
    by the inventory loadability probes. The helper also returns a
    plain-text option string so the caller can include debugging
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

    specimen_size = "\\small " if catalog_detail == "compact" else ""
    specimen_prefix = (
        "\\raggedright" + specimen_size + "\\sloppy\\emergencystretch=2em "
    )

    if lang:
        _ = lang

    render = (
        " {\\begingroup"
        + specimen_prefix
        + "\\fontspec["
        + opts
        + "]{"
        + inline_font
        + "}"
        + safe_specimen
        + "\\par\\endgroup}"
    )

    return render, options_plain


def generate_latex(
    font_list: list[CatalogFontEntryV12],
    *,
    catalog_detail: CatalogDetailLevel = "compact",
    indexed_navigation: bool = False,
    generation_metadata: Mapping[str, str] | None = None,
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
    indexed_navigation : bool, optional
        When ``True``, emit anchor-based family navigation with PDF
        bookmarks and an end-of-document grouped navigation index.
    generation_metadata : collections.abc.Mapping[str, str] | None, optional
        Optional first-page metadata keys used to replace LaTeX
        front-matter placeholders. Missing keys fall back to empty
        strings.

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
        indexed_navigation=indexed_navigation,
        generation_metadata=generation_metadata,
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
    indexed_navigation: bool = False,
    generation_metadata: Mapping[str, str] | None = None,
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
    indexed_navigation : bool, optional
        When ``True``, emit subsection-based navigation with a clickable
        table of contents and an end-of-document navigation index.
    generation_metadata : collections.abc.Mapping[str, str] | None, optional
        Optional first-page metadata keys used to replace LaTeX
        front-matter placeholders. Missing keys fall back to empty
        strings.

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

    if "%%FONTSHOW_OTHER_LANGUAGES%%" in latex_code:
        latex_code = latex_code.replace(
            "%%FONTSHOW_OTHER_LANGUAGES%%",
            "",
        )
    else:
        log_warn("LaTeX template marker %%FONTSHOW_OTHER_LANGUAGES%% not found")

    frontmatter = dict(generation_metadata or {})
    latex_code = _apply_frontmatter_metadata(
        latex_code,
        generation_timestamp=frontmatter.get("generation_timestamp", ""),
        command_line=frontmatter.get("command_line", ""),
        system_name=frontmatter.get("system_name", ""),
        hostname=frontmatter.get("hostname", ""),
    )

    total = len(family_order)
    latex_code += "\\section{Font List}\n"
    navigation_entries: list[tuple[str, str]] = []
    missing_entries: list[str] = []
    duplicate_entries: list[str] = []
    if not indexed_navigation:
        latex_code += "\\begin{itemize}\n"
        latex_code += "\\setlength{\\itemsep}{0.25em}\n"
        latex_code += "\\setlength{\\parsep}{0pt}\n"
        latex_code += "\\setlength{\\parskip}{0.1em}\n"
        latex_code += "\\setlength{\\topsep}{0.25em}\n"

    for idx, fam in enumerate(family_order, start=1):
        if idx % 500 == 0 or idx == total:
            log_info(f"  ... processed {idx}/{total}")

        family_result = _render_family_catalog_block(
            family_name=fam,
            family_fonts=fonts_by_family[fam],
            family_index=idx,
            catalog_detail=catalog_detail,
            indexed_navigation=indexed_navigation,
        )
        missing_entries.extend(family_result.missing_entries)
        duplicate_entries.extend(family_result.duplicate_entries)
        if family_result.navigation_entry is not None:
            navigation_entries.append(family_result.navigation_entry)
        latex_code += family_result.body_block

    if not indexed_navigation:
        latex_code += "\\end{itemize}\n"

    # Closing document and printing indices
    latex_code += _render_excluded_fonts_section(excluded_fonts)
    latex_code += _render_missing_variants_section(missing_entries)
    latex_code += _render_duplicate_sources_section(duplicate_entries)
    closing = LATEX_END_CODE_1 + str(total) + LATEX_END_CODE_2
    document_end = "\n\\end{document}\n"
    if indexed_navigation and closing.endswith(document_end):
        closing = (
            closing[: -len(document_end)]
            + _render_navigation_index(navigation_entries)
            + document_end
        )
    latex_code += closing
    return latex_code
