"""
Inventory I/O and normalization helpers.

This module provides utilities used to load, validate, and normalize
font inventory data structures before they are consumed by higher-level
catalog generation logic.

Responsibilities
----------------
- Load inventory JSON data from disk.
- Normalize filesystem paths contained in the inventory.
- Validate the structural integrity of inventory containers.
- Convert inventory structures into descriptor lists suitable for
  catalog generation.

Design principles
-----------------
The helpers in this module operate purely on inventory data and perform
no catalog rendering or LaTeX generation. They isolate inventory loading
and normalization logic so that catalog modules can assume a clean and
consistent in-memory representation.

Architectural role
------------------
This module belongs to the **inventory domain layer**. It forms the
boundary between raw inventory files produced by discovery/parsing
pipelines and the catalog subsystem that renders those fonts into the
final LaTeX catalog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fontshow.types import CatalogFontEntryV12

# ============================================================
# Helper: validate fonts container
# ============================================================


def _validate_fonts_container(data: dict[str, Any]) -> list[Any] | None:
    """
    Validate and return the 'fonts' container from an inventory JSON.

    Returns
    -------
    list[Any] | None
        The fonts list if present and valid, otherwise None.
    """
    fonts = data.get("fonts")

    if not isinstance(fonts, list):
        return None

    return fonts


def as_font_desc_list(fonts: Sequence[object]) -> list[CatalogFontEntryV12]:
    """
    Normalize a sequence of font descriptor objects.

    Parameters
    ----------
    fonts : collections.abc.Sequence[object]
        Sequence expected to contain font descriptor dictionaries.

    Returns
    -------
    list[CatalogFontEntryV12]
        List of validated font descriptor dictionaries.

    Raises
    ------
    TypeError
        If any element in `fonts` is not a dictionary.

    Notes
    -----
    Legacy coercion of non-dictionary entries is not supported.
    """
    out: list[CatalogFontEntryV12] = []
    for f in fonts:
        if not isinstance(f, dict):
            msg = f"Unexpected font entry type {type(f)} for font '{f}'"
            raise TypeError(msg)
        out.append(cast("CatalogFontEntryV12", f))
    return out
