"""
Schema-aware accessors for inventory font entries.

This module centralizes access to schema-versioned nested structures
such as ``metrics``, ``typography``, and ``loadability`` so callers do
not duplicate schema-shape assumptions throughout the codebase.

Responsibilities
----------------
- Read metrics and typography data from schema v1.4 font entries.
- Preserve read compatibility with older flat field layouts when
  needed by tests or intermediate data.
- Provide small mutation helpers for v1.4 font-entry sections.

Design principles
-----------------
Accessors are intentionally narrow and deterministic. They avoid
business logic and only normalize access to inventory data structures.

Architectural role
------------------
This module belongs to the **inventory subsystem** and supports schema
migration by isolating v1.4 layout knowledge from downstream consumers.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any


def get_font_metrics(font: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Return the metrics block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, Any]
        Metrics mapping when present. Falls back to the top-level entry
        so callers can still read legacy flat metric fields.
    """
    metrics = font.get("metrics")
    if isinstance(metrics, Mapping):
        return metrics
    return font


def get_font_typography(font: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Return the typography block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, Any]
        Typography mapping when present. Falls back to the top-level
        entry for compatibility with legacy flat specimen fields.
    """
    typography = font.get("typography")
    if isinstance(typography, Mapping):
        return typography
    return font


def get_font_loadability(font: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Return the loadability block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, Any]
        Loadability mapping when present, otherwise an empty mapping.
    """
    loadability = font.get("loadability")
    if isinstance(loadability, Mapping):
        return loadability
    return {}


def get_font_lualatex_loadability(font: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Return the nested LuaLaTeX loadability block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, Any]
        ``loadability.lualatex`` mapping when present, otherwise an
        empty mapping.
    """
    loadability = get_font_loadability(font)
    lualatex = loadability.get("lualatex")
    if isinstance(lualatex, Mapping):
        return lualatex
    return {}


def get_font_lualatex_render_variants(
    font: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    """
    Return persisted LuaLaTeX render-variant results for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    tuple[collections.abc.Mapping[str, Any], ...]
        Deterministic tuple of ``loadability.lualatex.render_variants``
        records. Non-mapping items are ignored.
    """
    lualatex = get_font_lualatex_loadability(font)
    raw_variants = lualatex.get("render_variants")
    if not isinstance(raw_variants, list):
        return ()
    return tuple(item for item in raw_variants if isinstance(item, Mapping))


def get_sample_text_info(font: Mapping[str, Any]) -> dict[str, Any] | None:
    """
    Return normalized sample-text metadata for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    dict[str, Any] | None
        Sample-text object when available. Legacy plain-string values
        are normalized into ``{"source": "font", "text": value}``.
    """
    typography = get_font_typography(font)
    sample_text = typography.get("sample_text")
    if isinstance(sample_text, dict):
        return sample_text
    if isinstance(sample_text, str):
        return {"source": "font", "text": sample_text}
    return None


def get_sample_text_value(font: Mapping[str, Any]) -> str | None:
    """
    Return the plain sample-text value for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    str | None
        Sample text when available, otherwise ``None``.
    """
    sample_info = get_sample_text_info(font)
    if not isinstance(sample_info, dict):
        return None
    text = sample_info.get("text")
    if isinstance(text, str):
        return text
    return None


def get_specimen_text(font: Mapping[str, Any]) -> str | None:
    """
    Return the specimen text for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    str | None
        Specimen text when available, otherwise ``None``.
    """
    typography = get_font_typography(font)
    specimen_text = typography.get("specimen_text")
    if isinstance(specimen_text, str):
        return specimen_text
    return None


def get_specimen_strategy(font: Mapping[str, Any]) -> str | None:
    """
    Return the specimen generation strategy for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    str | None
        Strategy string when available, otherwise ``None``.
    """
    typography = get_font_typography(font)
    strategy = typography.get("specimen_strategy")
    if isinstance(strategy, str):
        return strategy
    return None


def get_specimen_glyph_count(font: Mapping[str, Any]) -> int | None:
    """
    Return the accepted specimen glyph count for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Font entry to inspect.

    Returns
    -------
    int | None
        Glyph-count integer when available, otherwise ``None``.
    """
    typography = get_font_typography(font)
    glyph_count = typography.get("specimen_glyph_count")
    if isinstance(glyph_count, int):
        return glyph_count
    return None


def ensure_v13_typography(font: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """
    Ensure a mutable v1.4 typography block exists on a font entry.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Font entry updated in place.

    Returns
    -------
    collections.abc.MutableMapping[str, Any]
        Mutable typography mapping attached to ``font``.
    """
    typography = font.get("typography")
    if isinstance(typography, MutableMapping):
        return typography
    created: dict[str, Any] = {}
    font["typography"] = created
    return created


def ensure_v13_loadability(font: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """
    Ensure a mutable v1.4 loadability block exists on a font entry.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Font entry updated in place.

    Returns
    -------
    collections.abc.MutableMapping[str, Any]
        Mutable loadability mapping attached to ``font``.
    """
    loadability = font.get("loadability")
    if isinstance(loadability, MutableMapping):
        return loadability
    created: dict[str, Any] = {}
    font["loadability"] = created
    return created


def ensure_v13_lualatex_loadability(
    font: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """
    Ensure a mutable nested LuaLaTeX loadability block exists.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Font entry updated in place.

    Returns
    -------
    collections.abc.MutableMapping[str, Any]
        Mutable ``loadability.lualatex`` mapping attached to ``font``.
    """
    loadability = ensure_v13_loadability(font)
    lualatex = loadability.get("lualatex")
    if isinstance(lualatex, MutableMapping):
        return lualatex
    created: dict[str, Any] = {
        "attempted": False,
        "loadable": None,
        "reason": None,
        "runtime_fingerprint": None,
        "probe_input": None,
        "render_variants": [],
    }
    loadability["lualatex"] = created
    return created


def set_lualatex_loadability_fields(
    font: MutableMapping[str, Any],
    *,
    state: Mapping[str, Any],
) -> None:
    """
    Persist LuaLaTeX loadability fields in the v1.4 font entry.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Font entry updated in place.
    state : collections.abc.Mapping[str, Any]
        Mapping containing the persisted LuaLaTeX loadability fields to
        write to the nested v1.4 structure.

    Returns
    -------
    None
    """
    lualatex = ensure_v13_lualatex_loadability(font)
    lualatex["attempted"] = bool(state.get("attempted", False))
    lualatex["loadable"] = state.get("loadable")
    lualatex["reason"] = state.get("reason")
    lualatex["runtime_fingerprint"] = state.get("runtime_fingerprint")
    lualatex["probe_input"] = state.get("probe_input")
    raw_variants = lualatex.get("render_variants")
    if not isinstance(raw_variants, list):
        lualatex["render_variants"] = []


def set_lualatex_render_variants(
    font: MutableMapping[str, Any],
    *,
    states: Sequence[Mapping[str, Any]],
) -> None:
    """
    Persist LuaLaTeX render-variant validation records in a font entry.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Font entry updated in place.
    states : collections.abc.Sequence[collections.abc.Mapping[str, Any]]
        Ordered render-variant validation states to persist.

    Returns
    -------
    None
    """
    lualatex = ensure_v13_lualatex_loadability(font)
    lualatex["render_variants"] = [
        {
            "script": state.get("script"),
            "fontspec_opts": state.get("fontspec_opts"),
            "attempted": bool(state.get("attempted", False)),
            "loadable": state.get("loadable"),
            "reason": state.get("reason"),
            "runtime_fingerprint": state.get("runtime_fingerprint"),
            "probe_input": state.get("probe_input"),
        }
        for state in states
    ]


def set_specimen_fields(
    font: MutableMapping[str, Any],
    *,
    specimen_text: str,
    specimen_strategy: str,
    specimen_glyph_count: int,
    specimen_rejection_reason: str | None,
) -> None:
    """
    Persist specimen fields in the schema v1.4 typography block.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Font entry updated in place.
    specimen_text : str
        Final specimen text.
    specimen_strategy : str
        Deterministic specimen strategy label.
    specimen_glyph_count : int
        Count of accepted base glyphs in the specimen.
    specimen_rejection_reason : str | None
        Optional rejection/fallback reason.

    Returns
    -------
    None
    """
    typography = ensure_v13_typography(font)
    typography["specimen_text"] = specimen_text
    typography["specimen_strategy"] = specimen_strategy
    typography["specimen_glyph_count"] = specimen_glyph_count
    typography["specimen_rejection_reason"] = specimen_rejection_reason
