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
        Explicit persisted primary script when available; otherwise the
        dominant charset-derived script; otherwise the first inferred
        script; otherwise the first declared coverage script; otherwise
        None.

    Notes
    -----
    Script selection is deterministic. The helper trusts explicit
    inventory primary-script fields first so catalog generation does
    not re-derive a different answer from secondary evidence. When no
    explicit field is available, charset-derived script coverage under
    ``font["coverage"]["script_coverage_from_charset"]`` is used as a
    fallback. Non-writing scripts are ignored unless no writing
    scripts are available.
    """
    typography_raw = font.get("typography")
    typography = typography_raw if isinstance(typography_raw, Mapping) else {}
    explicit_typography_primary = typography.get("primary_script")
    if (
        isinstance(explicit_typography_primary, str)
        and explicit_typography_primary.strip()
        and explicit_typography_primary.strip().upper() != "UNKNOWN"
    ):
        return explicit_typography_primary

    inference_raw = font.get("inference")
    inference = inference_raw if isinstance(inference_raw, Mapping) else {}
    explicit_inference_primary = inference.get("primary_script")
    if (
        isinstance(explicit_inference_primary, str)
        and explicit_inference_primary.strip()
        and explicit_inference_primary.strip().upper() != "UNKNOWN"
    ):
        return explicit_inference_primary

    coverage_raw = font.get("coverage")
    coverage = coverage_raw if isinstance(coverage_raw, Mapping) else {}
    explicit_coverage_primary = coverage.get("primary_script")
    if (
        isinstance(explicit_coverage_primary, str)
        and explicit_coverage_primary.strip()
        and explicit_coverage_primary.strip().upper() != "UNKNOWN"
    ):
        return explicit_coverage_primary

    script_cov = coverage.get("script_coverage_from_charset")
    if isinstance(script_cov, dict) and script_cov:
        try:
            filtered = {
                str(script): value
                for script, value in script_cov.items()
                if isinstance(script, str)
                and script.strip()
                and isinstance(value, int | float)
                and str(script).lower() not in NON_WRITING_SCRIPTS
            }
            if filtered:
                return str(max(filtered.items(), key=lambda kv: kv[1])[0])
        except (TypeError, ValueError):
            pass

    scripts_raw = inference.get("scripts")
    scripts = scripts_raw if isinstance(scripts_raw, list) else []
    for script in scripts:
        if isinstance(script, str) and script.strip():
            return script
    cov_scripts_raw = coverage.get("scripts")
    cov_scripts = cov_scripts_raw if isinstance(cov_scripts_raw, list) else []
    for script in cov_scripts:
        if isinstance(script, str) and script.strip():
            return script
    return None
