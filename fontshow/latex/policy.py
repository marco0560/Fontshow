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
    Invariant:
    Non-Latin scripts must always receive an explicit ``Script=``
    option to enable HarfBuzz shaping.
    """
    info = SCRIPT_INFO.get(script_iso)

    if not info:
        return "", ""

    lang = info["polyglossia_language"]
    opts = info["fontspec_opts"] or ""

    # --- ensure shaping for non-Latin scripts ---
    if not opts and script_iso and script_iso != ScriptISO("LATN"):
        opts = f"Script={script_iso.title()}"

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


def nfss_family_id(font: dict) -> str:
    """
    Return a deterministic NFSS-safe identifier for a font.

    The identifier is derived from a stable SHA-256 digest of:
        <identity.file>#<ttc_index>

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing at least an `identity`
        mapping with optional `file` and `ttc_index` fields.

    Returns
    -------
    str
        Deterministic identifier prefixed with "FS" and truncated to
        10 hexadecimal characters.

    Notes
    -----
    The identifier is stable for a given ``identity.file`` and
    ``ttc_index`` pair and is suitable for use as an internal NFSS
    family token rather than a user-facing label.
    """
    identity = font.get("identity", {}) or {}
    file_path = identity.get("file", "")
    ttc_index = identity.get("ttc_index", 0)

    key = f"{file_path}#{ttc_index}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return "FS" + digest[:10]
