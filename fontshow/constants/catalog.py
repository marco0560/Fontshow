"""
Catalog subsystem constants.

This module defines configuration constants used during catalog
generation.

Responsibilities
----------------
- Define font families excluded from catalog rendering.
- Provide default font sets used for catalog testing.
- Expose catalog-specific configuration values.

Design principles
-----------------
Constants are centralized in this module to avoid duplication and to
ensure consistent configuration across the catalog generation workflow.

Architectural role
------------------
This module belongs to the **constants infrastructure layer** and
provides catalog-specific configuration values used by the catalog
pipeline and CLI commands.

Notes
-----
The exported sets are platform-sensitive and are resolved at import
time from the current runtime environment.
"""

from fontshow.platform.runtime import IS_LINUX, IS_WINDOWS

EXCLUDED_FONTS: set[str]
DEFAULT_TEST_FONTS: set[str]

if IS_WINDOWS:
    EXCLUDED_FONTS = set()
    DEFAULT_TEST_FONTS = {"Times New Roman", "Arial", "Calibri", "Noto Sans"}
elif IS_LINUX:
    EXCLUDED_FONTS = {
        "MuseJazz Text",
        "MnSymbol",
    }
    DEFAULT_TEST_FONTS = {
        "Times New Roman",
        "Arial",
        "Calibri",
        "Noto Sans Buginese",
        "Noto Sans Buhid",
        "Noto Sans Yi",
        "Noto Sans Devanagari Light",
        "Noto Sans Arabic",
        "Noto Sans Hebrew",
        "Noto Sans Thai",
        "Noto Sans Armenian",
        "Noto Sans Ethiopic",
        "Noto Sans Bengali",
        "Noto Sans Tamil",
        "Noto Sans Khmer",
        "Noto Sans Lao",
        "Noto Sans Myanmar",
        "Noto Sans Georgian",
        "Noto Sans Cherokee",
        "Noto Serif TC",
        "Noto Serif Hentaigana",
        "Bandal",
    }
else:
    EXCLUDED_FONTS = set()
    DEFAULT_TEST_FONTS = set()
