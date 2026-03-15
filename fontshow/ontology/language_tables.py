"""
Script and language ontology tables.

This module defines the authoritative ontology used by Fontshow to
describe writing systems and language inference profiles.

Responsibilities
----------------
- Define canonical script metadata keyed by ISO 15924 identifiers.
- Provide language inference profiles describing script usage.
- Supply representative specimen samples for scripts and languages.

Design principles
-----------------
Ontology tables are static and deterministic. Script identifiers follow
ISO 15924 conventions and language identifiers follow ISO 639 codes.
Entries are ordered deterministically to ensure stable repository diffs.

Architectural role
------------------
This module belongs to the **ontology subsystem** and provides the
linguistic knowledge base used by inventory analysis and catalog
generation.
"""

from __future__ import annotations

from typing import TypedDict

from fontshow.core.types import ScriptISO


class ScriptInfo(TypedDict):
    """
    Canonical description of a writing script.

    Parameters
    ----------
    canonical_name : str
        Human readable script name.
    display_language : str
        Representative language used when a script-only specimen is
        required.
    polyglossia_language : str
        Polyglossia language identifier, if required.
    fontspec_opts : str
        Additional ``fontspec`` options required for rendering.
    rtl : bool
        Whether the script is right-to-left.
    requires_polyglossia : bool
        Whether LuaLaTeX must enable Polyglossia for the script.
    specimen : str | None
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

    Parameters
    ----------
    canonical_name : str
        Human readable language name.
    scripts : list[ScriptISO]
        Scripts normally used to write the language.
    required_blocks : list[str]
        Unicode blocks required for language detection.
    optional_blocks : list[str]
        Blocks that increase confidence when present.
    sample : str | None
        Canonical language sample sentence.
    """

    canonical_name: str
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
        "fontspec_opts": "Script=Armenian",
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
        "fontspec_opts": "Script=Cherokee",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᎣᏏᏲ ᎠᏓᎨᏫᏍᏗ",
    },
    ScriptISO("CYRL"): {
        "canonical_name": "Cyrillic",
        "display_language": "ru",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Cyrillic",
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
        "fontspec_opts": "Script=Ethiopic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ሰላም እንታይ ከመይ ኢኻ",
    },
    ScriptISO("GEOR"): {
        "canonical_name": "Georgian",
        "display_language": "ka",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Georgian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ქართული ტექსტის მაგალითი",
    },
    ScriptISO("GREK"): {
        "canonical_name": "Greek",
        "display_language": "el",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Greek",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    },
    ScriptISO("HANG"): {
        "canonical_name": "Hangul",
        "display_language": "ko",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Hangul",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "키스의 고유조건은 입술끼리 만나야 한다",
    },
    ScriptISO("HANI"): {
        "canonical_name": "Han",
        "display_language": "zh",
        "polyglossia_language": "chinese",
        "fontspec_opts": "Script=CJK",
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
        "fontspec_opts": "Script=Kana",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "いろはにほへと ちりぬるを",
    },
    ScriptISO("KANA"): {
        "canonical_name": "Katakana",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "Script=Kana",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "アイウエオ カキクケコ",
    },
    ScriptISO("KHMR"): {
        "canonical_name": "Khmer",
        "display_language": "km",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Khmer",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ភាសាខ្មែរ​ជា​ភាសា​ស្រស់ស្អាត",
    },
    ScriptISO("LAOO"): {
        "canonical_name": "Lao",
        "display_language": "lo",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Lao",
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
        "fontspec_opts": "Script=Myanmar",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    },
    ScriptISO("SINH"): {
        "canonical_name": "Sinhala",
        "display_language": "si",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Sinhala",
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
        "fontspec_opts": "Script=Thai",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ภาษาไทยเป็นภาษาที่สวยงาม",
    },
    ScriptISO("YIII"): {
        "canonical_name": "Yi",
        "display_language": "ii",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Yi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꆈꌠꉙ ꉙꄜꐨ",
    },
}


LANGUAGE_INFO: dict[str, LanguageInfo] = {
    "am": {
        "canonical_name": "Amharic",
        "scripts": [ScriptISO("ETHI")],
        "required_blocks": ["Ethiopic"],
        "optional_blocks": ["Ethiopic Supplement"],
        "sample": "ሰላም እንታይ ከመይ ኢኻ",
    },
    "ar": {
        "canonical_name": "Arabic",
        "scripts": [ScriptISO("ARAB")],
        "required_blocks": ["Arabic"],
        "optional_blocks": ["Arabic Supplement"],
        "sample": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    },
    "bn": {
        "canonical_name": "Bengali",
        "scripts": [ScriptISO("BENG")],
        "required_blocks": ["Bengali"],
        "optional_blocks": [],
        "sample": "আমি বাংলায় গান গাই",
    },
    "chr": {
        "canonical_name": "Cherokee",
        "scripts": [ScriptISO("CHER")],
        "required_blocks": ["Cherokee"],
        "optional_blocks": ["Cherokee Supplement"],
        "sample": "ᎣᏏᏲ",
    },
    "de": {
        "canonical_name": "German",
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement", "Latin Extended-A"],
        "sample": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
    },
    "el": {
        "canonical_name": "Greek",
        "scripts": [ScriptISO("GREK")],
        "required_blocks": ["Greek and Coptic"],
        "optional_blocks": [],
        "sample": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    },
    "en": {
        "canonical_name": "English",
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "The quick brown fox jumps over the lazy dog",
    },
    "es": {
        "canonical_name": "Spanish",
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "El veloz murciélago hindú comía feliz cardillo y kiwi",
    },
    "fr": {
        "canonical_name": "French",
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "Portez ce vieux whisky au juge blond qui fume",
    },
    "he": {
        "canonical_name": "Hebrew",
        "scripts": [ScriptISO("HEBR")],
        "required_blocks": ["Hebrew"],
        "optional_blocks": [],
        "sample": "דג סקרן שט בים מאוכזב ולפתע מצא לו חברה",
    },
    "hi": {
        "canonical_name": "Hindi",
        "scripts": [ScriptISO("DEVA")],
        "required_blocks": ["Devanagari"],
        "optional_blocks": [],
        "sample": "सभी मनुष्य जन्म से स्वतंत्र और समान अधिकारों वाले हैं",
    },
    "hy": {
        "canonical_name": "Armenian",
        "scripts": [ScriptISO("ARMN")],
        "required_blocks": ["Armenian"],
        "optional_blocks": [],
        "sample": "Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    },
    "ii": {
        "canonical_name": "Nuosu (Yi)",
        "scripts": [ScriptISO("YIII")],
        "required_blocks": ["Yi Syllables"],
        "optional_blocks": [],
        "sample": "ꆈꌠꉙ ꉙꄜꐨ",
    },
    "it": {
        "canonical_name": "Italian",
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "Ma la volpe col suo balzo ha raggiunto il quieto Fido",
    },
    "ja": {
        "canonical_name": "Japanese",
        "scripts": [ScriptISO("HIRA"), ScriptISO("KANA")],
        "required_blocks": ["Hiragana"],
        "optional_blocks": ["Katakana", "CJK Unified Ideographs"],
        "sample": "いろはにほへと ちりぬるを",
    },
    "ka": {
        "canonical_name": "Georgian",
        "scripts": [ScriptISO("GEOR")],
        "required_blocks": ["Georgian"],
        "optional_blocks": [],
        "sample": "ქართული ტექსტის მაგალითი",
    },
    "km": {
        "canonical_name": "Khmer",
        "scripts": [ScriptISO("KHMR")],
        "required_blocks": ["Khmer"],
        "optional_blocks": [],
        "sample": "មនុស្សទាំងអស់កើតមកមានសេរីភាព",
    },
    "ko": {
        "canonical_name": "Korean",
        "scripts": [ScriptISO("HANG")],
        "required_blocks": ["Hangul Syllables"],
        "optional_blocks": [],
        "sample": "키스의 고유조건은 입술끼리 만나야 하고 특별한 기술은 필요치 않다",
    },
    "lo": {
        "canonical_name": "Lao",
        "scripts": [ScriptISO("LAOO")],
        "required_blocks": ["Lao"],
        "optional_blocks": [],
        "sample": "ພາສາລາວເປັນພາສາທີ່ສວຍງາມ",
    },
    "my": {
        "canonical_name": "Burmese",
        "scripts": [ScriptISO("MYMR")],
        "required_blocks": ["Myanmar"],
        "optional_blocks": ["Myanmar Extended-A"],
        "sample": "မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    },
    "pt": {
        "canonical_name": "Portuguese",
        "scripts": [ScriptISO("LATN")],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
        "sample": "Luís argüia que o pingüim feliz tomava chá",
    },
    "ru": {
        "canonical_name": "Russian",
        "scripts": [ScriptISO("CYRL")],
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
        "sample": "Съешь же ещё этих мягких французских булок",
    },
    "si": {
        "canonical_name": "Sinhala",
        "scripts": [ScriptISO("SINH")],
        "required_blocks": ["Sinhala"],
        "optional_blocks": [],
        "sample": "සියලු මිනිසුන් නිදහස්ව උපදින අතර",
    },
    "ta": {
        "canonical_name": "Tamil",
        "scripts": [ScriptISO("TAML")],
        "required_blocks": ["Tamil"],
        "optional_blocks": ["Tamil Supplement"],
        "sample": "யாதும் ஊரே யாவரும் கேளிர்",
    },
    "th": {
        "canonical_name": "Thai",
        "scripts": [ScriptISO("THAI")],
        "required_blocks": ["Thai"],
        "optional_blocks": [],
        "sample": "ภาษาไทยเป็นภาษาที่สวยงาม",
    },
    "ti": {
        "canonical_name": "Tigrinya",
        "scripts": [ScriptISO("ETHI")],
        "required_blocks": ["Ethiopic"],
        "optional_blocks": [],
        "sample": "ሰላም እንታይ ከመይ ኢኻ",
    },
    "zh": {
        "canonical_name": "Chinese",
        "scripts": [ScriptISO("HANI")],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
        "sample": "天地玄黃 宇宙洪荒",
    },
}
