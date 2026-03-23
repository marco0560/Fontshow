"""
Inventory subsystem constants.

This module defines static values shared by inventory validation and
normalization helpers.

Responsibilities
----------------
- Provide style-token detection patterns used during inventory checks.
- Centralize weight and width mappings for family-name leak heuristics.

Design principles
-----------------
Constants in this module must remain free of business logic so they can
be imported safely across the inventory subsystem.

Architectural role
------------------
This module belongs to the **constants infrastructure layer** and
provides inventory-specific constant values used by validation helpers.
"""

from __future__ import annotations

import re

STYLE_LEAK_RE = re.compile(
    r"\b("
    r"bold|italic|oblique|light|regular|medium|"
    r"semibold|extrabold|black|thin|"
    r"condensed|narrow|extended"
    r")\b",
    re.IGNORECASE,
)

STYLE_WEIGHT_RANGES: dict[str, tuple[int, int]] = {
    "thin": (1, 250),
    "light": (251, 350),
    "regular": (351, 450),
    "medium": (451, 550),
    "semibold": (551, 650),
    "bold": (651, 750),
    "extrabold": (751, 850),
    "black": (851, 1000),
}

STYLE_WIDTH_TOKENS = frozenset({"condensed", "narrow", "extended"})
STYLE_SLANT_TOKENS = frozenset({"italic", "oblique"})
