"""
Fontshow — language_tables
==========================

Authoritative language ↔ script semantic mappings.

These mappings are NOT Unicode ontology.
They represent Fontshow's linguistic policy layer and are shared
between parsing and inference modules to avoid circular imports.
"""

from __future__ import annotations

from typing import Any, TypedDict

from fontshow.types import ScriptISO, ScriptRenderPolicy


class LanguageProfileISO(TypedDict, total=False):
    required_blocks: list[str]
    optional_blocks: list[str]
    scripts: list[ScriptISO]
    rtl: bool


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
    # Spanish
    "es": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
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
    # Italian
    "it": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
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
    # Portuguese
    "pt": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
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
    "hang": "ko",
    "hani": "zh",
    "hebr": "he",
    "hira": "ja",
    "jpan": "ja",
    "kana": "ja",
    "khmr": "km",
    "laoo": "lo",
    "latn": "en",
    "mymr": "my",
    "sinh": "si",
    "taml": "ta",
    "thai": "th",
    "yiii": "ii",
}

# ------------------------------------------------------------------
# ISO15924 → human-readable script names
# (authoritative; moved from create_catalog.py)
# ------------------------------------------------------------------

SCRIPT_ISO_TO_HUMAN_CANONICAL: dict[ScriptISO, str] = {
    ScriptISO("ARAB"): "Arabic",
    ScriptISO("ARMN"): "Armenian",
    ScriptISO("BENG"): "Bengali",
    ScriptISO("CHER"): "Cherokee",
    ScriptISO("CYRL"): "Cyrillic",
    ScriptISO("DEVA"): "Devanagari",
    ScriptISO("ETHI"): "Ethiopic",
    ScriptISO("GEOR"): "Georgian",
    ScriptISO("GREK"): "Greek",
    ScriptISO("HANI"): "Han",
    ScriptISO("HEBR"): "Hebrew",
    ScriptISO("JPAN"): "Japanese",
    ScriptISO("KHMR"): "Khmer",
    ScriptISO("LAOO"): "Lao",
    ScriptISO("LATN"): "Latin",
    ScriptISO("MYMR"): "Myanmar",
    ScriptISO("SINH"): "Sinhala",
    ScriptISO("TAML"): "Tamil",
    ScriptISO("THAI"): "Thai",
}

# ------------------------------------------------------------------
# Canonical sample text per script
# (authoritative; moved from parse_font_inventory.py)
# ------------------------------------------------------------------

SCRIPT_SAMPLES: dict[str, str] = {
    "Arabic": "مرحبا بكم. هذا نص عربي قصير لاختبار عرض الخط بشكل صحيح.",
    "Armenian": "Հայերեն տեքստի կարճ օրինակ։",
    "Bengali": "বাংলা ভাষা একটি সমৃদ্ধ ভাষা। এটি একটি সংক্ষিপ্ত উদাহরণ বাক্য।",
    "Cherokee": "ᎣᏏᏲ ᎤᏓᎷᎸᏔᏅ ᎠᎴ ᎤᎵᏍᎩᎸᏙᏗ",
    "CJK": "漢字仮名交じり文の例。中文字符測試。日本語テスト。한국어 테스트。",
    "Cyrillic": "Пример текста на кириллице для проверки отображения шрифта.",
    "Devanagari": "नमस्ते। यह देवनागरी लिपि का एक छोटा नमूना पाठ है।",
    "Ethiopic": "ሰላም ለእናንተ። ይህ አጭር የኢትዮጵያ ፊደል ምሳሌ ነው።",
    "Georgian": "ეს არის ქართული ტექსტის მოკლე ნიმუში.",
    "Greek": "Καλημέρα σας. Αυτό είναι ένα σύντομο δείγμα ελληνικού κειμένου.",
    "Hangul": "안녕하세요. 이것은 한글 글꼴 표시를 위한 짧은 예시 문장입니다.",
    "Han": "天地玄黃 宇宙洪荒 日月盈昃 辰宿列張。",
    "Hebrew": "שלום לכם. זהו טקסט עברי קצר לבדיקת הצגת הגופן.",
    "Hiragana": "いろはにほへと ちりぬるを",
    "Japanese": "日本語の文章例です。漢字とひらがなとカタカナを含みます。",
    "Katakana": "アイウエオ カキクケコ",
    "Khmer": "នេះជាឧទាហរណ៍អត្ថបទភាសាខ្មែរ។",
    "Lao": "ນີ້ແມ່ນຕົວຢ່າງຂໍ້ຄວາມພາສາລາວ",
    "Latin": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Myanmar": "မြန်မာစာ နမူနာ စာသား",
    "Sinhala": "සිංහල භාෂාව සුන්දරයි. මෙය කෙටි උදාහරණ වාක්‍යයකි.",
    "Tamil": "தமிழ் மொழி அழகானது. இது ஒரு சுருக்கமான எடுத்துக்காட்டு உரை.",
    "Thai": "สวัสดีครับ นี่เป็นข้อความภาษาไทยสั้น ๆ สำหรับทดสอบแบบอักษร",
    "Yi": "ꆈꌠꉙ ꉙꄜꐨ",
}

# ------------------------------------------------------------------
# Canonical sample text per language
# For future use
# ------------------------------------------------------------------

LANGUAGE_SAMPLES: dict[str, str] = {
    "de": "Falsches Üben von Xylophonmusik quält jeden größeren Zwerg.",
    "en": "The quick brown fox jumps over the lazy dog.",
    "es": "El veloz murciélago hindú comía feliz cardillo y kiwi.",
    "fr": "Portez ce vieux whisky au juge blond qui fume.",
    "it": "Quel vituperabile xenofobo zelante assaggia il whisky ed esclama: evviva!",
    "pt": "Luís argüia que o pingüim feliz tomava chá e bebia água.",
    "vi": "Chú bé nhỏ đứng giữa trời mưa, nói rằng tiếng Việt rất đẹp.",
}

# ------------------------------------------------------------------
# Script → Polyglossia configuration
# (authoritative; moved from create_catalog.py)
# ------------------------------------------------------------------

SCRIPT_ISO_TO_POLYGLOSSIA: dict[ScriptISO, tuple[str, str]] = {
    ScriptISO("ARAB"): ("arabic", "Script=Arabic"),
    ScriptISO("BENG"): ("bengali", "Script=Bengali"),
    ScriptISO("DEVA"): ("hindi", "Script=Devanagari"),
    ScriptISO("HANI"): ("chinese", ""),
    ScriptISO("HEBR"): ("hebrew", "Script=Hebrew"),
    ScriptISO("HIRA"): ("japanese", ""),
    ScriptISO("KANA"): ("japanese", ""),
    ScriptISO("TAML"): ("tamil", "Script=Tamil"),
}


# ------------------------------------------------------------------
# Languages requiring RTL rendering (polyglossia direction)
# ------------------------------------------------------------------

RTL_LANGUAGES: frozenset[str] = frozenset(
    {
        "arabic",
        "hebrew",
        "syriac",
        "persian",
        "urdu",
    }
)

# ------------------------------------------------------------------
# Table generated with scripts/generate_script_render_policy.py
# ------------------------------------------------------------------

SCRIPT_RENDER_POLICY: dict[ScriptISO, ScriptRenderPolicy] = {
    ScriptISO("Arab"): ScriptRenderPolicy(
        language="arabic",
        fontspec_opts="Script=Arabic",
        rtl=True,
        requires_polyglossia=True,
    ),
    ScriptISO("Beng"): ScriptRenderPolicy(
        language="bengali",
        fontspec_opts="Script=Bengali",
        rtl=False,
        requires_polyglossia=True,
    ),
    ScriptISO("Deva"): ScriptRenderPolicy(
        language="hindi",
        fontspec_opts="Script=Devanagari",
        rtl=False,
        requires_polyglossia=True,
    ),
    ScriptISO("Hani"): ScriptRenderPolicy(
        language="chinese",
        fontspec_opts="",
        rtl=False,
        requires_polyglossia=True,
    ),
    ScriptISO("Hebr"): ScriptRenderPolicy(
        language="hebrew",
        fontspec_opts="Script=Hebrew",
        rtl=True,
        requires_polyglossia=True,
    ),
    ScriptISO("Hira"): ScriptRenderPolicy(
        language="japanese",
        fontspec_opts="",
        rtl=False,
        requires_polyglossia=True,
    ),
    ScriptISO("Kana"): ScriptRenderPolicy(
        language="japanese",
        fontspec_opts="",
        rtl=False,
        requires_polyglossia=True,
    ),
    ScriptISO("Taml"): ScriptRenderPolicy(
        language="tamil",
        fontspec_opts="Script=Tamil",
        rtl=False,
        requires_polyglossia=True,
    ),
}

# ------------------------------------------------------------------
# Canonical ISO15924 → display language
# Table generated with scripts/generate_script_display_language.py
# ------------------------------------------------------------------

# Canonical ISO15924 → display language
# Table generated with scripts/generate_script_display_language.py
SCRIPT_ISO_TO_DISPLAY_LANGUAGE: dict[ScriptISO, str] = {
    ScriptISO("ARAB"): "ar",
    ScriptISO("ARMN"): "hy",
    ScriptISO("BENG"): "bn",
    ScriptISO("BUGI"): "bug",
    ScriptISO("BUHD"): "bku",
    ScriptISO("CHER"): "chr",
    ScriptISO("CYRL"): "ru",
    ScriptISO("DEVA"): "hi",
    ScriptISO("ETHI"): "am",
    ScriptISO("GEOR"): "ka",
    ScriptISO("GREK"): "el",
    ScriptISO("HANG"): "ko",
    ScriptISO("HANI"): "zh",
    ScriptISO("HEBR"): "he",
    ScriptISO("HIRA"): "ja",
    ScriptISO("JPAN"): "ja",
    ScriptISO("KANA"): "ja",
    ScriptISO("KHMR"): "km",
    ScriptISO("LAOO"): "lo",
    ScriptISO("LATN"): "en",
    ScriptISO("MYMR"): "my",
    ScriptISO("SINH"): "si",
    ScriptISO("TAML"): "ta",
    ScriptISO("THAI"): "th",
    ScriptISO("YIII"): "ii",
}

# ------------------------------------------------------------------
# Phase 5 — Human script names normalization
# ------------------------------------------------------------------

SCRIPT_HUMAN_TO_ISO: dict[str, ScriptISO] = {
    "Arabic": ScriptISO("ARAB"),
    "Armenian": ScriptISO("ARMN"),
    "Bengali": ScriptISO("BENG"),
    "CJK": ScriptISO("HANI"),
    "Cherokee": ScriptISO("CHER"),
    "Cyrillic": ScriptISO("CYRL"),
    "Devanagari": ScriptISO("DEVA"),
    "Ethiopic": ScriptISO("ETHI"),
    "Georgian": ScriptISO("GEOR"),
    "Greek": ScriptISO("GREK"),
    "Han": ScriptISO("HANI"),
    "Hangul": ScriptISO("HANG"),
    "Hebrew": ScriptISO("HEBR"),
    "Hiragana": ScriptISO("HIRA"),
    "Katakana": ScriptISO("KANA"),
    "Japanese": ScriptISO("JPAN"),
    "Khmer": ScriptISO("KHMR"),
    "Lao": ScriptISO("LAOO"),
    "Latin": ScriptISO("LATN"),
    "Myanmar": ScriptISO("MYMR"),
    "Sinhala": ScriptISO("SINH"),
    "Tamil": ScriptISO("TAML"),
    "Thai": ScriptISO("THAI"),
    "Yi": ScriptISO("YIII"),
}

# ------------------------------------------------------------------
# Canonical ISO15924 → script specimen
# Table generated with scripts/generate_script_iso_samples.py
# ------------------------------------------------------------------
SCRIPT_ISO_SAMPLES: dict[ScriptISO, str] = {
    ScriptISO("ARAB"): "مرحبا بكم. هذا نص عربي قصير لاختبار عرض الخط بشكل صحيح.",
    ScriptISO("ARMN"): "Հայերեն տեքստի կարճ օրինակ։",
    ScriptISO("BENG"): "বাংলা ভাষা একটি সমৃদ্ধ ভাষা। এটি একটি সংক্ষিপ্ত উদাহরণ বাক্য।",
    ScriptISO("CHER"): "ᎣᏏᏲ ᎤᏓᎷᎸᏔᏅ ᎠᎴ ᎤᎵᏍᎩᎸᏙᏗ",
    ScriptISO("CYRL"): "Пример текста на кириллице для проверки отображения шрифта.",
    ScriptISO("DEVA"): "नमस्ते। यह देवनागरी लिपि का एक छोटा नमूना पाठ है।",
    ScriptISO("ETHI"): "ሰላም ለእናንተ። ይህ አጭር የኢትዮጵያ ፊደል ምሳሌ ነው።",
    ScriptISO("GEOR"): "ეს არის ქართული ტექსტის მოკლე ნიმუში.",
    ScriptISO("GREK"): "Καλημέρα σας. Αυτό არის ένα σύντομο δείγμα ελληνικού κειμένου.",
    ScriptISO("HANG"): "안녕하세요. 이것은 한글 글꼴 표시를 위한 짧은 예시 문장입니다.",
    ScriptISO(
        "HANI"
    ): "漢字仮名交じり文の例。中文字符測試。日本語テスト。한국어 테스트。",
    ScriptISO("HEBR"): "שלום לכם. זהו טקסט עברי קצר לבדיקת הצגת הגופן.",
    ScriptISO("HIRA"): "いろはにほへと ちりぬるを",
    ScriptISO("JPAN"): "日本語の文章例です。漢字とひらがなとカタカナを含みます。",
    ScriptISO("KANA"): "アイウエオ カキクケコ",
    ScriptISO("KHMR"): "នេះជាឧទាហរណ៍អត្ថបទភាសាខ្មែរ។",
    ScriptISO("LAOO"): "ນີ້ແມ່ນຕົວຢ່າງຂໍ້ຄວາມພາສາລາວ",
    ScriptISO("LATN"): "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    ScriptISO("MYMR"): "မြန်မာစာ နမူနာ စာသား",
    ScriptISO("SINH"): "සිංහල භාෂාව සුන්දරයි. මෙය කෙටි උදාහරණ වාක්‍යයකි.",
    ScriptISO("TAML"): "தமிழ் மொழி அழகானது. இது ஒரு சுருக்கமான எடுத்துக்காட்டு உரை.",
    ScriptISO("THAI"): "สวัสดีครับ นี่เป็นข้อความภาษาไทยสั้น ๆ สำหรับทดสอบแบบอักษร",
    ScriptISO("YIII"): "ꆈꌠꉙ ꉙꄜꐨ",
}

# ISO-script normalized language profiles
# Generated with scripts/generate_language_profiles_iso.py
LANGUAGE_PROFILES_ISO: dict[str, LanguageProfileISO] = {
    "am": {
        "required_blocks": ["Ethiopic"],
        "optional_blocks": ["Ethiopic Supplement", "Ethiopic Extended"],
        "scripts": [ScriptISO("ETHI")],
    },
    "ar": {
        "required_blocks": ["Arabic"],
        "optional_blocks": ["Arabic Supplement"],
        "scripts": [ScriptISO("ARAB")],
    },
    "chr": {
        "required_blocks": ["Cherokee", "Cherokee Supplement"],
        "optional_blocks": [],
        "scripts": [ScriptISO("CHER")],
    },
    "de": {
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
        "scripts": [ScriptISO("LATN")],
    },
    "el": {
        "required_blocks": ["Greek and Coptic"],
        "optional_blocks": [],
        "scripts": [ScriptISO("GREK")],
    },
    "en": {
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "scripts": [ScriptISO("LATN")],
    },
    "es": {
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
        "scripts": [ScriptISO("LATN")],
    },
    "fr": {
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
        "scripts": [ScriptISO("LATN")],
    },
    "ii": {
        "required_blocks": ["Yi Syllables"],
        "optional_blocks": [],
        "scripts": [ScriptISO("YIII")],
    },
    "it": {
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
        "scripts": [ScriptISO("LATN")],
    },
    "ja": {
        "required_blocks": ["Kana Supplement"],
        "optional_blocks": [
            "Hiragana",
            "Katakana",
            "Kana Extended-A",
            "CJK Unified Ideographs",
        ],
        "scripts": [ScriptISO("HIRA"), ScriptISO("KANA")],
    },
    "ka": {
        "required_blocks": ["Georgian"],
        "optional_blocks": ["Georgian Supplement"],
        "scripts": [ScriptISO("GEOR")],
    },
    "lo": {
        "required_blocks": ["Lao"],
        "optional_blocks": [],
        "scripts": [ScriptISO("LAOO")],
    },
    "my": {
        "required_blocks": ["Myanmar", "Myanmar Extended-A", "Myanmar Extended-B"],
        "optional_blocks": [],
        "scripts": [ScriptISO("MYMR")],
    },
    "pt": {
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
        "scripts": [ScriptISO("LATN")],
    },
    "ru": {
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
        "scripts": [ScriptISO("CYRL")],
    },
    "ta": {
        "required_blocks": ["Tamil", "Tamil Supplement"],
        "optional_blocks": [],
        "scripts": [ScriptISO("TAML")],
    },
    "th": {
        "required_blocks": ["Thai"],
        "optional_blocks": [],
        "scripts": [ScriptISO("THAI")],
    },
    "zh": {
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
        "scripts": [ScriptISO("HANI")],
    },
}
