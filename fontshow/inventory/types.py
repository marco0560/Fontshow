"""
Fontshow – inventory.types
==========================

Internal data structures used during the font inventory construction
pipeline.

These types represent intermediate contexts and data containers used
while extracting metadata from fonts and building normalized inventory
entries.

They are not part of the public inventory schema and must not be used
outside the inventory subsystem.
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
