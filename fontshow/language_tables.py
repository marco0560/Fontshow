"""
Fontshow — language_tables
==========================

Authoritative language ↔ script semantic mappings.

These mappings are NOT Unicode ontology.
They represent Fontshow's linguistic policy layer and are shared
between parsing and inference modules to avoid circular imports.
"""

from __future__ import annotations

from typing import Any

# ------------------------------------------------------------------
# Primary script per language (ISO-639 → ISO-15924)
# ------------------------------------------------------------------

LANGUAGE_PRIMARY_SCRIPT: dict[str, str] = {
    "ar": "ARAB",
    "bg": "CYRL",
    "cop": "COPT",
    "da": "LATN",
    "de": "LATN",
    "el": "GREK",
    "en": "LATN",
    "es": "LATN",
    "fi": "LATN",
    "fr": "LATN",
    "he": "HEBR",
    "hi": "DEVA",
    "hy": "ARMN",
    "it": "LATN",
    "ja": "JPAN",
    "ko": "HANG",
    "mk": "CYRL",
    "ne": "DEVA",
    "nl": "LATN",
    "no": "LATN",
    "pt": "LATN",
    "ru": "CYRL",
    "sr": "CYRL",
    "sv": "LATN",
    "th": "THAI",
    "ti": "ETHI",
    "uk": "CYRL",
    "vi": "LATN",
    "zh": "HANI",
}


# ------------------------------------------------------------------
# Language coverage profiles (Unicode-block-based)
# ------------------------------------------------------------------

LANGUAGE_PROFILES: dict[str, dict[str, Any]] = {
    # Arabic
    "ar": {
        "scripts": ["Arabic"],
        "required_blocks": ["Arabic"],
        "optional_blocks": ["Arabic Supplement"],
    },
    # Ethiopic
    "am": {
        "scripts": ["Ethiopic"],
        "required_blocks": ["Ethiopic"],
        "optional_blocks": ["Ethiopic Supplement", "Ethiopic Extended"],
    },
    # Cherokee
    "chr": {
        "scripts": ["Cherokee"],
        "required_blocks": ["Cherokee", "Cherokee Supplement"],
        "optional_blocks": [],
    },
    # German
    "de": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
    },
    # Greek
    "el": {
        "scripts": ["Greek"],
        "required_blocks": ["Greek and Coptic"],
        "optional_blocks": [],
    },
    # English
    "en": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
    },
    # French
    "fr": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
    },
    # Yi
    "ii": {
        "scripts": ["Yi"],
        "required_blocks": ["Yi Syllables"],
        "optional_blocks": [],
    },
    # Japanese
    "ja": {
        "scripts": ["Hiragana", "Katakana"],
        "required_blocks": ["Kana Supplement"],
        "optional_blocks": [
            "Hiragana",
            "Katakana",
            "Kana Extended-A",
            "CJK Unified Ideographs",
        ],
    },
    # Georgian
    "ka": {
        "scripts": ["Georgian"],
        "required_blocks": ["Georgian"],
        "optional_blocks": ["Georgian Supplement"],
    },
    # Lao
    "lo": {
        "scripts": ["Lao"],
        "required_blocks": ["Lao"],
        "optional_blocks": [],
    },
    # Myanmar
    "my": {
        "scripts": ["Myanmar"],
        "required_blocks": ["Myanmar", "Myanmar Extended-A", "Myanmar Extended-B"],
        "optional_blocks": [],
    },
    # Russian
    "ru": {
        "scripts": ["Cyrillic"],
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
    },
    # Tamil
    "ta": {
        "scripts": ["Tamil"],
        "required_blocks": ["Tamil", "Tamil Supplement"],
        "optional_blocks": [],
    },
    # Thai
    "th": {
        "scripts": ["Thai"],
        "required_blocks": ["Thai"],
        "optional_blocks": [],
    },
    # Chinese
    "zh": {
        "scripts": ["Han"],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
    },
}

# ------------------------------------------------------------------
# Script → display language mapping
# (authoritative; moved from infer_languages.py)
# ------------------------------------------------------------------
# Canonical display language per ISO-15924 script
#
# Purpose:
# Fontshow needs a representative language for specimen rendering,
# not linguistic capability classification.
#
# This mapping provides a deterministic fallback when coverage-based
# inference yields no reliable languages.
# ------------------------------------------------------------------

SCRIPT_TO_DISPLAY_LANGUAGE: dict[str, str] = {
    "arab": "ar",
    "armn": "hy",
    "beng": "bn",
    "buhd": "bku",
    "bugi": "bug",
    "cher": "chr",
    "cyrl": "ru",
    "deva": "hi",
    "ethi": "am",
    "geor": "ka",
    "grek": "el",
    "hani": "zh",
    "hebr": "he",
    "jpan": "ja",
    "khmr": "km",
    "laoo": "lo",
    "latn": "en",
    "mymr": "my",
    "sinh": "si",
    "taml": "ta",
    "thai": "th",
}

# ------------------------------------------------------------------
# ISO15924 → human-readable script names
# (authoritative; moved from create_catalog.py)
# ------------------------------------------------------------------

SCRIPT_ISO_TO_HUMAN: dict[str, str] = {
    "arab": "Arabic",
    "armn": "Armenian",
    "beng": "Bengali",
    "cher": "Cherokee",
    "cyrl": "Cyrillic",
    "deva": "Devanagari",
    "ethi": "Ethiopic",
    "geor": "Georgian",
    "grek": "Greek",
    "hani": "Han",
    "hebr": "Hebrew",
    "jpan": "Japanese",
    "khmr": "Khmer",
    "laoo": "Lao",
    "latn": "Latin",
    "mymr": "Myanmar",
    "sinh": "Sinhala",
    "taml": "Tamil",
    "thai": "Thai",
}

# ------------------------------------------------------------------
# Canonical sample text per script
# (authoritative; moved from parse_font_inventory.py)
# ------------------------------------------------------------------

SCRIPT_SAMPLES: dict[str, str] = {
    "Latin": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Greek": "Καλημέρα σας. Αυτό είναι ένα σύντομο δείγμα ελληνικού κειμένου.",
    "Cyrillic": "Пример текста на кириллице для проверки отображения шрифта.",
    "Arabic": "مرحبا بكم. هذا نص عربي قصير لاختبار عرض الخط بشكل صحيح.",
    "Hebrew": "שלום לכם. זהו טקסט עברי קצר לבדיקת הצגת הגופן.",
    "Thai": "สวัสดีครับ นี่เป็นข้อความภาษาไทยสั้น ๆ สำหรับทดสอบแบบอักษร",
    "Devanagari": "नमस्ते। यह देवनागरी लिपि का एक छोटा नमूना पाठ है।",
    "Hangul": "안녕하세요. 이것은 한글 글꼴 표시를 위한 짧은 예시 문장입니다.",
    "CJK": "漢字仮名交じり文の例。中文字符測試。日本語テスト。한국어 테스트。",
}

# ------------------------------------------------------------------
# Script → Polyglossia configuration
# (authoritative; moved from create_catalog.py)
# ------------------------------------------------------------------

SCRIPT_TO_POLYGLOSSIA: dict[str, tuple[str, str]] = {
    "arab": ("arabic", "Script=Arabic"),
    "beng": ("bengali", "Script=Bengali"),
    "deva": ("hindi", "Script=Devanagari"),
    "hani": ("chinese", ""),
    "hebr": ("hebrew", "Script=Hebrew"),
    "hira": ("japanese", ""),
    "kana": ("japanese", ""),
    "taml": ("tamil", "Script=Tamil"),
}
