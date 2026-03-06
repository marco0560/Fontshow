"""
Catalog metadata helpers.

This module contains small utilities used by the catalog generation
pipeline to extract and normalize font metadata from inventory entries.

Responsibilities
----------------
- Derive canonical family names used for catalog grouping.
- Provide consistent access to font identity information.
- Normalize metadata fields used during catalog generation.

Design principles
-----------------
The helpers in this module operate purely on in-memory inventory
structures and perform no rendering or formatting. They exist to keep
catalog generation logic free from low-level metadata handling.

Architectural role
------------------
This module belongs to the **catalog domain layer**. It provides the
metadata foundation used by higher-level catalog helpers such as label
generation (`catalog.labels`), specimen selection (`catalog.sample`),
and document rendering (`catalog.document`).
"""

from fontshow.types import CatalogFontEntryV12


def font_family(font: CatalogFontEntryV12 | dict[str, object]) -> str:
    """
    Return a best-effort font family name for rendering and sorting.

    Parameters
    ----------
    font : dict[str, object]
        Schema 1.2 font descriptor dictionary.

    Returns
    -------
    str
        Resolved family name if available, otherwise "Unknown Font".
    """
    fam = font.get("family") or font.get("postscript_name") or font.get("full_name")

    return fam if isinstance(fam, str) and fam else "Unknown Font"
