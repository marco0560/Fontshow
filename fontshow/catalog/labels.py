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

from collections.abc import Mapping

from fontshow.ontology.unicode_tables import NON_WRITING_SCRIPTS


def primary_script(font: Mapping[str, object]) -> str | None:
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
        Dominant charset-derived script when available; otherwise the
        first inferred script; otherwise the first declared coverage
        script; otherwise None.

    Notes
    -----
    Script selection is deterministic. When charset-derived script
    coverage is present under ``font["coverage"]["script_coverage_from_charset"]``,
    the highest-coverage writing script is preferred. Non-writing
    scripts are ignored unless no writing scripts are available.
    """
    coverage_raw = font.get("coverage")
    coverage = coverage_raw if isinstance(coverage_raw, Mapping) else {}
    script_cov = coverage.get("script_coverage_from_charset")
    if isinstance(script_cov, dict) and script_cov:
        try:
            filtered = {
                str(script): value
                for script, value in script_cov.items()
                if str(script).lower() not in NON_WRITING_SCRIPTS
            }
            source = filtered or script_cov
            return str(max(source.items(), key=lambda kv: kv[1])[0])
        except (TypeError, ValueError):
            pass

    inference_raw = font.get("inference")
    inference = inference_raw if isinstance(inference_raw, Mapping) else {}
    scripts_raw = inference.get("scripts")
    scripts = scripts_raw if isinstance(scripts_raw, list) else []
    if scripts:
        return str(scripts[0])
    cov_scripts_raw = coverage.get("scripts")
    cov_scripts = cov_scripts_raw if isinstance(cov_scripts_raw, list) else []
    return str(cov_scripts[0]) if cov_scripts else None
