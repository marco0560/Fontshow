"""
Catalog labeling helpers.

This module provides utilities used when rendering catalog entries to
derive human-readable labels and badges from font metadata.

Responsibilities
----------------
- Determine the primary script of a font.
- Produce script and language labels used in catalog output.
- Generate font-type labels (serif, sans, mono, etc.).
- Assemble visual badge strings used in catalog entries.

Design principles
-----------------
These helpers operate purely on inventory metadata and return formatted
labels. They do not perform LaTeX escaping or document rendering; those
concerns belong to the LaTeX subsystem.

Architectural role
------------------
This module belongs to the catalog domain layer and is used by the
catalog rendering pipeline when constructing individual font entries.
"""

from fontshow.catalog.sample import choose_sample_language


def font_type_label(font: dict) -> str:
    """
    Classify font type for labeling purposes.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing an optional `classification`
        section.

    Returns
    -------
    str
        One of:
        - "EMOJI" if the font is classified as emoji
        - "DECORATIVE" if classified as decorative
        - "TEXT" otherwise

    Notes
    -----
    When multiple classification flags are present, emoji takes
    precedence over decorative, and decorative takes precedence over the
    default text label.
    """
    cls = font.get("classification", {}) or {}
    if cls.get("is_emoji"):
        return "EMOJI"
    if cls.get("is_decorative"):
        return "DECORATIVE"
    return "TEXT"


def primary_script(font: dict) -> str | None:
    """
    Determine the primary script associated with a font.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary possibly containing `inference`
        and `coverage` sections with script lists.

    Returns
    -------
    str | None
        First inferred script if available; otherwise the first declared
        coverage script; otherwise None.

    Notes
    -----
    Script selection is deterministic: the function prefers the first
    entry in ``font["inference"]["scripts"]`` and falls back to the
    first entry in ``font["coverage"]["scripts"]`` only when no inferred
    script is available.
    """
    inf = font.get("inference", {}) or {}
    scripts = inf.get("scripts", []) or []
    if scripts:
        return str(scripts[0])
    cov_scripts = font.get("coverage", {}).get("scripts", []) or []
    return str(cov_scripts[0]) if cov_scripts else None


def script_label(font: dict, max_scripts: int = 2) -> str:
    """
    Build a short uppercase label summarizing font scripts.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary possibly containing `inference`
        and `coverage` sections with script lists.
    max_scripts : int, optional
        Maximum number of scripts to include in the label (default is 2).

    Returns
    -------
    str
        Uppercase comma-separated script label, or "UNKNOWN" if no script
        information is available.

    Notes
    -----
    The function uses inferred scripts when available and falls back to
    coverage scripts otherwise. The output is truncated to the first
    ``max_scripts`` entries before joining them with commas.
    """
    inf = font.get("inference", {}) or {}
    scripts = inf.get("scripts", []) or []
    if not scripts:
        scripts = font.get("coverage", {}).get("scripts", []) or []
    if not scripts:
        return "UNKNOWN"
    return ", ".join(str(s).upper() for s in scripts[:max_scripts])


def language_label(font: dict) -> str:
    """
    Build an uppercase language label for a font.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary used to determine a representative
        language via `choose_sample_language()`.

    Returns
    -------
    str
        Uppercase language code if available, otherwise "N/A".

    Notes
    -----
    This function delegates representative language selection to
    `choose_sample_language()` so the label stays aligned with specimen
    selection behavior used elsewhere in the catalog pipeline.
    """
    lang = choose_sample_language(font)
    return lang.upper() if lang else "N/A"
