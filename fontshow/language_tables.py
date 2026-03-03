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

from fontshow.types import ScriptISO, ScriptRenderPolicy, iso_to_tag, tag_to_iso

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
# Phase 6 — Rendering policy adapter
# ------------------------------------------------------------------

SCRIPT_RENDER_POLICY: dict[ScriptISO, ScriptRenderPolicy] = {}

for _script, (_lang, _opts) in SCRIPT_ISO_TO_POLYGLOSSIA.items():
    SCRIPT_RENDER_POLICY[_script] = ScriptRenderPolicy(
        language=_lang,
        fontspec_opts=_opts,
        rtl=_lang in RTL_LANGUAGES,
        requires_polyglossia=bool(_lang),
    )

# ------------------------------------------------------------------
# Ontology invariants (Phase 5)
# ------------------------------------------------------------------


def _validate_script_identifier_invariants() -> None:
    for iso in LANGUAGE_PRIMARY_SCRIPT.values():
        iso_id = ScriptISO(iso)
        assert tag_to_iso(iso_to_tag(iso_id)) == iso_id


_validate_script_identifier_invariants()

# ------------------------------------------------------------------
# Phase 5 — ISO-canonical derived views
# ------------------------------------------------------------------

# Canonical ISO15924 → display language
SCRIPT_ISO_TO_DISPLAY_LANGUAGE: dict[ScriptISO, str] = {
    tag_to_iso(tag): lang for tag, lang in SCRIPT_TO_DISPLAY_LANGUAGE.items()
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

# Canonical ISO15924 → sample text

_missing_sample_scripts = set(SCRIPT_SAMPLES) - set(SCRIPT_HUMAN_TO_ISO)
if _missing_sample_scripts:
    msg = f"Missing SCRIPT_HUMAN_TO_ISO entries for SCRIPT_SAMPLES: {sorted(_missing_sample_scripts)!r}"
    raise KeyError(msg)

_profile_script_names = {
    s for _lang, _profile in LANGUAGE_PROFILES.items() for s in _profile["scripts"]
}
_missing_profile_scripts = _profile_script_names - set(SCRIPT_HUMAN_TO_ISO)
if _missing_profile_scripts:
    msg = f"Missing SCRIPT_HUMAN_TO_ISO entries for LANGUAGE_PROFILES scripts: {sorted(_missing_profile_scripts)!r}"
    raise KeyError(msg)

SCRIPT_ISO_SAMPLES: dict[ScriptISO, str] = {
    SCRIPT_HUMAN_TO_ISO[name]: sample for name, sample in SCRIPT_SAMPLES.items()
}

# Canonical ISO15924 representation of language profiles
LANGUAGE_PROFILES_ISO: dict[str, dict[str, Any]] = {
    lang: {
        **profile,
        "scripts": [SCRIPT_HUMAN_TO_ISO[s] for s in profile["scripts"]],
    }
    for lang, profile in LANGUAGE_PROFILES.items()
}
