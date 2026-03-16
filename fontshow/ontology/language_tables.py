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

from typing import Literal, NotRequired, TypedDict

from fontshow.core.types import ScriptISO
from fontshow.ontology.unicode_tables import UNICODE_BLOCK_RANGES


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
    required_blocks : list[str]
        Unicode blocks that provide primary evidence for script inference.
    optional_blocks : list[str]
        Unicode blocks that provide supporting evidence for script inference.
    suppresses : list[ScriptISO]
        Lower-priority scripts removed when this script is inferred strongly.
    inference_priority : int
        Deterministic tie-break priority used during script inference.
    unicode_max_ranges : list[tuple[int, int]]
        Fallback Unicode ranges used when only ``unicode.max`` is available.
    block_match : Literal["exact", "prefix"]
        Matching mode used for required and optional block patterns.
    collapse_group : str
        Optional group identifier used to collapse related scripts.
    preferred_over : list[ScriptISO]
        Scripts to demote when this script has equal or stronger evidence.
    """

    canonical_name: str
    display_language: str
    polyglossia_language: str
    fontspec_opts: str
    rtl: bool
    requires_polyglossia: bool
    specimen: str | None
    required_blocks: NotRequired[list[str]]
    optional_blocks: NotRequired[list[str]]
    suppresses: NotRequired[list[ScriptISO]]
    inference_priority: NotRequired[int]
    unicode_max_ranges: NotRequired[list[tuple[int, int]]]
    block_match: NotRequired[Literal["exact", "prefix"]]
    collapse_group: NotRequired[str]
    preferred_over: NotRequired[list[ScriptISO]]


class LanguageInfo(TypedDict):
    """
    Canonical description of a language inference profile.

    Parameters
    ----------
    canonical_name : str
        Human readable language name.
    scripts : list[ScriptISO]
        Scripts normally used to write the language.
    primary_script : ScriptISO
        Preferred canonical script used for representative fallback logic.
    required_blocks : list[str]
        Unicode blocks required for language detection.
    optional_blocks : list[str]
        Blocks that increase confidence when present.
    sample : str | None
        Canonical language sample sentence.
    """

    canonical_name: str
    scripts: list[ScriptISO]
    primary_script: NotRequired[ScriptISO]
    required_blocks: list[str]
    optional_blocks: list[str]
    sample: str | None


class ScriptInferenceOverride(TypedDict, total=False):
    """
    Partial override row used to backfill script inference metadata.

    Parameters
    ----------
    required_blocks : list[str]
        Override for primary script-evidence block patterns.
    optional_blocks : list[str]
        Override for supporting script-evidence block patterns.
    suppresses : list[ScriptISO]
        Override for hard script suppressions.
    inference_priority : int
        Override for deterministic script-priority ordering.
    unicode_max_ranges : list[tuple[int, int]]
        Override for ``unicode.max`` fallback ranges.
    block_match : Literal["exact", "prefix"]
        Override for block matching mode.
    collapse_group : str
        Override for optional script collapse grouping.
    preferred_over : list[ScriptISO]
        Override for soft script precedence relationships.
    """

    required_blocks: list[str]
    optional_blocks: list[str]
    suppresses: list[ScriptISO]
    inference_priority: int
    unicode_max_ranges: list[tuple[int, int]]
    block_match: Literal["exact", "prefix"]
    collapse_group: str
    preferred_over: list[ScriptISO]


SCRIPT_INFO: dict[ScriptISO, ScriptInfo] = {
    ScriptISO("ADLM"): {
        "canonical_name": "Adlam",
        "display_language": "ff",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Adlam",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𞤀𞤁𞤂𞤃𞤄𞤅𞤆𞤇𞤈𞤉𞤊𞤋𞤌𞤍𞤎𞤏𞤐𞤑𞤒𞤓𞤔𞤕𞤖𞤗",
    },
    ScriptISO("AHOM"): {
        "canonical_name": "Ahom",
        "display_language": "aho",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Ahom",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑜀𑜁𑜂𑜃𑜄𑜅𑜆𑜇𑜈𑜉𑜊𑜋𑜌𑜍𑜎𑜏𑜐𑜑𑜒𑜓𑜔𑜕𑜖𑜗",
    },
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
    ScriptISO("BALI"): {
        "canonical_name": "Balinese",
        "display_language": "ban",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Balinese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᬀᬁᬂᬃᬄᬅᬆᬇᬈᬉᬊᬋᬌᬍᬎᬏᬐᬑᬒᬓᬔᬕᬖᬗ",
    },
    ScriptISO("BATK"): {
        "canonical_name": "Batak",
        "display_language": "bbc",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Batak",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᯀᯁᯂᯃᯄᯅᯆᯇᯈᯉᯊᯋᯌᯍᯎᯏᯐᯑᯒᯓᯔᯕᯖᯗ",
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
    ScriptISO("BOPO"): {
        "canonical_name": "Bopomofo",
        "display_language": "zh",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Bopomofo",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄚㄛㄜ",
    },
    ScriptISO("BRAH"): {
        "canonical_name": "Brahmi",
        "display_language": "sa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Brahmi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑀀𑀁𑀂𑀃𑀄𑀅𑀆𑀇𑀈𑀉𑀊𑀋𑀌𑀍𑀎𑀏𑀐𑀑𑀒𑀓𑀔𑀕𑀖𑀗",
    },
    ScriptISO("BUGI"): {
        "canonical_name": "Buginese",
        "display_language": "bug",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Buginese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᨀᨁᨂᨃᨄᨅᨆᨇᨈᨉᨊᨋᨌᨍᨎᨏᨐᨑᨒᨓᨔᨕᨖꧏ᨞᨟",
    },
    ScriptISO("BUHD"): {
        "canonical_name": "Buhid",
        "display_language": "bku",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Buhid",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᝀᝁᝂᝃᝄᝅᝆᝇᝈᝉᝊᝋᝌᝍᝎᝏᝐᝑ᜵᜶",
    },
    ScriptISO("CANS"): {
        "canonical_name": "Canadian Syllabics",
        "display_language": "cr",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Canadian Syllabics",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "᐀ᐁᐂᐃᐄᐅᐆᐇᐈᐉᐊᐋᐌᐍᐎᐏᐐᐑᐒᐓᐔᐕᐖᐗ",
    },
    ScriptISO("CHAM"): {
        "canonical_name": "Cham",
        "display_language": "cjm",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Cham",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꨀꨁꨂꨃꨄꨅꨆꨇꨈꨉꨊꨋꨌꨍꨎꨏꨐꨑꨒꨓꨔꨕꨖꨗ",
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
    ScriptISO("COPT"): {
        "canonical_name": "Coptic",
        "display_language": "cop",
        "polyglossia_language": "coptic",
        "fontspec_opts": "Script=Coptic",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "ϢϣϤϥϦϧϨϩϪϫϬϭϮϯⲀⲁⲂⲃⲄⲅⲆⲇⲈⲉ",
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
    ScriptISO("DIAK"): {
        "canonical_name": "Dives Akuru",
        "display_language": "dv",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Dives Akuru}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑤀𑤂𑤄 𑤋𑤢𑤼",
    },
    ScriptISO("DSRT"): {
        "canonical_name": "Deseret",
        "display_language": "en",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Deseret",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐐀𐐁𐐂𐐃𐐄𐐅𐐆𐐇𐐈𐐉𐐊𐐋𐐌𐐍𐐎𐐏𐐐𐐑𐐒𐐓𐐔𐐕𐐖𐐗",
    },
    ScriptISO("DOGR"): {
        "canonical_name": "Dogra",
        "display_language": "doi",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Dogra",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑠖𑠮𑠝𑠳 𑠛𑠯𑠬𑠬𑠰",
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
    ScriptISO("ELBA"): {
        "canonical_name": "Elbasan",
        "display_language": "sq",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Elbasan",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐔀𐔁𐔂𐔃𐔄𐔅𐔆𐔇𐔈𐔉𐔊𐔋𐔌𐔍𐔎𐔏𐔐𐔑𐔒𐔓𐔔𐔕𐔖𐔗",
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
    ScriptISO("GLAG"): {
        "canonical_name": "Glagolitic",
        "display_language": "cu",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Glagolitic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ⰀⰁⰂⰃⰄⰅⰆⰇⰈⰉⰊⰋⰌⰍⰎⰏⰐⰑⰒⰓⰔⰕⰖⰗ",
    },
    ScriptISO("GRAN"): {
        "canonical_name": "Grantha",
        "display_language": "sa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Grantha",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑌀𑌁𑌂𑌃𑌅𑌆𑌇𑌈𑌉𑌊𑌋𑌌𑌏𑌐𑌓𑌔𑌕𑌖𑌗𑌘𑌙𑌚𑌛𑌜",
    },
    ScriptISO("GUJR"): {
        "canonical_name": "Gujarati",
        "display_language": "gu",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Gujarati",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ઁંઃઅઆઇઈઉઊઋઌઍએઐઑઓઔકખગઘઙચછ",
    },
    ScriptISO("GURU"): {
        "canonical_name": "Gurmukhi",
        "display_language": "pa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Gurmukhi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ਁਂਃਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟ",
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
    ScriptISO("HANO"): {
        "canonical_name": "Hanunoo",
        "display_language": "hnn",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Hanunoo",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᜠᜡᜢᜣᜤᜥᜦᜧᜨᜩᜪᜫᜬᜭᜮᜯᜰᜱᜲᜳ᜴",
    },
    ScriptISO("ROHG"): {
        "canonical_name": "Hanifi Rohingya",
        "display_language": "rhg",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Hanifi Rohingya}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐴀𐴁𐴂𐴃𐴄𐴅𐴆𐴇𐴈𐴉𐴊𐴋𐴌𐴍𐴎𐴏𐴐𐴑𐴒𐴓𐴔𐴕𐴖𐴗",
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
    ScriptISO("JPAN"): {
        "canonical_name": "Japanese",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "Script=Kana",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "いろはにほへと ちりぬるを",
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
    ScriptISO("JAVA"): {
        "canonical_name": "Javanese",
        "display_language": "jv",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Javanese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꦀꦁꦂꦃꦄꦅꦆꦇꦈꦉꦊꦋꦌꦍꦎꦏꦐꦑꦒꦓꦔꦕꦖꦗ",
    },
    ScriptISO("KTHI"): {
        "canonical_name": "Kaithi",
        "display_language": "bho",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Kaithi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑂀𑂁𑂂𑂃𑂄𑂅𑂆𑂇𑂈𑂉𑂊𑂋𑂌𑂍𑂎𑂏𑂐𑂑𑂒𑂓𑂔𑂕𑂖𑂗",
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
    ScriptISO("LEPC"): {
        "canonical_name": "Lepcha",
        "display_language": "lep",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Lepcha",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᰀᰁᰂᰃᰄᰅᰆᰇᰈᰉᰊᰋᰌᰍᰎᰏᰐᰑᰒᰓᰔᰕᰖᰗ",
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
    "aho": {
        "canonical_name": "Ahom",
        "scripts": [ScriptISO("AHOM")],
        "required_blocks": ["Ahom"],
        "optional_blocks": ["Ahom Supplement"],
        "sample": "𑜀𑜁𑜂𑜃𑜄𑜅𑜆𑜇𑜈𑜉𑜊𑜋𑜌𑜍𑜎𑜏𑜐𑜑𑜒𑜓𑜔𑜕𑜖𑜗",
    },
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
    "ban": {
        "canonical_name": "Balinese",
        "scripts": [ScriptISO("BALI")],
        "required_blocks": ["Balinese"],
        "optional_blocks": [],
        "sample": "ᬀᬁᬂᬃᬄᬅᬆᬇᬈᬉᬊᬋᬌᬍᬎᬏᬐᬑᬒᬓᬔᬕᬖᬗ",
    },
    "bbc": {
        "canonical_name": "Batak Toba",
        "scripts": [ScriptISO("BATK")],
        "required_blocks": ["Batak"],
        "optional_blocks": [],
        "sample": "ᯀᯁᯂᯃᯄᯅᯆᯇᯈᯉᯊᯋᯌᯍᯎᯏᯐᯑᯒᯓᯔᯕᯖᯗ",
    },
    "bho": {
        "canonical_name": "Bhojpuri",
        "scripts": [ScriptISO("KTHI"), ScriptISO("DEVA")],
        "required_blocks": ["Kaithi"],
        "optional_blocks": ["Devanagari"],
        "sample": "𑂀𑂁𑂂𑂃𑂄𑂅𑂆𑂇𑂈𑂉𑂊𑂋𑂌𑂍𑂎𑂏𑂐𑂑𑂒𑂓𑂔𑂕𑂖𑂗",
    },
    "bn": {
        "canonical_name": "Bengali",
        "scripts": [ScriptISO("BENG")],
        "required_blocks": ["Bengali"],
        "optional_blocks": [],
        "sample": "আমি বাংলায় গান গাই",
    },
    "bku": {
        "canonical_name": "Buhid",
        "scripts": [ScriptISO("BUHD")],
        "required_blocks": ["Buhid"],
        "optional_blocks": [],
        "sample": "ᝀᝁᝂᝃᝄᝅᝆᝇᝈᝉᝊᝋᝌᝍᝎᝏᝐᝑ᜵᜶",
    },
    "bug": {
        "canonical_name": "Buginese",
        "scripts": [ScriptISO("BUGI")],
        "required_blocks": ["Buginese"],
        "optional_blocks": [],
        "sample": "ᨀᨁᨂᨃᨄᨅᨆᨇᨈᨉᨊᨋᨌᨍᨎᨏᨐᨑᨒᨓᨔᨕᨖꧏ᨞᨟",
    },
    "cop": {
        "canonical_name": "Coptic",
        "scripts": [ScriptISO("COPT")],
        "required_blocks": ["Coptic"],
        "optional_blocks": ["Coptic Epact Numbers"],
        "sample": "ϢϣϤϥϦϧϨϩϪϫϬϭϮϯⲀⲁⲂⲃⲄⲅⲆⲇⲈⲉ",
    },
    "cr": {
        "canonical_name": "Cree",
        "scripts": [ScriptISO("CANS"), ScriptISO("LATN")],
        "required_blocks": ["Unified Canadian Aboriginal Syllabics"],
        "optional_blocks": ["Unified Canadian Aboriginal Syllabics Extended"],
        "sample": "᐀ᐁᐂᐃᐄᐅᐆᐇᐈᐉᐊᐋᐌᐍᐎᐏᐐᐑᐒᐓᐔᐕᐖᐗ",
    },
    "cu": {
        "canonical_name": "Church Slavic",
        "scripts": [ScriptISO("GLAG"), ScriptISO("CYRL")],
        "required_blocks": ["Glagolitic"],
        "optional_blocks": ["Glagolitic Supplement"],
        "sample": "ⰀⰁⰂⰃⰄⰅⰆⰇⰈⰉⰊⰋⰌⰍⰎⰏⰐⰑⰒⰓⰔⰕⰖⰗ",
    },
    "cjm": {
        "canonical_name": "Eastern Cham",
        "scripts": [ScriptISO("CHAM")],
        "required_blocks": ["Cham"],
        "optional_blocks": [],
        "sample": "ꨀꨁꨂꨃꨄꨅꨆꨇꨈꨉꨊꨋꨌꨍꨎꨏꨐꨑꨒꨓꨔꨕꨖꨗ",
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
    "doi": {
        "canonical_name": "Dogri",
        "scripts": [ScriptISO("DOGR"), ScriptISO("DEVA")],
        "required_blocks": ["Dogra"],
        "optional_blocks": ["Devanagari", "Devanagari Extended-A"],
        "sample": "𑠖𑠮𑠝𑠳 𑠛𑠯𑠬𑠬𑠰",
    },
    "dv": {
        "canonical_name": "Dhivehi",
        "scripts": [ScriptISO("DIAK")],
        "required_blocks": ["Dives Akuru"],
        "optional_blocks": ["Thaana"],
        "sample": "𑤀𑤂𑤄 𑤋𑤢𑤼",
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
        "scripts": [ScriptISO("LATN"), ScriptISO("DSRT")],
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
    "ff": {
        "canonical_name": "Fulah",
        "scripts": [ScriptISO("ADLM"), ScriptISO("LATN")],
        "required_blocks": ["Adlam"],
        "optional_blocks": ["Arabic"],
        "sample": "𞤀𞤁𞤂𞤃𞤄𞤅𞤆𞤇𞤈𞤉𞤊𞤋𞤌𞤍𞤎𞤏𞤐𞤑𞤒𞤓𞤔𞤕𞤖𞤗",
    },
    "gu": {
        "canonical_name": "Gujarati",
        "scripts": [ScriptISO("GUJR")],
        "required_blocks": ["Gujarati"],
        "optional_blocks": ["Gujarati Supplement"],
        "sample": "ઁંઃઅઆઇઈઉઊઋઌઍએઐઑઓઔકખગઘઙચછ",
    },
    "hnn": {
        "canonical_name": "Hanunoo",
        "scripts": [ScriptISO("HANO")],
        "required_blocks": ["Hanunoo"],
        "optional_blocks": [],
        "sample": "ᜠᜡᜢᜣᜤᜥᜦᜧᜨᜩᜪᜫᜬᜭᜮᜯᜰᜱᜲᜳ᜴",
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
        "scripts": [ScriptISO("JPAN"), ScriptISO("HIRA"), ScriptISO("KANA")],
        "required_blocks": ["Hiragana"],
        "optional_blocks": ["Katakana", "CJK Unified Ideographs"],
        "sample": "いろはにほへと ちりぬるを",
    },
    "jv": {
        "canonical_name": "Javanese",
        "scripts": [ScriptISO("JAVA")],
        "required_blocks": ["Javanese"],
        "optional_blocks": [],
        "sample": "ꦀꦁꦂꦃꦄꦅꦆꦇꦈꦉꦊꦋꦌꦍꦎꦏꦐꦑꦒꦓꦔꦕꦖꦗ",
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
    "lep": {
        "canonical_name": "Lepcha",
        "scripts": [ScriptISO("LEPC")],
        "required_blocks": ["Lepcha"],
        "optional_blocks": [],
        "sample": "ᰀᰁᰂᰃᰄᰅᰆᰇᰈᰉᰊᰋᰌᰍᰎᰏᰐᰑᰒᰓᰔᰕᰖᰗ",
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
    "pa": {
        "canonical_name": "Panjabi",
        "scripts": [ScriptISO("GURU")],
        "required_blocks": ["Gurmukhi"],
        "optional_blocks": ["Gurmukhi Extensions"],
        "sample": "ਁਂਃਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟ",
    },
    "rhg": {
        "canonical_name": "Rohingya",
        "scripts": [ScriptISO("ROHG"), ScriptISO("ARAB")],
        "required_blocks": ["Hanifi Rohingya"],
        "optional_blocks": ["Arabic"],
        "sample": "𐴀𐴁𐴂𐴃𐴄𐴅𐴆𐴇𐴈𐴉𐴊𐴋𐴌𐴍𐴎𐴏𐴐𐴑𐴒𐴓𐴔𐴕𐴖𐴗",
    },
    "ru": {
        "canonical_name": "Russian",
        "scripts": [ScriptISO("CYRL")],
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
        "sample": "Съешь же ещё этих мягких французских булок",
    },
    "sa": {
        "canonical_name": "Sanskrit",
        "scripts": [ScriptISO("BRAH"), ScriptISO("GRAN"), ScriptISO("DEVA")],
        "required_blocks": ["Brahmi"],
        "optional_blocks": ["Grantha", "Devanagari"],
        "sample": "𑀀𑀁𑀂𑀃𑀄𑀅𑀆𑀇𑀈𑀉𑀊𑀋𑀌𑀍𑀎𑀏𑀐𑀑𑀒𑀓𑀔𑀕𑀖𑀗",
    },
    "si": {
        "canonical_name": "Sinhala",
        "scripts": [ScriptISO("SINH")],
        "required_blocks": ["Sinhala"],
        "optional_blocks": [],
        "sample": "සියලු මිනිසුන් නිදහස්ව උපදින අතර",
    },
    "sq": {
        "canonical_name": "Albanian",
        "scripts": [ScriptISO("ELBA"), ScriptISO("LATN")],
        "required_blocks": ["Elbasan"],
        "optional_blocks": ["Basic Latin"],
        "sample": "𐔀𐔁𐔂𐔃𐔄𐔅𐔆𐔇𐔈𐔉𐔊𐔋𐔌𐔍𐔎𐔏𐔐𐔑𐔒𐔓𐔔𐔕𐔖𐔗",
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
        "scripts": [ScriptISO("HANI"), ScriptISO("BOPO")],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": ["Bopomofo", "Bopomofo Extended"],
        "sample": "天地玄黃 宇宙洪荒",
    },
}


_SCRIPT_INFERENCE_PRIORITY: dict[ScriptISO, int] = {
    ScriptISO("LATN"): 0,
    ScriptISO("ARAB"): 1,
    ScriptISO("ARMN"): 2,
    ScriptISO("BENG"): 3,
    ScriptISO("BOPO"): 4,
    ScriptISO("BRAH"): 5,
    ScriptISO("BUGI"): 6,
    ScriptISO("BUHD"): 7,
    ScriptISO("CANS"): 8,
    ScriptISO("CHER"): 9,
    ScriptISO("COPT"): 10,
    ScriptISO("CYRL"): 11,
    ScriptISO("DEVA"): 12,
    ScriptISO("DIAK"): 13,
    ScriptISO("DOGR"): 14,
    ScriptISO("DSRT"): 15,
    ScriptISO("ELBA"): 16,
    ScriptISO("ETHI"): 17,
    ScriptISO("GEOR"): 18,
    ScriptISO("GLAG"): 19,
    ScriptISO("GREK"): 20,
    ScriptISO("GRAN"): 21,
    ScriptISO("GUJR"): 22,
    ScriptISO("GURU"): 23,
    ScriptISO("HANG"): 24,
    ScriptISO("HANI"): 25,
    ScriptISO("HEBR"): 26,
    ScriptISO("HIRA"): 27,
    ScriptISO("JPAN"): 28,
    ScriptISO("KANA"): 29,
    ScriptISO("KHMR"): 30,
    ScriptISO("KTHI"): 31,
    ScriptISO("LAOO"): 32,
    ScriptISO("MYMR"): 33,
    ScriptISO("ROHG"): 34,
    ScriptISO("SINH"): 35,
    ScriptISO("TAML"): 36,
    ScriptISO("THAI"): 37,
    ScriptISO("YIII"): 38,
    ScriptISO("ADLM"): 39,
    ScriptISO("AHOM"): 40,
    ScriptISO("BALI"): 41,
    ScriptISO("BATK"): 42,
    ScriptISO("CHAM"): 43,
    ScriptISO("JAVA"): 44,
    ScriptISO("HANO"): 45,
    ScriptISO("LEPC"): 46,
}

_SCRIPT_INFERENCE_OVERRIDES: dict[ScriptISO, ScriptInferenceOverride] = {
    ScriptISO("ADLM"): {
        "optional_blocks": ["Arabic"],
        "preferred_over": [ScriptISO("ARAB"), ScriptISO("LATN")],
    },
    ScriptISO("BOPO"): {
        "required_blocks": ["Bopomofo"],
        "optional_blocks": ["Bopomofo Extended"],
        "block_match": "exact",
        "unicode_max_ranges": [(0x3100, 0x312F), (0x31A0, 0x31BF)],
    },
    ScriptISO("BRAH"): {
        "optional_blocks": ["Grantha", "Devanagari"],
        "preferred_over": [ScriptISO("DEVA"), ScriptISO("GRAN")],
        "unicode_max_ranges": [(0x11000, 0x1107F)],
    },
    ScriptISO("CANS"): {
        "optional_blocks": [
            "Unified Canadian Aboriginal Syllabics Extended",
            "Unified Canadian Aboriginal Syllabics Extended-A",
        ],
        "preferred_over": [ScriptISO("LATN")],
    },
    ScriptISO("COPT"): {
        "unicode_max_ranges": [(0x2C80, 0x2CFF), (0x102E0, 0x102FF)],
    },
    ScriptISO("DSRT"): {
        "required_blocks": ["Deseret"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x10400, 0x1044F)],
    },
    ScriptISO("DOGR"): {
        "optional_blocks": ["Devanagari", "Devanagari Extended-A"],
        "suppresses": [ScriptISO("DEVA"), ScriptISO("LATN")],
        "preferred_over": [ScriptISO("DEVA"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0x11800, 0x1184F)],
    },
    ScriptISO("DIAK"): {
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x11900, 0x1195F)],
    },
    ScriptISO("ELBA"): {
        "optional_blocks": ["Greek and Coptic"],
        "unicode_max_ranges": [(0x10500, 0x1052F)],
    },
    ScriptISO("GLAG"): {
        "optional_blocks": ["Glagolitic Supplement", "Cyrillic"],
        "unicode_max_ranges": [(0x2C00, 0x2C5F), (0x1E000, 0x1E02F)],
    },
    ScriptISO("GRAN"): {
        "required_blocks": ["Grantha"],
        "optional_blocks": ["Tamil", "Devanagari"],
        "unicode_max_ranges": [(0x11300, 0x1137F)],
    },
    ScriptISO("HANG"): {
        "required_blocks": ["Hangul"],
        "optional_blocks": [],
        "block_match": "prefix",
        "suppresses": [ScriptISO("HANI")],
        "preferred_over": [ScriptISO("HANI")],
    },
    ScriptISO("HANI"): {
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [
            "CJK Compatibility Ideographs",
            "CJK Compatibility Ideographs Supplement",
        ],
        "block_match": "prefix",
        "collapse_group": "JPAN",
    },
    ScriptISO("HIRA"): {
        "required_blocks": ["Hiragana"],
        "optional_blocks": ["Katakana", "CJK Unified Ideographs"],
        "collapse_group": "JPAN",
    },
    ScriptISO("JPAN"): {
        "required_blocks": ["Hiragana", "Katakana", "Kana"],
        "optional_blocks": ["CJK Unified Ideographs"],
        "suppresses": [ScriptISO("HANI"), ScriptISO("HIRA"), ScriptISO("KANA")],
        "preferred_over": [ScriptISO("HANI"), ScriptISO("HIRA"), ScriptISO("KANA")],
        "block_match": "prefix",
        "collapse_group": "JPAN",
    },
    ScriptISO("KANA"): {
        "required_blocks": ["Katakana", "Kana"],
        "optional_blocks": ["Hiragana", "CJK Unified Ideographs"],
        "block_match": "prefix",
        "collapse_group": "JPAN",
    },
    ScriptISO("KTHI"): {
        "optional_blocks": ["Devanagari"],
        "unicode_max_ranges": [(0x11080, 0x110CF)],
    },
    ScriptISO("LATN"): {
        "required_blocks": ["Basic Latin", "Latin"],
        "optional_blocks": [],
        "block_match": "prefix",
        "unicode_max_ranges": [(0x0000, 0x024F)],
    },
    ScriptISO("ROHG"): {
        "optional_blocks": ["Arabic"],
        "unicode_max_ranges": [(0x10D00, 0x10D3F)],
    },
}


def _finalize_language_info() -> None:
    """
    Normalize language ontology rows with explicit primary-script metadata.

    Returns
    -------
    None
    """
    for info in LANGUAGE_INFO.values():
        scripts = list(info.get("scripts", []))
        if not scripts:
            continue
        info["primary_script"] = scripts[0]


def _derive_script_default_blocks(script_iso: ScriptISO) -> tuple[list[str], list[str]]:
    """
    Derive default inference blocks for a script from its display language.

    Parameters
    ----------
    script_iso : ScriptISO
        Script whose representative language should be inspected.

    Returns
    -------
    tuple[list[str], list[str]]
        Required and optional Unicode blocks used as default inference
        evidence for the script.
    """
    info = SCRIPT_INFO[script_iso]
    lang_info = LANGUAGE_INFO[info["display_language"]]
    primary_script = lang_info["primary_script"]
    required = list(lang_info.get("required_blocks", []))
    optional = list(lang_info.get("optional_blocks", []))

    if primary_script == script_iso:
        return required, optional

    return required, optional


def _derive_unicode_max_ranges(
    required_blocks: list[str],
    match_mode: str,
) -> list[tuple[int, int]]:
    """
    Derive fallback Unicode ranges from configured required block evidence.

    Parameters
    ----------
    required_blocks : list[str]
        Required block patterns stored in the script ontology.
    match_mode : str
        Block matching mode used by the script entry.

    Returns
    -------
    list[tuple[int, int]]
        Unicode ranges suitable for ``unicode.max`` fallback inference.
    """
    ranges: list[tuple[int, int]] = []

    for pattern in required_blocks:
        for block_name, block_range in UNICODE_BLOCK_RANGES.items():
            if match_mode == "prefix" and block_name.startswith(pattern):
                ranges.append(block_range)
            if match_mode == "exact" and block_name == pattern:
                ranges.append(block_range)

    return ranges


def _finalize_script_info() -> None:
    """
    Normalize script ontology rows with explicit inference metadata.

    Returns
    -------
    None
    """
    for index, script_iso in enumerate(SCRIPT_INFO):
        info = SCRIPT_INFO[script_iso]
        required_blocks, optional_blocks = _derive_script_default_blocks(script_iso)
        overrides: ScriptInferenceOverride = _SCRIPT_INFERENCE_OVERRIDES.get(
            script_iso,
            {},
        )

        info["required_blocks"] = list(
            overrides.get("required_blocks", required_blocks)
        )
        info["optional_blocks"] = list(
            overrides.get("optional_blocks", optional_blocks)
        )
        info["suppresses"] = list(overrides.get("suppresses", []))
        info["inference_priority"] = int(
            overrides.get(
                "inference_priority",
                _SCRIPT_INFERENCE_PRIORITY.get(script_iso, index + 100),
            )
        )
        info["block_match"] = overrides.get("block_match", "exact")
        info["unicode_max_ranges"] = list(
            overrides.get(
                "unicode_max_ranges",
                _derive_unicode_max_ranges(
                    info["required_blocks"],
                    info["block_match"],
                ),
            )
        )
        info["collapse_group"] = str(overrides.get("collapse_group", ""))
        info["preferred_over"] = list(overrides.get("preferred_over", []))


_finalize_language_info()
_finalize_script_info()
