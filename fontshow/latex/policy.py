"""
LaTeX rendering policy helpers.

This module contains helpers that determine how fonts, scripts, and
languages should be represented when generating LaTeX catalog output.

Responsibilities
----------------
- Determine script display labels used in catalog entries.
- Compute rendering policies for fonts based on script and language
  metadata.
- Collect secondary language declarations required by Polyglossia.

Design principles
-----------------
These functions implement policy decisions about how font metadata is
mapped to LaTeX constructs, but they do not perform document generation
or string escaping. Low-level LaTeX-safe text handling lives in
``latex.render``.

Architectural role
------------------
This module belongs to the LaTeX subsystem and acts as a bridge between
inventory metadata and the LaTeX rendering layer used by the catalog
generation pipeline.
"""

import hashlib

from fontshow.core.types import CatalogFontEntryV12, ScriptISO
from fontshow.ontology.language_tables import SCRIPT_INFO


def _format_script_display(script_iso: str) -> str:
    """
    Convert ISO script code to human-readable display form.

    Parameters
    ----------
    script_iso : str
        ISO-15924 script code to format.

    Returns
    -------
    str
        Human-readable display label including the canonical script
        name when available.

    Notes
    -----
    Example: ``"TAML" -> "Tamil (TAML)"``.
    Unknown script codes are returned in their normalized uppercase form.
    """
    iso = ScriptISO(script_iso.upper())
    info = SCRIPT_INFO.get(iso)
    if info:
        human = info["canonical_name"]
        return f"{human} ({iso})"
    return str(iso)


def _get_render_policy(script_iso: ScriptISO) -> tuple[str, str]:
    """
    Return Polyglossia language and fontspec options for a script.

    Parameters
    ----------
    script_iso : ScriptISO
        Canonical script code used to look up rendering policy.

    Returns
    -------
    tuple[str, str]
        Two-element tuple ``(polyglossia_language, fontspec_options)``.

    Notes
    -----
    The policy is driven entirely by the ontology table. This helper
    must not synthesize `Script=` names from ISO-15924 codes because
    those values are not guaranteed to match the names accepted by
    `fontspec`.
    """
    info = SCRIPT_INFO.get(script_iso)

    if not info:
        return "", ""

    lang = info["polyglossia_language"]
    opts = info["fontspec_opts"] or ""

    return lang, opts


def _collect_polyglossia_other_languages(font_list: list[CatalogFontEntryV12]) -> str:
    """
    Collect secondary Polyglossia languages required by the font list.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        Catalog font entries whose inferred scripts determine required
        Polyglossia declarations.

    Returns
    -------
    str
        Concatenated ``\\setotherlanguage{...}`` declarations for the
        LaTeX preamble.

    Notes
    -----
    Deterministic behavior:
    - stable ordering (sorted)
    - never fails rendering if a mapping is missing
    - always includes ``latin`` to preserve legacy template assumptions
    """
    # Always include latin to preserve legacy template assumptions
    langs: set[str] = {"latin"}  # preserve previous template behavior

    for font in font_list:
        inf_raw = font.get("inference") or {}
        inf = inf_raw if isinstance(inf_raw, dict) else {}
        scripts_raw_obj = inf.get("scripts")
        scripts_raw: list[str] = (
            scripts_raw_obj if isinstance(scripts_raw_obj, list) else []
        )

        for s in scripts_raw:
            if not isinstance(s, str) or not s:
                continue
            script_iso = ScriptISO(s.upper())
            info = SCRIPT_INFO.get(script_iso)
            if info:
                lang = info["polyglossia_language"]
                if lang and lang != "english":
                    langs.add(lang)

    return "".join(f"\\setotherlanguage{{{lang}}}\n" for lang in sorted(langs))


def _collect_polyglossia_font_setup(font_list: list[CatalogFontEntryV12]) -> str:
    """
    Collect placeholder Polyglossia font-command declarations.

    Each language-specific ``\\<language>font`` command is declared once in the
    preamble so specimen entries can use a direct local ``\\renewfontfamily``
    without any TeX-side conditionals.
    """

    langs: set[str] = set()

    for font in font_list:
        inf_raw = font.get("inference") or {}
        inf = inf_raw if isinstance(inf_raw, dict) else {}
        scripts_raw_obj = inf.get("scripts")
        scripts_raw: list[str] = (
            scripts_raw_obj if isinstance(scripts_raw_obj, list) else []
        )

        for s in scripts_raw:
            if not isinstance(s, str) or not s:
                continue
            script_iso = ScriptISO(s.upper())
            info = SCRIPT_INFO.get(script_iso)
            if info:
                lang = info["polyglossia_language"]
                if lang and lang != "english":
                    langs.add(lang)

    return "".join(
        f"\\newfontfamily\\{lang}font{{Latin Modern Roman}}\n" for lang in sorted(langs)
    )


def nfss_family_id(font: dict) -> str:
    """
    Return a deterministic NFSS-safe identifier for a font.

    The identifier is derived from a stable SHA-256 digest of:
        <path>#0

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing the schema 1.2 `path`
        field.

    Returns
    -------
    str
        Deterministic identifier prefixed with "FS" and truncated to
        10 hexadecimal characters.

    Notes
    -----
    The identifier is stable for a given ``path`` and is suitable for use as an internal NFSS
    family token rather than a user-facing label.
    """
    file_path = font.get("path", "")

    key = f"{file_path}#0"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return "FS" + digest[:10]
