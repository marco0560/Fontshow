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
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from fontshow.core.types import FontRef, JSONDict

type ReadableFontMapping = Mapping[str, object]


class MutableFontMapping(Protocol):
    """
    Structural protocol for partially-built mutable font mappings.
    """

    def get(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:
        """
        Return a mapping value or a fallback default.

        Parameters
        ----------
        key : str
            Mapping key to resolve.
        default : object | None, optional
            Fallback value returned when ``key`` is absent.

        Returns
        -------
        object | None
            Stored mapping value or ``default`` when the key is missing.
        """
        ...

    def __setitem__(
        self,
        key: str,
        value: object,
    ) -> None: ...


def get_font_metrics(font: ReadableFontMapping) -> Mapping[str, object]:
    """
    Return the metrics block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, object]
        Metrics mapping when present. Falls back to the top-level entry
        so callers can still read legacy flat metric fields.
    """
    metrics = font.get("metrics")
    if isinstance(metrics, Mapping):
        return metrics
    return font


def get_font_typography(font: ReadableFontMapping) -> Mapping[str, object]:
    """
    Return the typography block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, object]
        Typography mapping when present. Falls back to the top-level
        entry for compatibility with legacy flat specimen fields.
    """
    typography = font.get("typography")
    if isinstance(typography, Mapping):
        return typography
    return font


def get_font_loadability(font: ReadableFontMapping) -> Mapping[str, object]:
    """
    Return the loadability block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, object]
        Loadability mapping when present, otherwise an empty mapping.
    """
    loadability = font.get("loadability")
    if isinstance(loadability, Mapping):
        return loadability
    return {}


def get_font_lualatex_loadability(
    font: ReadableFontMapping,
) -> Mapping[str, object]:
    """
    Return the nested LuaLaTeX loadability block for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Mapping[str, object]
        ``loadability.lualatex`` mapping when present, otherwise an
        empty mapping.
    """
    loadability = get_font_loadability(font)
    lualatex = loadability.get("lualatex")
    if isinstance(lualatex, Mapping):
        return lualatex
    return {}


def get_font_lualatex_render_variants(
    font: ReadableFontMapping,
) -> Sequence[Mapping[str, object]]:
    """
    Return persisted LuaLaTeX render-variant records for a font.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    collections.abc.Sequence[collections.abc.Mapping[str, object]]
        Persisted render-variant records.
    """
    lualatex = get_font_lualatex_loadability(font)
    raw_variants = lualatex.get("render_variants")
    if not isinstance(raw_variants, list):
        return ()
    return tuple(item for item in raw_variants if isinstance(item, Mapping))


def get_sample_text_info(font: FontRef) -> dict[str, Any] | None:
    """
    Return normalized sample-text metadata for a font entry.

    Parameters
    ----------
    font : FontRef
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


def get_sample_text_value(font: FontRef) -> str | None:
    """
    Return the plain sample-text value for a font entry.

    Parameters
    ----------
    font : FontRef
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


def get_specimen_text(font: ReadableFontMapping) -> str | None:
    """
    Return the accepted specimen text for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    str | None
        Accepted specimen text when present.
    """
    typography = get_font_typography(font)
    specimen_text = typography.get("specimen_text")
    if isinstance(specimen_text, str):
        return specimen_text
    return None


def get_specimen_strategy(font: ReadableFontMapping) -> str | None:
    """
    Return the accepted specimen strategy for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    str | None
        Accepted specimen strategy when present.
    """
    typography = get_font_typography(font)
    strategy = typography.get("specimen_strategy")
    if isinstance(strategy, str):
        return strategy
    return None


def get_specimen_glyph_count(font: ReadableFontMapping) -> int | None:
    """
    Return the accepted specimen glyph count for a font entry.

    Parameters
    ----------
    font : collections.abc.Mapping[str, object]
        Font entry to inspect.

    Returns
    -------
    int | None
        Accepted specimen glyph count when present.
    """
    typography = get_font_typography(font)
    glyph_count = typography.get("specimen_glyph_count")
    if isinstance(glyph_count, int):
        return glyph_count
    return None


def ensure_v13_typography(font: MutableFontMapping) -> JSONDict:
    """
    Ensure a mutable v1.4 typography block exists on a font entry.

    Parameters
    ----------
    font : MutableMapping[str, object]
        Font entry updated in place.

    Returns
    -------
    JSONDict
        JSON dictionary attached to ``font``.
    """
    typography = font.get("typography")
    if isinstance(typography, dict):
        return typography

    created: JSONDict = {}
    font["typography"] = created
    return created


def ensure_v13_loadability(
    font: MutableFontMapping,
) -> MutableMapping[str, Any]:
    """
    Ensure a mutable v1.4 loadability block exists on a font entry.

    Parameters
    ----------
    font : MutableMapping[str, object]
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
    font: FontRef,
) -> MutableMapping[str, Any]:
    """
    Ensure a mutable nested LuaLaTeX loadability block exists.

    Parameters
    ----------
    font : FontRef
        Font entry updated in place.

    Returns
    -------
    collections.abc.MutableMapping[str, Any]
        Mutable ``loadability.lualatex`` mapping attached to ``font``.
    """
    loadability = ensure_v13_loadability(cast("MutableFontMapping", font))
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
    font: FontRef,
    *,
    state: Mapping[str, Any],
) -> None:
    """
    Persist LuaLaTeX loadability fields in the v1.4 font entry.

    Parameters
    ----------
    font : FontRef
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
    font: FontRef,
    *,
    states: Sequence[Mapping[str, Any]],
) -> None:
    """
    Persist LuaLaTeX render-variant validation records in a font entry.

    Parameters
    ----------
    font : FontRef
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
            "specimen_text": state.get("specimen_text"),
            "specimen_glyph_count": state.get("specimen_glyph_count"),
            "specimen_strategy": state.get("specimen_strategy"),
        }
        for state in states
    ]


def set_specimen_fields(
    font: FontRef,
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
    font : FontRef
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
    typography = ensure_v13_typography(cast("MutableFontMapping", font))
    typography["specimen_text"] = specimen_text
    typography["specimen_strategy"] = specimen_strategy
    typography["specimen_glyph_count"] = specimen_glyph_count
    typography["specimen_rejection_reason"] = specimen_rejection_reason
