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

import re


def clean_font_name(name: str) -> str:
    """
    Normalize a raw font name to a base family-like name.

    Parameters
    ----------
    name : str
        Raw font name as obtained from system sources.

    Returns
    -------
    str
        Normalized base name with trailing container hints removed and
        common style or weight suffixes stripped.

    Notes
    -----
    Normalization is performed in two regex-based passes. The first
    removes terminal parenthetical format markers such as ``(TrueType)``
    and ``(OpenType)``. The second strips a broad set of style, weight,
    and width suffixes, including both English and Italian variants.
    """
    clean_name = re.sub(r"\s*\((TrueType|OpenType|True Type|Type 1)\)\s*$", "", name)

    variants = r"\s+(Bold|Italic|Light|Regular|Medium|Semibold|Black|Thin|Heavy|Narrow|Condensed|Extended|Grassetto|Corsivo|Chiaro|Normale|Medio|Nero|Sottile|Pesante|Condensato|Esteso).*$"
    return re.sub(variants, "", clean_name, flags=re.IGNORECASE).strip()
