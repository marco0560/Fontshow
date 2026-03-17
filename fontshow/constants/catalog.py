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
        "Lohit Gujarati",
        "Lohit Gurmukhi",
        "Lohit Kannada",
        "MuseJazz Text",
        "MnSymbol",
    }
    DEFAULT_TEST_FONTS = {
        "Times New Roman",
        "Arial",
        "Calibri",
        "Lohit Assamese",
        "Lohit Gujarati",
        "Noto Sans Brahmi",
        "Noto Sans Buginese",
        "Noto Sans Buhid",
        "Noto Sans Canadian Aboriginal",
        "Noto Sans Coptic",
        "Noto Sans Deseret",
        "Noto Sans Yi",
        "Noto Sans Devanagari Light",
        "Noto Sans Arabic",
        "Noto Sans Hebrew",
        "Noto Sans Thai",
        "Noto Sans Armenian",
        "Noto Sans Elbasan",
        "Noto Sans Ethiopic",
        "Noto Sans Bengali",
        "Noto Sans Glagolitic",
        "Noto Sans Grantha",
        "Noto Sans Hanifi Rohingya",
        "Noto Sans Kaithi",
        "Noto Sans Tamil",
        "Noto Sans Khmer",
        "Noto Sans Lao",
        "Noto Sans Myanmar",
        "Noto Sans Georgian",
        "Noto Sans Cherokee",
        "Noto Sans Bamum",
        "Noto Sans Bamum Medium",
        "Noto Sans Bamum SemiBold",
        "Noto Sans Chakma",
        "Noto Sans Mro",
        "Noto Sans Old Permic",
        "Noto Sans Osage",
        "Noto Sans Newa",
        "Noto Sans NKo",
        "Noto Sans NKo Unjoined",
        "Noto Sans Mende Kikakui",
        "Noto Sans Lisu",
        "Noto Sans Limbu",
        "Noto Sans Mongolian",
        "Noto Sans Meetei Mayek",
        "Noto Sans Medefaidrin",
        "Noto Sans Kayah Li",
        "Noto Sans Psalter Pahlavi",
        "Noto Sans PsaPahlavi",
        "Noto Sans Sogdian",
        "Noto Sans Gothic",
        "Noto Sans Kannada",
        "Noto Sans Malayalam",
        "Noto Sans Oriya",
        "Noto Sans Telugu",
        "Noto Sans Thaana",
        "Noto Sans Syriac",
        "Noto Sans Old Sogdian",
        "Noto Sans OldSogdian",
        "Noto Sans InsPahlavi",
        "Noto Sans Rejang",
        "Noto Sans Saurashtra",
        "Noto Sans Sundanese",
        "Noto Sans Syloti Nagri",
        "Noto Sans Tai Le",
        "Noto Sans Vai",
        "Noto Sans Gunjala Gondi",
        "Noto Sans Gunjala Gondi Medium",
        "Noto Sans Gunjala Gondi Semibold",
        "Noto Sans Masaram Gondi",
        "Noto Sans Tagalog",
        "Noto Sans Tagbanwa",
        "Noto Sans Tai Tham",
        "Noto Sans Tai Viet",
        "Noto Sans Tifinagh",
        "Noto Sans Tirhuta",
        "Noto Sans Warang Citi",
        "Noto Serif TC",
        "Noto Serif Hentaigana",
        "Bandal",
    }
else:
    EXCLUDED_FONTS = set()
    DEFAULT_TEST_FONTS = set()
