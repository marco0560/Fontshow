"""
LuaLaTeX font loadability validation helpers.

This module consumes persisted LuaLaTeX loadability for catalog font
entries before LaTeX output is generated.

Responsibilities
----------------
- Detect whether a font entry requires persisted LuaLaTeX loadability.
- Filter catalog inputs so unloadable fonts are skipped deterministically.

Design principles
-----------------
Catalog generation is a consumer of loadability state, not a probing
stage. Missing, stale, or incomplete persisted loadability is rejected
instead of being repaired with runtime subprocess probes.

Architectural role
------------------
This module belongs to the **catalog pipeline infrastructure layer** and
supports `create-catalog` robustness without changing the inventory
schema or the final rendering contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fontshow.core.cli_utils import log_warn
from fontshow.inventory.latex_validation_metadata import (
    collect_latex_validation_metadata,
)
from fontshow.inventory.loadability import validate_persisted_lualatex_loadability
from fontshow.inventory.schema_accessors import (
    get_font_lualatex_loadability,
)

if TYPE_CHECKING:
    from fontshow.core.types import CatalogFontEntryV12

_SUPPORTED_LOADABILITY_EXTENSIONS = {".ttf", ".otf", ".ttc"}


@dataclass(frozen=True)
class LoadabilityExclusion:
    """
    Structured unloadable-font record produced by catalog filtering.

    Parameters
    ----------
    identity : str
        Stable identity string used for logging.
    family : str
        Human-readable family name when available.
    path : str
        Font path associated with the skipped entry.
    detail : str | None
        Deterministic reason detail when available.
    """

    identity: str
    family: str
    path: str
    detail: str | None


@dataclass(frozen=True)
class LoadabilityFilterResult:
    """
    Result of filtering catalog fonts by LuaLaTeX loadability.

    Parameters
    ----------
    kept : list[CatalogFontEntryV12]
        Font entries retained for rendering.
    excluded : list[LoadabilityExclusion]
        Structured records for skipped unloadable fonts.
    """

    kept: list[CatalogFontEntryV12]
    excluded: list[LoadabilityExclusion]


def _is_validation_candidate(font: CatalogFontEntryV12) -> bool:
    """
    Return whether the font should be checked via LuaLaTeX.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font descriptor under consideration.

    Returns
    -------
    bool
        True when the entry points to an existing supported font file.

    Notes
    -----
    Validation is intentionally restricted to real on-disk font files so
    test inventories and inventories with missing paths keep their
    current behavior.
    """
    path = Path(str(font.get("path", "")).strip())
    return path.suffix.lower() in _SUPPORTED_LOADABILITY_EXTENSIONS and path.exists()


def _current_lualatex_validation_metadata() -> dict[str, object]:
    """
    Collect the current LuaLaTeX validation metadata for catalog gating.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, object]
        Current schema-compatible ``metadata.validation.lualatex`` block.
    """
    return collect_latex_validation_metadata()


def _persisted_loadability_state(
    font: CatalogFontEntryV12,
) -> tuple[str, str | None]:
    """
    Classify the persisted loadability state for a catalog font entry.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font descriptor to inspect.
    Returns
    -------
    tuple[str, str | None]
        Pair ``(state, detail)`` where ``state`` is either
        ``trusted-pass`` or ``trusted-fail``.

    Raises
    ------
    ValueError
        If the caller did not validate persisted loadability readiness
        before classification.
    """
    persisted = get_font_lualatex_loadability(font)
    persisted_loadable = persisted.get("loadable")
    if persisted_loadable is True:
        return "trusted-pass", None
    if persisted_loadable is False:
        persisted_reason = persisted.get("reason")
        detail = persisted_reason if isinstance(persisted_reason, str) else None
        return "trusted-fail", detail
    msg = "catalog inventory is missing complete persisted LuaLaTeX loadability"
    raise ValueError(msg)


def _font_warning_identity(font: CatalogFontEntryV12) -> str:
    """
    Build a human-readable identity for skipped-font warnings.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font descriptor used to construct the warning label.

    Returns
    -------
    str
        Human-readable label preferring full name or family, with path
        and stable font id included when available.
    """
    full_name = str(font.get("full_name", "")).strip()
    family = str(font.get("family", "")).strip()
    path = str(font.get("path", "")).strip()
    font_id = str(font.get("unique_font_id", "")).strip()

    label = full_name or family or path or font_id or "unknown-font"
    parts = [label]
    if path and path != label:
        parts.append(f"path={path}")
    if font_id and font_id != label:
        parts.append(f"id={font_id}")
    return " | ".join(parts)


def filter_loadable_catalog_fonts(
    fonts: list[CatalogFontEntryV12],
) -> list[CatalogFontEntryV12]:
    """
    Filter out fonts that fail best-effort LuaLaTeX validation.

    Parameters
    ----------
    fonts : list[CatalogFontEntryV12]
        Catalog font entries ready for rendering.

    Returns
    -------
    list[CatalogFontEntryV12]
        Original entries except those proven unloadable by LuaLaTeX.

    Notes
    -----
    This helper consumes persisted loadability only. It never performs
    runtime LuaLaTeX probes.
    """
    return filter_loadable_catalog_fonts_with_report(fonts).kept


def filter_loadable_catalog_fonts_with_report(
    fonts: list[CatalogFontEntryV12],
) -> LoadabilityFilterResult:
    """
    Filter fonts and collect structured unloadable-font reporting data.

    Parameters
    ----------
    fonts : list[CatalogFontEntryV12]
        Catalog font entries ready for rendering.

    Returns
    -------
    LoadabilityFilterResult
        Kept render set plus structured exclusion records.
    """
    validation_metadata = _current_lualatex_validation_metadata()
    candidates = [font for font in fonts if _is_validation_candidate(font)]
    if not candidates:
        return LoadabilityFilterResult(kept=list(fonts), excluded=[])

    errors = validate_persisted_lualatex_loadability(fonts, validation_metadata)
    if errors:
        preview = "; ".join(errors[:5])
        suffix = "" if len(errors) <= 5 else "; ..."
        msg = f"catalog inventory is not loadability-ready: {preview}{suffix}"
        raise ValueError(msg)

    kept: list[CatalogFontEntryV12] = []
    excluded: list[LoadabilityExclusion] = []
    for font in fonts:
        if not _is_validation_candidate(font):
            kept.append(font)
            continue

        state, detail = _persisted_loadability_state(font)
        if state == "trusted-pass":
            kept.append(font)
            continue
        if state == "trusted-fail":
            pass
        else:
            msg = f"unexpected persisted loadability state: {state}"
            raise ValueError(msg)

        identity = _font_warning_identity(font)
        log_warn(f"Font skipped: {identity}")
        log_warn("Reason: LuaLaTeX load failure")
        log_warn(f"Detail: {detail or 'LuaLaTeX load failure'}")
        excluded.append(
            LoadabilityExclusion(
                identity=identity,
                family=str(font.get("family", "")).strip(),
                path=str(font.get("path", "")).strip(),
                detail=detail,
            )
        )

    return LoadabilityFilterResult(kept=kept, excluded=excluded)
