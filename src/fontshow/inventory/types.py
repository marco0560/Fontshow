"""
Inventory internal data structures.

This module defines internal data containers used during inventory
construction and metadata extraction.

Responsibilities
----------------
- Provide context objects used while building inventory entries.
- Define intermediate data structures used during font metadata
  extraction.
- Support deterministic construction of normalized inventory records.

Design principles
-----------------
These types represent internal implementation details of the inventory
pipeline and must not appear in the serialized inventory schema. The
module contains lightweight data structures without external
dependencies.

Architectural role
------------------
This module belongs to the **inventory subsystem** and defines internal
types used during font metadata extraction and inventory construction.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FontBuildContext:
    """
    Context object used while constructing a single inventory descriptor.

    Parameters
    ----------
    font_path : Path
        Filesystem path to the source font file.
    platform_name : str
        Normalized platform identifier for the current runtime.
    fonttools : dict[str, Any]
        Per-face metadata extracted from fontTools.
    fontconfig : dict[str, Any] | None
        Optional Fontconfig enrichment metadata.

    Notes
    -----
    The structure bundles all per-face inputs required by
    `build_font_descriptor()`: the source path, normalized platform
    name, fontTools metadata, and optional Fontconfig metadata.
    """

    font_path: Path
    platform_name: str
    fonttools: dict[str, Any]
    fontconfig: dict[str, Any] | None
