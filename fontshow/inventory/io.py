"""
Inventory I/O helpers.

This module contains helpers used when loading and validating
font inventory JSON structures before they are processed by
the parsing pipeline.
"""

from __future__ import annotations

from typing import Any

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
