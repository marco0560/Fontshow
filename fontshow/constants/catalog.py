"""
Catalog generation constants.

This module contains configuration constants used during catalog
generation such as excluded fonts and default rendering parameters.
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
