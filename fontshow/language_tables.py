"""
Fontshow — language_tables
==========================

Authoritative ontology for scripts and languages used by Fontshow.

Design principles
-----------------
- ISO15924 script identifiers are the canonical keys.
- Language identifiers use ISO 639 codes.
- Samples are embedded directly in ontology entries.
- Tables are static and deterministic.
- Entries are sorted alphabetically for stable diffs.
"""

from __future__ import annotations

from typing import TypedDict

from fontshow.types import ScriptISO


class ScriptInfo(TypedDict):
    """
    Canonical description of a writing script.

    canonical_name
        Human readable script name.

    display_language
        Representative language used when a script-only specimen is required.

    polyglossia_language
        Polyglossia language identifier (if required).

    fontspec_opts
        Additional fontspec options required for rendering.

    rtl
        True for right-to-left scripts.

    requires_polyglossia
        Whether LuaLaTeX must enable Polyglossia for the script.

    specimen
        Canonical specimen sentence representative of the script.
    """

    canonical_name: str
    display_language: str
    polyglossia_language: str
    fontspec_opts: str
    rtl: bool
    requires_polyglossia: bool
    specimen: str | None


class LanguageInfo(TypedDict):
    """
    Canonical description of a language inference profile.

    scripts
        Scripts normally used to write the language.

    required_blocks
        Unicode blocks required for language detection.

    optional_blocks
        Blocks that increase confidence when present.

    sample
        Canonical language sample sentence.
    """

    scripts: list[ScriptISO]
    required_blocks: list[str]
    optional_blocks: list[str]
    sample: str | None


SCRIPT_INFO: dict[ScriptISO, ScriptInfo] = {
    ScriptISO("ARAB"): {
        "canonical_name": "Arabic",
        "display_language": "ar",
        "polyglossia_language": "arabic",
        "fontspec_opts": "Script=Arabic",
        "rtl": True,
        "requires_polyglossia": True,
        "specimen": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    },
    ScriptISO("ARMN"): {
        "canonical_name": "Armenian",
        "display_language": "hy",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    },
    ScriptISO("BENG"): {
        "canonical_name": "Bengali",
        "display_language": "bn",
        "polyglossia_language": "bengali",
        "fontspec_opts": "Script=Bengali",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "বাংলা ভাষা একটি সমৃদ্ধ ভাষা।",
    },
    ScriptISO("CHER"): {
        "canonical_name": "Cherokee",
        "display_language": "chr",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᎣᏏᏲ ᎠᏓᎨᏫᏍᏗ",
    },
    ScriptISO("CYRL"): {
        "canonical_name": "Cyrillic",
        "display_language": "ru",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Съешь же ещё этих мягких французских булок",
    },
    ScriptISO("DEVA"): {
        "canonical_name": "Devanagari",
        "display_language": "hi",
        "polyglossia_language": "hindi",
        "fontspec_opts": "Script=Devanagari",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "नमस्ते दुनिया",
    },
    ScriptISO("ETHI"): {
        "canonical_name": "Ethiopic",
        "display_language": "ti",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ሰላም እንታይ ከመይ ኢኻ",
    },
    ScriptISO("GEOR"): {
        "canonical_name": "Georgian",
        "display_language": "ka",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ქართული ტექსტის მაგალითი",
    },
    ScriptISO("GREK"): {
        "canonical_name": "Greek",
        "display_language": "el",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    },
    ScriptISO("HANG"): {
        "canonical_name": "Hangul",
        "display_language": "ko",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "키스의 고유조건은 입술끼리 만나야 한다",
    },
    ScriptISO("HANI"): {
        "canonical_name": "Han",
        "display_language": "zh",
        "polyglossia_language": "chinese",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "天地玄黃 宇宙洪荒",
    },
    ScriptISO("HEBR"): {
        "canonical_name": "Hebrew",
        "display_language": "he",
        "polyglossia_language": "hebrew",
        "fontspec_opts": "Script=Hebrew",
        "rtl": True,
        "requires_polyglossia": True,
        "specimen": "דג סקרן שט בים מאוכזב",
    },
    ScriptISO("HIRA"): {
        "canonical_name": "Hiragana",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "いろはにほへと ちりぬるを",
    },
    ScriptISO("KANA"): {
        "canonical_name": "Katakana",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "アイウエオ カキクケコ",
    },
    ScriptISO("KHMR"): {
        "canonical_name": "Khmer",
        "display_language": "km",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ភាសាខ្មែរ​ជា​ភាសា​ស្រស់ស្អាត",
    },
    ScriptISO("LAOO"): {
        "canonical_name": "Lao",
        "display_language": "lo",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ພາສາລາວເປັນພາສາທີ່ສວຍງາມ",
    },
    ScriptISO("LATN"): {
        "canonical_name": "Latin",
        "display_language": "en",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "The quick brown fox jumps over the lazy dog",
    },
    ScriptISO("MYMR"): {
        "canonical_name": "Myanmar",
        "display_language": "my",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    },
    ScriptISO("SINH"): {
        "canonical_name": "Sinhala",
        "display_language": "si",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "සිංහල භාෂාව ලස්සනයි",
    },
    ScriptISO("TAML"): {
        "canonical_name": "Tamil",
        "display_language": "ta",
        "polyglossia_language": "tamil",
        "fontspec_opts": "Script=Tamil",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "யாதும் ஊரே யாவரும் கேளிர்",
    },
    ScriptISO("THAI"): {
        "canonical_name": "Thai",
        "display_language": "th",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ภาษาไทยเป็นภาษาที่สวยงาม",
    },
    ScriptISO("YIII"): {
        "canonical_name": "Yi",
        "display_language": "ii",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꆈꌠꉙ ꉙꄜꐨ",
    },
}


LANGUAGE_INFO: dict[str, LanguageInfo] = {
    "am": {
        "scripts": [ScriptISO("ETHI")],
        "required_blocks": ["Ethiopic"],
        "optional_blocks": ["Ethiopic Supplement"],
        "sample": "ሰላም እንታይ ከመይ ኢኻ",
    },
    "ar": {
        "scripts": [ScriptISO("ARAB")],
        "required_blocks": ["Arabic"],
        "optional_blocks": ["Arabic Supplement"],
        "sample": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    },
    "chr": {
        "scripts": [ScriptISO("CHER")],
        "required_blocks": ["Cherokee"],
        "optional_blocks": ["Cherokee Supplement"],
        "sample": "ᎣᏏᏲ",
    },
    "de": {
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
        "sample": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
    },
    "el": {
        "scripts": [ScriptISO("GREK")],
        "required_blocks": ["Greek and Coptic"],
        "optional_blocks": [],
        "sample": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    },
    "en": {
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "The quick brown fox jumps over the lazy dog",
    },
    "es": {
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "El veloz murciélago hindú comía feliz cardillo y kiwi",
    },
    "fr": {
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "Portez ce vieux whisky au juge blond qui fume",
    },
    "ii": {
        "scripts": [ScriptISO("YIII")],
        "required_blocks": ["Yi Syllables"],
        "optional_blocks": [],
        "sample": "ꆈꌠꉙ ꉙꄜꐨ",
    },
    "it": {
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "Ma la volpe col suo balzo ha raggiunto il quieto Fido",
    },
    "ja": {
        "scripts": [ScriptISO("HIRA"), ScriptISO("KANA")],
        "required_blocks": ["Hiragana"],
        "optional_blocks": ["Katakana", "CJK Unified Ideographs"],
        "sample": "いろはにほへと ちりぬるを",
    },
    "ka": {
        "scripts": [ScriptISO("GEOR")],
        "required_blocks": ["Georgian"],
        "optional_blocks": [],
        "sample": "ქართული ტექსტის მაგალითი",
    },
    "lo": {
        "scripts": [ScriptISO("LAOO")],
        "required_blocks": ["Lao"],
        "optional_blocks": [],
        "sample": "ພາສາລາວເປັນພາສາທີ່ສວຍງາມ",
    },
    "my": {
        "scripts": [ScriptISO("MYMR")],
        "required_blocks": ["Myanmar"],
        "optional_blocks": ["Myanmar Extended-A"],
        "sample": "မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    },
    "pt": {
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "Luís argüia que o pingüim feliz tomava chá",
    },
    "ru": {
        "scripts": [ScriptISO("CYRL")],
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
        "sample": "Съешь же ещё этих мягких французских булок",
    },
    "ta": {
        "scripts": [ScriptISO("TAML")],
        "required_blocks": ["Tamil"],
        "optional_blocks": ["Tamil Supplement"],
        "sample": "யாதும் ஊரே யாவரும் கேளிர்",
    },
    "th": {
        "scripts": [ScriptISO("THAI")],
        "required_blocks": ["Thai"],
        "optional_blocks": [],
        "sample": "ภาษาไทยเป็นภาษาที่สวยงาม",
    },
    "zh": {
        "scripts": [ScriptISO("HANI")],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
        "sample": "天地玄黃 宇宙洪荒",
    },
}
