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
    font_path: Path
    platform_name: str
    fonttools: dict[str, Any]
    fontconfig: dict[str, Any] | None
