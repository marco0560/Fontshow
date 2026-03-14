"""
Catalog labeling helpers.

This module contains metadata-derived labeling utilities used by the
catalog pipeline.

Responsibilities
----------------
- Determine the primary script of a font.

Design principles
-----------------
Helpers in this module operate purely on inventory metadata. They do
not perform LaTeX escaping or document rendering.

Architectural role
------------------
This module belongs to the catalog domain layer and supports catalog
selection and rendering helpers.
"""


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
