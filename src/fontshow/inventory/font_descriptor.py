"""
Font inventory descriptor construction.

This module builds normalized font inventory entries from metadata
collected during the discovery stage.

Responsibilities
----------------
- Combine metadata obtained from platform tools and fontTools.
- Normalize font properties and metrics.
- Classify fonts according to format characteristics.
- Construct the final inventory descriptor for each font face.

Design principles
-----------------
The module performs deterministic transformations of already extracted
metadata. It must not invoke external tools or perform direct font
binary parsing.

Architectural role
------------------
This module belongs to the **inventory subsystem** and constructs the
normalized font descriptors that form the core of the Fontshow
inventory structure.
"""

from typing import Any

from fontshow.constants.opentype import (
    NAME_ID_FAMILY,
    NAME_ID_FULLNAME,
    NAME_ID_POSTSCRIPT,
    NAME_ID_SUBFAMILY,
    NAME_ID_VERSION,
)
from fontshow.core.types import Severity, WarningInfo
from fontshow.inventory.fonttools_extraction import (
    _best_name,
    extract_sample_text,
)
from fontshow.inventory.types import FontBuildContext
from fontshow.inventory.utils import make_font_id


def _normalize_metrics(
    fonttools,
    typography,
    names,
    identity: tuple[str | None, str | None, str | None, str | None],
):
    """
    Normalize core metrics and identity fields for descriptor emission.

    Parameters
    ----------
    fonttools : Any
        FontTools-derived metadata block for the current face.
    typography : Any
        Typography sub-block containing normalized weight and width data.
    names : Any
        Name-table mapping used to resolve fallback version strings.
    identity : tuple[str | None, str | None, str | None, str | None]
        Tuple ``(family, style, fullname, postscript)`` with optional
        identity values extracted earlier in descriptor construction.

    Returns
    -------
    tuple[str, str, str, str, str, int, int, int, int, int, float, bool, int]
        Normalized identity and metric values ready for insertion into
        the final inventory descriptor.

    Notes
    -----
    The helper applies schema-safe defaults and clamps width, weight,
    units-per-em, and glyph-count values to valid ranges expected by
    downstream inventory validation.
    """
    family, style, fullname, postscript = identity

    family_s = family or "Unknown"
    style_s = style or "Regular"
    fullname_s = fullname or f"{family_s} {style_s}"
    postscript_s = postscript or f"{family_s}-{style_s}".replace(" ", "")
    version_s = _best_name(names, NAME_ID_VERSION) if names else None
    version_s = version_s or "unknown"

    units_per_em_i = int(fonttools.get("units_per_em") or 1000)
    if units_per_em_i < 1:
        units_per_em_i = 1000

    ascent_i = int(fonttools.get("ascent") or 0)
    descent_i = int(fonttools.get("descent") or 0)

    weight_i = int(typography.get("weight_class") or 400)
    weight_i = min(max(weight_i, 1), 1000)

    width_i = int(typography.get("width_class") or 5)
    width_i = min(max(width_i, 1), 9)

    italic_angle_f = float(fonttools.get("italic_angle") or 0.0)
    is_fixed_pitch_b = bool(fonttools.get("is_fixed_pitch", False))

    glyph_count_i = max(int(fonttools.get("glyph_count") or 1), 1)

    return (
        family_s,
        style_s,
        fullname_s,
        postscript_s,
        version_s,
        units_per_em_i,
        ascent_i,
        descent_i,
        weight_i,
        width_i,
        italic_angle_f,
        is_fixed_pitch_b,
        glyph_count_i,
    )


def build_font_descriptor(ctx: FontBuildContext) -> dict[str, Any]:
    """
    Build the canonical per-font descriptor used in the JSON inventory.

    This function assembles **all metadata for a single font face** into a
    stable, JSON-serializable structure consumed by the rest of the project
    (parsing, inference, LaTeX rendering).

    The descriptor is intentionally verbose but normalized, so that downstream
    tools never need to re-open font files.

    High-level structure::

        {
          "identity": {...},
          "platform": {...},
          "format": {...},
          "coverage": {...},
          "typography": {...},
          "classification": {...},
          "license": {...},
          "vendor": ...,
          "embedding_rights": ...,
          "source": {...}
        }

    Parameters
    ----------
    ctx : FontBuildContext
        Descriptor-construction context bundling font path, platform
        identity, extracted fontTools metadata, and optional Fontconfig
        enrichment.

    Returns
    -------
    dict[str, Any]
        Dictionary representing the canonical font descriptor for the font face.

    Notes
    -----
    The descriptor is intentionally self-contained so downstream stages
    do not need to reopen the font binary.
    """
    names: dict[str, list[str]] = (
        ctx.fonttools.get("names", {})
        if isinstance(ctx.fonttools.get("names", {}), dict)
        else {}
    )

    # -------------------------------
    # Identity - names and file
    # -------------------------------
    family = _best_name(names, NAME_ID_FAMILY)
    style = _best_name(names, NAME_ID_SUBFAMILY)
    postscript = _best_name(names, NAME_ID_POSTSCRIPT)
    fullname = _best_name(names, NAME_ID_FULLNAME)

    # -------------------------------
    # Embedded sample text (font-level)
    # -------------------------------
    sample_text = {"source": "font", "text": ""}
    try:
        samples = extract_sample_text(str(ctx.font_path))
        if samples:
            sample_text = {
                "source": "font",
                # Use the first sample only for simplicity
                # (usually there's only one anyway)
                # TODO(#0): consider storing all samples?
                "text": samples[0],
            }
    except (OSError, ValueError, UnicodeError):
        sample_text = {"source": "font", "text": ""}

    # -------------------------------
    # FontConfig enrichment (optional)
    # -------------------------------
    languages: list[str] = []
    scripts: list[str] = []
    charset: str | None = None
    if ctx.fontconfig:
        languages = ctx.fontconfig.get("languages", []) or []
        scripts = ctx.fontconfig.get("scripts", []) or []
        charset = ctx.fontconfig.get("charset")

    # -------------------------------
    # Unicode coverage
    # -------------------------------
    unicode_block = ctx.fonttools.get("unicode", {}) or {}
    unicode_max = unicode_block.get("max")

    coverage = {
        "unicode": {
            "count": int(unicode_block.get("count", 0) or 0),
            "min": unicode_block.get("min"),
            "max": unicode_max,
        },
        "unicode_blocks": (
            ctx.fonttools.get("unicode_blocks", {})
            if isinstance(ctx.fonttools.get("unicode_blocks"), dict)
            else {}
        ),
        "scripts": scripts,
        "languages": languages,
        "charset": charset,
        "charset_ranges": (
            ctx.fonttools.get("unicode_ranges", [])
            if isinstance(ctx.fonttools.get("unicode_ranges"), list)
            else []
        ),
    }

    # -------------------------------
    # Typography source data
    # -------------------------------
    typography_source = {
        "weight_class": None,
        "width_class": None,
        "opentype_features": ctx.fonttools.get("opentype_features", []) or [],
    }

    os2 = ctx.fonttools.get("os2", {})
    if isinstance(os2, dict) and "error" not in os2:
        typography_source["weight_class"] = os2.get("weight_class")
        typography_source["width_class"] = os2.get("width_class")

    # -------------------------------
    # Format summary and classification
    # -------------------------------

    ttc_index = ctx.fonttools.get("ttc_index")

    # -------------------------------
    # Structural / extraction warnings emitted during descriptor construction
    # -------------------------------
    warnings: list[WarningInfo] = []

    if not family:
        warnings.append(
            {
                "code": "missing_family",
                "message": "Font has no family name",
                "severity": Severity.WARN,
            }
        )

    if not style:
        warnings.append(
            {
                "code": "missing_subfamily",
                "message": "Font has no subfamily/style name",
                "severity": Severity.WARN,
            }
        )

    unicode_block = coverage.get("unicode")
    unicode_count = (
        unicode_block.get("count") if isinstance(unicode_block, dict) else None
    )
    if not unicode_count:
        warnings.append(
            {
                "code": "no_unicode_coverage",
                "message": "Font reports no Unicode coverage",
                "severity": Severity.WARN,
            }
        )

    if ctx.fonttools.get("glyph_count") in (None, 0):
        warnings.append(
            {
                "code": "missing_glyph_count",
                "message": "Glyph count unavailable",
                "severity": Severity.WARN,
            }
        )

    if typography_source.get("weight_class") is None:
        warnings.append(
            {
                "code": "missing_weight_class",
                "message": "OS/2 weight_class missing",
                "severity": Severity.INFO,
            }
        )

    if typography_source.get("width_class") is None:
        warnings.append(
            {
                "code": "missing_width_class",
                "message": "OS/2 width_class missing",
                "severity": Severity.INFO,
            }
        )

    if not ctx.fonttools.get("ok", True):
        warnings.append(
            {
                "code": "fonttools_degraded",
                "message": ctx.fonttools.get("error", "fontTools extraction degraded"),
                "severity": Severity.WARN,
            }
        )

    # -------------------------------
    # Required schema normalizations for the active inventory contract
    # -------------------------------
    (
        family_s,
        style_s,
        fullname_s,
        postscript_s,
        version_s,
        units_per_em_i,
        ascent_i,
        descent_i,
        weight_i,
        width_i,
        italic_angle_f,
        is_fixed_pitch_b,
        glyph_count_i,
    ) = _normalize_metrics(
        ctx.fonttools,
        typography_source,
        names,
        (family, style, fullname, postscript),
    )

    # Specimen inference deferred to parse-inventory.
    # Must remain schema-valid (non-empty specimen_text).
    specimen_text = " "
    specimen_strategy = "deferred"
    specimen_glyph_count = None
    specimen_rejection_reason = "deferred_to_parse_inventory"
    metrics = {
        "units_per_em": units_per_em_i,
        "ascent": ascent_i,
        "descent": descent_i,
        "weight_class": weight_i,
        "width_class": width_i,
        "italic_angle": italic_angle_f,
        "is_fixed_pitch": is_fixed_pitch_b,
        "glyph_count": glyph_count_i,
    }
    typography = {
        "sample_text": sample_text,
        "specimen_text": specimen_text,
        "specimen_strategy": specimen_strategy,
        "specimen_glyph_count": specimen_glyph_count,
        "specimen_rejection_reason": specimen_rejection_reason,
        "primary_script": None,
        "script_display_name": None,
        "render_policy": {
            "polyglossia_language": None,
            "fontspec_opts": None,
        },
        "script_source": None,
        "opentype_features": typography_source["opentype_features"],
    }
    return {
        "path": str(ctx.font_path),
        "family": family_s,
        "subfamily": style_s,
        "typographic_subfamily": style_s,
        "full_name": fullname_s,
        "postscript_name": postscript_s,
        "version_string": version_s,
        "unique_font_id": make_font_id(str(ctx.font_path), ttc_index),
        "metrics": metrics,
        "coverage": coverage,
        "inference": {},
        "charset": {"fc_charset": coverage.get("charset")},
        "typography": typography,
        "loadability": {
            "lualatex": {
                "attempted": False,
                "loadable": None,
                "reason": None,
                "runtime_fingerprint": None,
                "probe_input": None,
            }
        },
        "warnings": warnings,
    }
