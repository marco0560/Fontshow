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
    ScriptISO("AGHB"): {
        "canonical_name": "Caucasian Albanian",
        "display_language": "xag",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Caucasian Albanian}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐔰𐔱𐔲𐔳𐔴𐔵𐔶𐔷𐔸𐔹𐔺𐔻𐔼𐔽𐔾𐔿𐕀𐕁𐕂𐕃𐕄𐕅𐕆𐕇",
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
    ScriptISO("AVST"): {
        "canonical_name": "Avestan",
        "display_language": "ae",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Avestan",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐬀𐬁𐬂𐬃𐬄𐬅𐬆𐬇𐬈𐬉𐬊𐬋𐬌𐬍𐬎𐬏𐬐𐬑𐬒𐬓𐬔𐬕𐬖𐬗",
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
    ScriptISO("BAMU"): {
        "canonical_name": "Bamum",
        "display_language": "bax",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Bamum",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꚠꚡꚢꚣꚤꚥꚦꚧꚨꚩꚪꚫꚬꚭꚮꚯꚰꚱꚲꚳꚴꚵꚶꚷ",
    },
    ScriptISO("BASS"): {
        "canonical_name": "Bassa Vah",
        "display_language": "bsq",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Bassa Vah}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𖫐𖫑𖫒𖫓𖫔𖫕𖫖𖫗𖫘𖫙𖫚𖫛𖫜𖫝𖫞𖫟𖫠𖫡𖫢𖫣𖫤𖫥𖫦𖫧",
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
    ScriptISO("BHKS"): {
        "canonical_name": "Bhaiksuki",
        "display_language": "pli",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Bhaiksuki",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑰀𑰁𑰂𑰃𑰄𑰅𑰆𑰇𑰈𑰉𑰊𑰋𑰌𑰍𑰎𑰏𑰐𑰑𑰒𑰓𑰔𑰕𑰖𑰗",
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
    ScriptISO("BYZM"): {
        "canonical_name": "Byzantine Music",
        "display_language": "zxx",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Byzantine Music}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𝀀𝀁𝀂𝀃𝀄𝀅𝀆𝀇𝀈𝀉𝀊𝀋𝀌𝀍𝀎𝀏𝀐𝀑𝀒𝀓𝀔𝀕𝀖𝀗",
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
    ScriptISO("CARI"): {
        "canonical_name": "Carian",
        "display_language": "xcr",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Carian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐊠𐊡𐊢𐊣𐊤𐊥𐊦𐊧𐊨𐊩𐊪𐊫𐊬𐊭𐊮𐊯𐊰𐊱𐊲𐊳𐊴𐊵𐊶𐊷",
    },
    ScriptISO("CHAK"): {
        "canonical_name": "Chakma",
        "display_language": "ccp",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Chakma",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑄃𑄄𑄅𑄆𑄇𑄈𑄉𑄊𑄋𑄌𑄍𑄎𑄏𑄐𑄑𑄒𑄓𑄔𑄕𑄖𑄗𑄘𑄙𑄚",
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
    ScriptISO("CHRS"): {
        "canonical_name": "Chorasmian",
        "display_language": "xco",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Chorasmian",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐾰𐾱𐾲𐾳𐾴𐾵𐾶𐾷𐾸𐾹𐾺𐾻𐾼𐾽𐾾𐾿𐿀𐿁𐿂𐿃𐿄𐿅𐿆𐿇",
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
    ScriptISO("CPMN"): {
        "canonical_name": "Cypro-Minoan",
        "display_language": "und",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Cypro-Minoan}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𒾐𒾑𒾒𒾓𒾔𒾕𒾖𒾗𒾘𒾙𒾚𒾛𒾜𒾝𒾞𒾟𒾠𒾡𒾢𒾣𒾤𒾥𒾦𒾧",
    },
    ScriptISO("CPRT"): {
        "canonical_name": "Cypriot Syllabary",
        "display_language": "ecy",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Cypriot Syllabary}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐠀𐠁𐠂𐠃𐠄𐠅𐠆𐠇𐠈𐠉𐠊𐠋𐠌𐠍𐠎𐠏𐠐𐠑𐠒𐠓𐠔𐠕𐠖𐠗",
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
    ScriptISO("GOTH"): {
        "canonical_name": "Gothic",
        "display_language": "got",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Gothic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐌰𐌱𐌲𐌳𐌴𐌵𐌶𐌷𐌸𐌹𐌺𐌻𐌼𐌽𐌾𐌿𐍀𐍁𐍂𐍃𐍄𐍅𐍆𐍇",
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
    ScriptISO("GONG"): {
        "canonical_name": "Gunjala Gondi",
        "display_language": "gon",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Gunjala Gondi}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑵠𑵡𑵢𑵣𑵤𑵥𑵦𑵧𑵨𑵩𑵪𑵫𑵬𑵭𑵮𑵯𑵰𑵱𑵲𑵳𑵴𑵵𑵶𑵷",
    },
    ScriptISO("GONM"): {
        "canonical_name": "Masaram Gondi",
        "display_language": "gon",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Masaram Gondi}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑴀𑴁𑴂𑴃𑴄𑴅𑴆𑴇𑴈𑴉𑴊𑴋𑴌𑴍𑴎𑴏𑴐𑴑𑴒𑴓𑴔𑴕𑴖𑴗",
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
    ScriptISO("KNDA"): {
        "canonical_name": "Kannada",
        "display_language": "kn",
        "polyglossia_language": "kannada",
        "fontspec_opts": "Script=Kannada",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞ",
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
    ScriptISO("HLUW"): {
        "canonical_name": "Anatolian Hieroglyphs",
        "display_language": "hlu",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Anatolian Hieroglyphs}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𔐀𔐁𔐂𔐃𔐄𔐅𔐆𔐇𔐈𔐉𔐊𔐋𔐌𔐍𔐎𔐏𔐐𔐑𔐒𔐓𔐔𔐕𔐖𔐗",
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
    ScriptISO("LIMB"): {
        "canonical_name": "Limbu",
        "display_language": "lif",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Limbu",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᤀᤁᤂᤃᤄᤅᤆᤇᤈᤉᤊᤋᤌᤍᤎᤏᤐᤑᤒᤓᤔᤕᤖᤗ",
    },
    ScriptISO("LISU"): {
        "canonical_name": "Lisu",
        "display_language": "lis",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Lisu",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꓐꓑꓒꓓꓔꓕꓖꓗꓘꓙꓚꓛꓜꓝꓞꓟꓠꓡꓢꓣꓤꓥꓦꓧ",
    },
    ScriptISO("MLYM"): {
        "canonical_name": "Malayalam",
        "display_language": "ml",
        "polyglossia_language": "malayalam",
        "fontspec_opts": "Script=Malayalam",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞ",
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
    ScriptISO("MEDF"): {
        "canonical_name": "Medefaidrin",
        "display_language": "dmf",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Medefaidrin",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𖹀𖹁𖹂𖹃𖹄𖹅𖹆𖹇𖹈𖹉𖹊𖹋𖹌𖹍𖹎𖹏𖹐𖹑𖹒𖹓𖹔𖹕𖹖𖹗",
    },
    ScriptISO("MEND"): {
        "canonical_name": "Mende Kikakui",
        "display_language": "men",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Mende Kikakui}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𞠀𞠁𞠂𞠃𞠄𞠅𞠆𞠇𞠈𞠉𞠊𞠋𞠌𞠍𞠎𞠏𞠐𞠑𞠒𞠓𞠔𞠕𞠖𞠗",
    },
    ScriptISO("MONG"): {
        "canonical_name": "Mongolian",
        "display_language": "mn",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Mongolian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᠠᠡᠢᠣᠤᠥᠦᠧᠨᠩᠪᠫᠬᠭᠮᠯᠰᠱᠲᠳᠴᠵᠶᠷ",
    },
    ScriptISO("MROO"): {
        "canonical_name": "Mro",
        "display_language": "mro",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Mro",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𖩠𖩡𖩢𖩣𖩤𖩥𖩦𖩧𖩨𖩩𖩪𖩫𖩬𖩭𖩮𖩯𖩰𖩱𖩲𖩳𖩴𖩵𖩶𖩷",
    },
    ScriptISO("MTEI"): {
        "canonical_name": "Meetei Mayek",
        "display_language": "mni",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Meitei Mayek}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꯀꯁꯂꯃꯄꯅꯆꯇꯈꯉꯊꯋꯌꯍꯎꯏꯐꯑꯒꯓꯔꯕꯖꯗ",
    },
    ScriptISO("NEWA"): {
        "canonical_name": "Newa",
        "display_language": "new",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Newa",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑐀𑐁𑐂𑐃𑐄𑐅𑐆𑐇𑐈𑐉𑐊𑐋𑐌𑐍𑐎𑐏𑐐𑐑𑐒𑐓𑐔𑐕𑐖𑐗",
    },
    ScriptISO("NKOO"): {
        "canonical_name": "NKo",
        "display_language": "nqo",
        "polyglossia_language": "",
        "fontspec_opts": "Script={N'Ko}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "߀߁߂߃߄߅߆߇߈߉ߊߋߌߍߎߏߐߑߒߓߔߕߖߗ",
    },
    ScriptISO("OSGE"): {
        "canonical_name": "Osage",
        "display_language": "osa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Osage",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐒰𐒱𐒲𐒳𐒴𐒵𐒶𐒷𐒸𐒹𐒺𐒻𐒼𐒽𐒾𐒿𐓀𐓁𐓂𐓃𐓄𐓅𐓆𐓇",
    },
    ScriptISO("PERM"): {
        "canonical_name": "Old Permic",
        "display_language": "kv",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Old Permic}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐍐𐍑𐍒𐍓𐍔𐍕𐍖𐍗𐍘𐍙𐍚𐍛𐍜𐍝𐍞𐍟𐍠𐍡𐍢𐍣𐍤𐍥𐍦𐍧",
    },
    ScriptISO("RJNG"): {
        "canonical_name": "Rejang",
        "display_language": "rej",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Rejang",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꤰꤱꤲꤳꤴꤵꤶꤷꤸꤹꤺꤻꤼꤽꤾꤿꥀꥁꥂꥃꥄꥅꥆꥇ",
    },
    ScriptISO("PHLP"): {
        "canonical_name": "Psalter Pahlavi",
        "display_language": "pal",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Psalter Pahlavi}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐮀𐮁𐮂𐮃𐮄𐮅𐮆𐮇𐮈𐮉𐮊𐮋𐮌𐮍𐮎𐮏𐮐𐮑𐮒𐮓𐮔𐮕𐮖𐮗",
    },
    ScriptISO("PHLI"): {
        "canonical_name": "Inscriptional Pahlavi",
        "display_language": "pal",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Inscriptional Pahlavi}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐭠𐭡𐭢𐭣𐭤𐭥𐭦𐭧𐭨𐭩𐭪𐭫𐭬𐭭𐭮𐭯𐭰𐭱𐭲𐭳𐭴𐭵𐭶𐭷",
    },
    ScriptISO("ORYA"): {
        "canonical_name": "Oriya",
        "display_language": "or",
        "polyglossia_language": "odia",
        "fontspec_opts": "Script=Oriya",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "ଅଆଇଈଉଊଋଏଐଓଔକଖଗଘଙଚଛଜଝଞ",
    },
    ScriptISO("SOGO"): {
        "canonical_name": "Old Sogdian",
        "display_language": "sog",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Old Sogdian}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐼀𐼁𐼂𐼃𐼄𐼅𐼆𐼇𐼈𐼉𐼊𐼋𐼌𐼍𐼎𐼏𐼐𐼑𐼒𐼓𐼔𐼕𐼖𐼗",
    },
    ScriptISO("SOGD"): {
        "canonical_name": "Sogdian",
        "display_language": "sog",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Sogdian",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐼰𐼱𐼲𐼳𐼴𐼵𐼶𐼷𐼸𐼹𐼺𐼻𐼼𐼽𐼾𐼿𐽀𐽁𐽂𐽃𐽄𐽅𐽆𐽇",
    },
    ScriptISO("SAUR"): {
        "canonical_name": "Saurashtra",
        "display_language": "saz",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Saurashtra",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꢂꢃꢄꢅꢆꢇꢈꢉꢊꢋꢌꢍꢎꢏꢐꢑꢒꢓꢔꢕꢖꢗꢘꢙ",
    },
    ScriptISO("SUND"): {
        "canonical_name": "Sundanese",
        "display_language": "su",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Sundanese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᮃᮄᮅᮆᮇᮈᮉᮊᮋᮌᮍᮎᮏᮐᮑᮒᮓᮔᮕᮖᮗᮘᮙᮚ",
    },
    ScriptISO("SYLO"): {
        "canonical_name": "Syloti Nagri",
        "display_language": "syl",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Syloti Nagri}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꠀꠁꠂꠃꠄꠅ꠆ꠇꠈꠉꠊꠋꠌꠍꠎꠏꠐꠑꠒꠓꠔꠕꠖꠗ",
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
    ScriptISO("TAGB"): {
        "canonical_name": "Tagbanwa",
        "display_language": "tbw",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tagbanwa",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᝠᝡᝢᝣᝤᝥᝦᝧᝨᝩᝪᝫᝬᝮᝯᝰᝲᝳ᝴",
    },
    ScriptISO("TGLG"): {
        "canonical_name": "Tagalog",
        "display_language": "tl",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tagalog",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᜀᜁᜂᜃᜄᜅᜆᜇᜈᜉᜊᜋᜌᜎᜏᜐᜑᜒᜓ᜔",
    },
    ScriptISO("LANA"): {
        "canonical_name": "Tai Tham",
        "display_language": "nod",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Tai Tham}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᨠᨡᨢᨣᨤᨥᨦᨧᨨᨩᨪᨫᨬᨭᨮᨯᨰᨱᨲᨳᨴᨵᨶᨷ",
    },
    ScriptISO("TAVT"): {
        "canonical_name": "Tai Viet",
        "display_language": "blt",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Tai Viet}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꪀꪁꪂꪃꪄꪅꪆꪇꪈꪉꪊꪋꪌꪍꪎꪏꪐꪑꪒꪓꪔꪕꪖꪗ",
    },
    ScriptISO("TALE"): {
        "canonical_name": "Tai Le",
        "display_language": "tdd",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Tai Le}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᥐᥑᥒᥓᥔᥕᥖᥗᥘᥙᥚᥛᥜᥝᥞᥟᥠᥡᥢᥣᥤᥥᥦᥧ",
    },
    ScriptISO("TFNG"): {
        "canonical_name": "Tifinagh",
        "display_language": "zgh",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tifinagh",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ⴰⴱⴲⴳⴴⴵⴶⴷⴸⴹⴺⴻⴼⴽⴾⴿⵀⵁⵂⵃⵄⵅⵆⵇ",
    },
    ScriptISO("TIRH"): {
        "canonical_name": "Tirhuta",
        "display_language": "mai",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tirhuta",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑒀𑒁𑒂𑒃𑒄𑒅𑒆𑒇𑒈𑒉𑒊𑒋𑒌𑒍𑒎𑒏𑒐𑒑𑒒𑒓𑒔𑒕𑒖𑒗",
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
    ScriptISO("TELU"): {
        "canonical_name": "Telugu",
        "display_language": "te",
        "polyglossia_language": "telugu",
        "fontspec_opts": "Script=Telugu",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞ",
    },
    ScriptISO("THAA"): {
        "canonical_name": "Thaana",
        "display_language": "dv",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Thaana",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "ހށނރބޅކއވމފދތލގޏސޑޒ",
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
    ScriptISO("SYRC"): {
        "canonical_name": "Syriac",
        "display_language": "syr",
        "polyglossia_language": "syriac",
        "fontspec_opts": "Script=Syriac",
        "rtl": True,
        "requires_polyglossia": True,
        "specimen": "ܐܒܓܕ ܗܘܙܚ ܛܝܟܠ ܡܢܣܥ",
    },
    ScriptISO("KALI"): {
        "canonical_name": "Kayah Li",
        "display_language": "kyu",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Kayah Li}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "꤀꤁꤂꤃꤄꤅꤆꤇꤈꤉ꤊꤋꤌꤍꤎꤏꤐꤑꤒꤓꤔꤕꤖꤗ",
    },
    ScriptISO("WARA"): {
        "canonical_name": "Warang Citi",
        "display_language": "hoc",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Warang Citi}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑢠𑢡𑢢𑢣𑢤𑢥𑢦𑢧𑢨𑢩𑢪𑢫𑢬𑢭𑢮𑢯𑢰𑢱𑢲𑢳𑢴𑢵𑢶𑢷",
    },
    ScriptISO("VAII"): {
        "canonical_name": "Vai",
        "display_language": "vai",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Vai",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꔀꔁꔂꔃꔄꔅꔆꔇꔈꔉꔊꔋꔌꔍꔎꔏꔐꔑꔒꔓꔔꔕꔖꔗ",
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
    "ae": {
        "canonical_name": "Avestan",
        "scripts": [ScriptISO("AVST")],
        "required_blocks": ["Avestan"],
        "optional_blocks": [],
        "sample": "𐬀𐬁𐬂𐬃𐬄𐬅𐬆𐬇𐬈𐬉𐬊𐬋𐬌𐬍𐬎𐬏𐬐𐬑𐬒𐬓𐬔𐬕𐬖𐬗",
    },
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
    "bax": {
        "canonical_name": "Bamum",
        "scripts": [ScriptISO("BAMU")],
        "required_blocks": ["Bamum"],
        "optional_blocks": [],
        "sample": "ꚠꚡꚢꚣꚤꚥꚦꚧꚨꚩꚪꚫꚬꚭꚮꚯꚰꚱꚲꚳꚴꚵꚶꚷ",
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
    "bsq": {
        "canonical_name": "Bassa",
        "scripts": [ScriptISO("BASS")],
        "required_blocks": ["Bassa Vah"],
        "optional_blocks": [],
        "sample": "𖫐𖫑𖫒𖫓𖫔𖫕𖫖𖫗𖫘𖫙𖫚𖫛𖫜𖫝𖫞𖫟𖫠𖫡𖫢𖫣𖫤𖫥𖫦𖫧",
    },
    "cop": {
        "canonical_name": "Coptic",
        "scripts": [ScriptISO("COPT")],
        "required_blocks": ["Coptic"],
        "optional_blocks": ["Coptic Epact Numbers"],
        "sample": "ϢϣϤϥϦϧϨϩϪϫϬϭϮϯⲀⲁⲂⲃⲄⲅⲆⲇⲈⲉ",
    },
    "ccp": {
        "canonical_name": "Chakma",
        "scripts": [ScriptISO("CHAK")],
        "required_blocks": ["Chakma"],
        "optional_blocks": [],
        "sample": "𑄃𑄄𑄅𑄆𑄇𑄈𑄉𑄊𑄋𑄌𑄍𑄎𑄏𑄐𑄑𑄒𑄓𑄔𑄕𑄖𑄗𑄘𑄙𑄚",
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
    "ecy": {
        "canonical_name": "Eteocypriot",
        "scripts": [ScriptISO("CPRT")],
        "required_blocks": ["Cypriot Syllabary"],
        "optional_blocks": [],
        "sample": "𐠀𐠁𐠂𐠃𐠄𐠅𐠆𐠇𐠈𐠉𐠊𐠋𐠌𐠍𐠎𐠏𐠐𐠑𐠒𐠓𐠔𐠕𐠖𐠗",
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
        "scripts": [ScriptISO("DIAK"), ScriptISO("THAA")],
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
    "got": {
        "canonical_name": "Gothic",
        "scripts": [ScriptISO("GOTH")],
        "required_blocks": ["Gothic"],
        "optional_blocks": [],
        "sample": "𐌰𐌱𐌲𐌳𐌴𐌵𐌶𐌷𐌸𐌹𐌺𐌻𐌼𐌽𐌾𐌿𐍀𐍁𐍂𐍃𐍄𐍅𐍆𐍇",
    },
    "hlu": {
        "canonical_name": "Hieroglyphic Luwian",
        "scripts": [ScriptISO("HLUW")],
        "required_blocks": ["Anatolian Hieroglyphs"],
        "optional_blocks": [],
        "sample": "𔐀𔐁𔐂𔐃𔐄𔐅𔐆𔐇𔐈𔐉𔐊𔐋𔐌𔐍𔐎𔐏𔐐𔐑𔐒𔐓𔐔𔐕𔐖𔐗",
    },
    "gon": {
        "canonical_name": "Gondi",
        "scripts": [ScriptISO("GONG"), ScriptISO("GONM")],
        "required_blocks": ["Gunjala Gondi"],
        "optional_blocks": ["Masaram Gondi"],
        "sample": "𑵠𑵡𑵢𑵣𑵤𑵥𑵦𑵧𑵨𑵩𑵪𑵫𑵬𑵭𑵮𑵯𑵰𑵱𑵲𑵳𑵴𑵵𑵶𑵷",
    },
    "hoc": {
        "canonical_name": "Ho",
        "scripts": [ScriptISO("WARA")],
        "required_blocks": ["Warang Citi"],
        "optional_blocks": [],
        "sample": "𑢠𑢡𑢢𑢣𑢤𑢥𑢦𑢧𑢨𑢩𑢪𑢫𑢬𑢭𑢮𑢯𑢰𑢱𑢲𑢳𑢴𑢵𑢶𑢷",
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
    "kn": {
        "canonical_name": "Kannada",
        "scripts": [ScriptISO("KNDA")],
        "required_blocks": ["Kannada"],
        "optional_blocks": ["Kannada Supplement"],
        "sample": "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞ",
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
    "lif": {
        "canonical_name": "Limbu",
        "scripts": [ScriptISO("LIMB")],
        "required_blocks": ["Limbu"],
        "optional_blocks": [],
        "sample": "ᤀᤁᤂᤃᤄᤅᤆᤇᤈᤉᤊᤋᤌᤍᤎᤏᤐᤑᤒᤓᤔᤕᤖᤗ",
    },
    "lis": {
        "canonical_name": "Lisu",
        "scripts": [ScriptISO("LISU")],
        "required_blocks": ["Lisu"],
        "optional_blocks": [],
        "sample": "ꓐꓑꓒꓓꓔꓕꓖꓗꓘꓙꓚꓛꓜꓝꓞꓟꓠꓡꓢꓣꓤꓥꓦꓧ",
    },
    "my": {
        "canonical_name": "Burmese",
        "scripts": [ScriptISO("MYMR")],
        "required_blocks": ["Myanmar"],
        "optional_blocks": ["Myanmar Extended-A"],
        "sample": "မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    },
    "dmf": {
        "canonical_name": "Medefaidrin",
        "scripts": [ScriptISO("MEDF")],
        "required_blocks": ["Medefaidrin"],
        "optional_blocks": [],
        "sample": "𖹀𖹁𖹂𖹃𖹄𖹅𖹆𖹇𖹈𖹉𖹊𖹋𖹌𖹍𖹎𖹏𖹐𖹑𖹒𖹓𖹔𖹕𖹖𖹗",
    },
    "men": {
        "canonical_name": "Mende",
        "scripts": [ScriptISO("MEND")],
        "required_blocks": ["Mende Kikakui"],
        "optional_blocks": [],
        "sample": "𞠀𞠁𞠂𞠃𞠄𞠅𞠆𞠇𞠈𞠉𞠊𞠋𞠌𞠍𞠎𞠏𞠐𞠑𞠒𞠓𞠔𞠕𞠖𞠗",
    },
    "mn": {
        "canonical_name": "Mongolian",
        "scripts": [ScriptISO("MONG")],
        "required_blocks": ["Mongolian"],
        "optional_blocks": [],
        "sample": "ᠠᠡᠢᠣᠤᠥᠦᠧᠨᠩᠪᠫᠬᠭᠮᠯᠰᠱᠲᠳᠴᠵᠶᠷ",
    },
    "mni": {
        "canonical_name": "Manipuri",
        "scripts": [ScriptISO("MTEI")],
        "required_blocks": ["Meetei Mayek"],
        "optional_blocks": ["Meetei Mayek Extensions"],
        "sample": "ꯀꯁꯂꯃꯄꯅꯆꯇꯈꯉꯊꯋꯌꯍꯎꯏꯐꯑꯒꯓꯔꯕꯖꯗ",
    },
    "new": {
        "canonical_name": "Newar",
        "scripts": [ScriptISO("NEWA")],
        "required_blocks": ["Newa"],
        "optional_blocks": [],
        "sample": "𑐀𑐁𑐂𑐃𑐄𑐅𑐆𑐇𑐈𑐉𑐊𑐋𑐌𑐍𑐎𑐏𑐐𑐑𑐒𑐓𑐔𑐕𑐖𑐗",
    },
    "nqo": {
        "canonical_name": "NKo",
        "scripts": [ScriptISO("NKOO")],
        "required_blocks": ["NKo"],
        "optional_blocks": [],
        "sample": "߀߁߂߃߄߅߆߇߈߉ߊߋߌߍߎߏߐߑߒߓߔߕߖߗ",
    },
    "osa": {
        "canonical_name": "Osage",
        "scripts": [ScriptISO("OSGE")],
        "required_blocks": ["Osage"],
        "optional_blocks": [],
        "sample": "𐒰𐒱𐒲𐒳𐒴𐒵𐒶𐒷𐒸𐒹𐒺𐒻𐒼𐒽𐒾𐒿𐓀𐓁𐓂𐓃𐓄𐓅𐓆𐓇",
    },
    "pli": {
        "canonical_name": "Pali",
        "scripts": [ScriptISO("BHKS")],
        "required_blocks": ["Bhaiksuki"],
        "optional_blocks": [],
        "sample": "𑰀𑰁𑰂𑰃𑰄𑰅𑰆𑰇𑰈𑰉𑰊𑰋𑰌𑰍𑰎𑰏𑰐𑰑𑰒𑰓𑰔𑰕𑰖𑰗",
    },
    "ml": {
        "canonical_name": "Malayalam",
        "scripts": [ScriptISO("MLYM")],
        "required_blocks": ["Malayalam"],
        "optional_blocks": ["Malayalam Supplement"],
        "sample": "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞ",
    },
    "mro": {
        "canonical_name": "Mro",
        "scripts": [ScriptISO("MROO")],
        "required_blocks": ["Mro"],
        "optional_blocks": [],
        "sample": "𖩠𖩡𖩢𖩣𖩤𖩥𖩦𖩧𖩨𖩩𖩪𖩫𖩬𖩭𖩮𖩯𖩰𖩱𖩲𖩳𖩴𖩵𖩶𖩷",
    },
    "kv": {
        "canonical_name": "Komi",
        "scripts": [ScriptISO("PERM"), ScriptISO("CYRL")],
        "required_blocks": ["Old Permic"],
        "optional_blocks": ["Cyrillic"],
        "sample": "𐍐𐍑𐍒𐍓𐍔𐍕𐍖𐍗𐍘𐍙𐍚𐍛𐍜𐍝𐍞𐍟𐍠𐍡𐍢𐍣𐍤𐍥𐍦𐍧",
    },
    "pal": {
        "canonical_name": "Middle Persian",
        "scripts": [ScriptISO("PHLP"), ScriptISO("PHLI")],
        "required_blocks": ["Psalter Pahlavi"],
        "optional_blocks": ["Inscriptional Pahlavi"],
        "sample": "𐮀𐮁𐮂𐮃𐮄𐮅𐮆𐮇𐮈𐮉𐮊𐮋𐮌𐮍𐮎𐮏𐮐𐮑𐮒𐮓𐮔𐮕𐮖𐮗",
    },
    "or": {
        "canonical_name": "Odia",
        "scripts": [ScriptISO("ORYA")],
        "required_blocks": ["Oriya"],
        "optional_blocks": [],
        "sample": "ଅଆଇଈଉଊଋଏଐଓଔକଖଗଘଙଚଛଜଝଞ",
    },
    "sog": {
        "canonical_name": "Sogdian",
        "scripts": [ScriptISO("SOGD"), ScriptISO("SOGO")],
        "required_blocks": ["Sogdian"],
        "optional_blocks": ["Old Sogdian"],
        "sample": "𐼰𐼱𐼲𐼳𐼴𐼵𐼶𐼷𐼸𐼹𐼺𐼻𐼼𐼽𐼾𐼿𐽀𐽁𐽂𐽃𐽄𐽅𐽆𐽇",
    },
    "su": {
        "canonical_name": "Sundanese",
        "scripts": [ScriptISO("SUND")],
        "required_blocks": ["Sundanese"],
        "optional_blocks": ["Sundanese Supplement"],
        "sample": "ᮃᮄᮅᮆᮇᮈᮉᮊᮋᮌᮍᮎᮏᮐᮑᮒᮓᮔᮕᮖᮗᮘᮙᮚ",
    },
    "syl": {
        "canonical_name": "Sylheti",
        "scripts": [ScriptISO("SYLO")],
        "required_blocks": ["Syloti Nagri"],
        "optional_blocks": [],
        "sample": "ꠀꠁꠂꠃꠄꠅ꠆ꠇꠈꠉꠊꠋꠌꠍꠎꠏꠐꠑꠒꠓꠔꠕꠖꠗ",
    },
    "syr": {
        "canonical_name": "Syriac",
        "scripts": [ScriptISO("SYRC")],
        "required_blocks": ["Syriac"],
        "optional_blocks": ["Syriac Supplement"],
        "sample": "ܐܒܓܕ ܗܘܙܚ ܛܝܟܠ ܡܢܣܥ",
    },
    "tl": {
        "canonical_name": "Tagalog",
        "scripts": [ScriptISO("TGLG"), ScriptISO("LATN")],
        "required_blocks": ["Tagalog"],
        "optional_blocks": ["Basic Latin"],
        "sample": "ᜀᜁᜂᜃᜄᜅᜆᜇᜈᜉᜊᜋᜌᜎᜏᜐᜑᜒᜓ᜔",
    },
    "und": {
        "canonical_name": "Undetermined",
        "scripts": [ScriptISO("CPMN")],
        "required_blocks": ["Cypro-Minoan"],
        "optional_blocks": [],
        "sample": "𒾐𒾑𒾒𒾓𒾔𒾕𒾖𒾗𒾘𒾙𒾚𒾛𒾜𒾝𒾞𒾟𒾠𒾡𒾢𒾣𒾤𒾥𒾦𒾧",
    },
    "tbw": {
        "canonical_name": "Tagbanwa",
        "scripts": [ScriptISO("TAGB")],
        "required_blocks": ["Tagbanwa"],
        "optional_blocks": [],
        "sample": "ᝠᝡᝢᝣᝤᝥᝦᝧᝨᝩᝪᝫᝬᝮᝯᝰᝲᝳ᝴",
    },
    "nod": {
        "canonical_name": "Northern Thai",
        "scripts": [ScriptISO("LANA")],
        "required_blocks": ["Tai Tham"],
        "optional_blocks": [],
        "sample": "ᨠᨡᨢᨣᨤᨥᨦᨧᨨᨩᨪᨫᨬᨭᨮᨯᨰᨱᨲᨳᨴᨵᨶᨷ",
    },
    "blt": {
        "canonical_name": "Tai Dam",
        "scripts": [ScriptISO("TAVT")],
        "required_blocks": ["Tai Viet"],
        "optional_blocks": [],
        "sample": "ꪀꪁꪂꪃꪄꪅꪆꪇꪈꪉꪊꪋꪌꪍꪎꪏꪐꪑꪒꪓꪔꪕꪖꪗ",
    },
    "zgh": {
        "canonical_name": "Standard Moroccan Tamazight",
        "scripts": [ScriptISO("TFNG")],
        "required_blocks": ["Tifinagh"],
        "optional_blocks": [],
        "sample": "ⴰⴱⴲⴳⴴⴵⴶⴷⴸⴹⴺⴻⴼⴽⴾⴿⵀⵁⵂⵃⵄⵅⵆⵇ",
    },
    "mai": {
        "canonical_name": "Maithili",
        "scripts": [ScriptISO("TIRH"), ScriptISO("DEVA")],
        "required_blocks": ["Tirhuta"],
        "optional_blocks": ["Devanagari"],
        "sample": "𑒀𑒁𑒂𑒃𑒄𑒅𑒆𑒇𑒈𑒉𑒊𑒋𑒌𑒍𑒎𑒏𑒐𑒑𑒒𑒓𑒔𑒕𑒖𑒗",
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
    "rej": {
        "canonical_name": "Rejang",
        "scripts": [ScriptISO("RJNG")],
        "required_blocks": ["Rejang"],
        "optional_blocks": [],
        "sample": "ꤰꤱꤲꤳꤴꤵꤶꤷꤸꤹꤺꤻꤼꤽꤾꤿꥀꥁꥂꥃꥄꥅꥆꥇ",
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
    "saz": {
        "canonical_name": "Saurashtra",
        "scripts": [ScriptISO("SAUR")],
        "required_blocks": ["Saurashtra"],
        "optional_blocks": [],
        "sample": "ꢂꢃꢄꢅꢆꢇꢈꢉꢊꢋꢌꢍꢎꢏꢐꢑꢒꢓꢔꢕꢖꢗꢘꢙ",
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
    "te": {
        "canonical_name": "Telugu",
        "scripts": [ScriptISO("TELU")],
        "required_blocks": ["Telugu"],
        "optional_blocks": [],
        "sample": "అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞ",
    },
    "kyu": {
        "canonical_name": "Western Kayah",
        "scripts": [ScriptISO("KALI")],
        "required_blocks": ["Kayah Li"],
        "optional_blocks": [],
        "sample": "꤀꤁꤂꤃꤄꤅꤆꤇꤈꤉ꤊꤋꤌꤍꤎꤏꤐꤑꤒꤓꤔꤕꤖꤗ",
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
    "tdd": {
        "canonical_name": "Tai Nua",
        "scripts": [ScriptISO("TALE")],
        "required_blocks": ["Tai Le"],
        "optional_blocks": [],
        "sample": "ᥐᥑᥒᥓᥔᥕᥖᥗᥘᥙᥚᥛᥜᥝᥞᥟᥠᥡᥢᥣᥤᥥᥦᥧ",
    },
    "zh": {
        "canonical_name": "Chinese",
        "scripts": [ScriptISO("HANI"), ScriptISO("BOPO")],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": ["Bopomofo", "Bopomofo Extended"],
        "sample": "天地玄黃 宇宙洪荒",
    },
    "vai": {
        "canonical_name": "Vai",
        "scripts": [ScriptISO("VAII")],
        "required_blocks": ["Vai"],
        "optional_blocks": [],
        "sample": "ꔀꔁꔂꔃꔄꔅꔆꔇꔈꔉꔊꔋꔌꔍꔎꔏꔐꔑꔒꔓꔔꔕꔖꔗ",
    },
    "xag": {
        "canonical_name": "Aghwan",
        "scripts": [ScriptISO("AGHB")],
        "required_blocks": ["Caucasian Albanian"],
        "optional_blocks": [],
        "sample": "𐔰𐔱𐔲𐔳𐔴𐔵𐔶𐔷𐔸𐔹𐔺𐔻𐔼𐔽𐔾𐔿𐕀𐕁𐕂𐕃𐕄𐕅𐕆𐕇",
    },
    "xco": {
        "canonical_name": "Chorasmian",
        "scripts": [ScriptISO("CHRS")],
        "required_blocks": ["Chorasmian"],
        "optional_blocks": [],
        "sample": "𐾰𐾱𐾲𐾳𐾴𐾵𐾶𐾷𐾸𐾹𐾺𐾻𐾼𐾽𐾾𐾿𐿀𐿁𐿂𐿃𐿄𐿅𐿆𐿇",
    },
    "xcr": {
        "canonical_name": "Carian",
        "scripts": [ScriptISO("CARI")],
        "required_blocks": ["Carian"],
        "optional_blocks": [],
        "sample": "𐊠𐊡𐊢𐊣𐊤𐊥𐊦𐊧𐊨𐊩𐊪𐊫𐊬𐊭𐊮𐊯𐊰𐊱𐊲𐊳𐊴𐊵𐊶𐊷",
    },
    "zxx": {
        "canonical_name": "No linguistic content",
        "scripts": [ScriptISO("BYZM")],
        "required_blocks": ["Byzantine Musical Symbols"],
        "optional_blocks": [],
        "sample": "𝀀𝀁𝀂𝀃𝀄𝀅𝀆𝀇𝀈𝀉𝀊𝀋𝀌𝀍𝀎𝀏𝀐𝀑𝀒𝀓𝀔𝀕𝀖𝀗",
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
    ScriptISO("GOTH"): 19,
    ScriptISO("GLAG"): 20,
    ScriptISO("GREK"): 21,
    ScriptISO("GRAN"): 22,
    ScriptISO("GUJR"): 23,
    ScriptISO("GURU"): 24,
    ScriptISO("HANG"): 25,
    ScriptISO("HANI"): 26,
    ScriptISO("HEBR"): 27,
    ScriptISO("HIRA"): 28,
    ScriptISO("JPAN"): 29,
    ScriptISO("KANA"): 30,
    ScriptISO("KHMR"): 31,
    ScriptISO("KNDA"): 32,
    ScriptISO("KTHI"): 33,
    ScriptISO("KALI"): 34,
    ScriptISO("LAOO"): 34,
    ScriptISO("LAOO"): 35,
    ScriptISO("LIMB"): 36,
    ScriptISO("LISU"): 37,
    ScriptISO("MLYM"): 38,
    ScriptISO("MYMR"): 39,
    ScriptISO("MEDF"): 40,
    ScriptISO("MEND"): 41,
    ScriptISO("MONG"): 42,
    ScriptISO("MTEI"): 43,
    ScriptISO("NEWA"): 44,
    ScriptISO("NKOO"): 45,
    ScriptISO("ORYA"): 46,
    ScriptISO("OSGE"): 47,
    ScriptISO("PHLI"): 48,
    ScriptISO("ROHG"): 49,
    ScriptISO("SINH"): 50,
    ScriptISO("SOGO"): 51,
    ScriptISO("SYRC"): 52,
    ScriptISO("TAML"): 53,
    ScriptISO("TELU"): 54,
    ScriptISO("THAA"): 55,
    ScriptISO("THAI"): 56,
    ScriptISO("YIII"): 57,
    ScriptISO("ADLM"): 58,
    ScriptISO("AHOM"): 59,
    ScriptISO("BALI"): 60,
    ScriptISO("BATK"): 61,
    ScriptISO("CHAM"): 62,
    ScriptISO("JAVA"): 63,
    ScriptISO("HANO"): 64,
    ScriptISO("LEPC"): 65,
    ScriptISO("MROO"): 66,
    ScriptISO("PERM"): 67,
    ScriptISO("PHLP"): 68,
    ScriptISO("SOGD"): 69,
    ScriptISO("TAGB"): 70,
    ScriptISO("TGLG"): 71,
    ScriptISO("LANA"): 72,
    ScriptISO("TAVT"): 73,
    ScriptISO("TFNG"): 74,
    ScriptISO("TIRH"): 75,
    ScriptISO("VAII"): 76,
    ScriptISO("BAMU"): 77,
    ScriptISO("CHAK"): 78,
    ScriptISO("GONG"): 79,
    ScriptISO("GONM"): 80,
    ScriptISO("RJNG"): 81,
    ScriptISO("SAUR"): 82,
    ScriptISO("SUND"): 83,
    ScriptISO("SYLO"): 84,
    ScriptISO("TALE"): 85,
    ScriptISO("WARA"): 86,
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
    ScriptISO("BAMU"): {
        "required_blocks": ["Bamum"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA6A0, 0xA6FF)],
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
    ScriptISO("CHAK"): {
        "required_blocks": ["Chakma"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("BENG"), ScriptISO("LATN"), ScriptISO("MYMR")],
        "preferred_over": [ScriptISO("BENG"), ScriptISO("LATN"), ScriptISO("MYMR")],
        "unicode_max_ranges": [(0x11100, 0x1114F)],
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
    ScriptISO("GOTH"): {
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x10330, 0x1034F)],
    },
    ScriptISO("GRAN"): {
        "required_blocks": ["Grantha"],
        "optional_blocks": ["Tamil", "Devanagari"],
        "unicode_max_ranges": [(0x11300, 0x1137F)],
    },
    ScriptISO("GONG"): {
        "required_blocks": ["Gunjala Gondi"],
        "optional_blocks": ["Masaram Gondi"],
        "suppresses": [ScriptISO("DEVA"), ScriptISO("LATN")],
        "preferred_over": [ScriptISO("GONM"), ScriptISO("DEVA"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0x11D60, 0x11DAF)],
    },
    ScriptISO("GONM"): {
        "required_blocks": ["Masaram Gondi"],
        "optional_blocks": ["Gunjala Gondi"],
        "suppresses": [ScriptISO("DEVA"), ScriptISO("LATN")],
        "preferred_over": [ScriptISO("GONG"), ScriptISO("DEVA"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0x11D00, 0x11D5F)],
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
    ScriptISO("KNDA"): {
        "optional_blocks": ["Kannada Supplement"],
        "suppresses": [ScriptISO("DEVA")],
        "preferred_over": [ScriptISO("DEVA")],
        "unicode_max_ranges": [(0x0C80, 0x0CFF)],
    },
    ScriptISO("KALI"): {
        "required_blocks": ["Kayah Li"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA900, 0xA92F)],
    },
    ScriptISO("LATN"): {
        "required_blocks": ["Basic Latin", "Latin"],
        "optional_blocks": [],
        "block_match": "prefix",
        "unicode_max_ranges": [(0x0000, 0x024F)],
    },
    ScriptISO("LIMB"): {
        "required_blocks": ["Limbu"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x1900, 0x194F)],
    },
    ScriptISO("LISU"): {
        "required_blocks": ["Lisu"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA4D0, 0xA4FF)],
    },
    ScriptISO("MLYM"): {
        "optional_blocks": ["Malayalam Supplement"],
        "unicode_max_ranges": [(0x0D00, 0x0D7F)],
    },
    ScriptISO("MEDF"): {
        "required_blocks": ["Medefaidrin"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x16E40, 0x16E9F)],
    },
    ScriptISO("MEND"): {
        "required_blocks": ["Mende Kikakui"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x1E800, 0x1E8DF)],
    },
    ScriptISO("MONG"): {
        "required_blocks": ["Mongolian"],
        "optional_blocks": ["Mongolian Supplement"],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x1800, 0x18AF)],
    },
    ScriptISO("MROO"): {
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x16A40, 0x16A6F)],
    },
    ScriptISO("MTEI"): {
        "required_blocks": ["Meetei Mayek"],
        "optional_blocks": ["Meetei Mayek Extensions"],
        "suppresses": [ScriptISO("LATN"), ScriptISO("BENG")],
        "preferred_over": [ScriptISO("LATN"), ScriptISO("BENG")],
        "unicode_max_ranges": [(0xABC0, 0xABFF)],
    },
    ScriptISO("NEWA"): {
        "required_blocks": ["Newa"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN"), ScriptISO("DEVA")],
        "preferred_over": [ScriptISO("LATN"), ScriptISO("DEVA")],
        "unicode_max_ranges": [(0x11400, 0x1147F)],
    },
    ScriptISO("NKOO"): {
        "required_blocks": ["NKo"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN"), ScriptISO("ARAB")],
        "preferred_over": [ScriptISO("LATN"), ScriptISO("ARAB")],
        "unicode_max_ranges": [(0x07C0, 0x07FF)],
    },
    ScriptISO("PERM"): {
        "optional_blocks": ["Cyrillic"],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x10350, 0x1037F)],
    },
    ScriptISO("PHLI"): {
        "required_blocks": ["Inscriptional Pahlavi"],
        "optional_blocks": ["Psalter Pahlavi"],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("PHLP"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0x10B60, 0x10B7F)],
    },
    ScriptISO("PHLP"): {
        "unicode_max_ranges": [(0x10B80, 0x10BAF)],
    },
    ScriptISO("RJNG"): {
        "required_blocks": ["Rejang"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA930, 0xA95F)],
    },
    ScriptISO("ORYA"): {
        "required_blocks": ["Oriya"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("DEVA")],
        "preferred_over": [ScriptISO("DEVA")],
        "unicode_max_ranges": [(0x0B00, 0x0B7F)],
    },
    ScriptISO("OSGE"): {
        "required_blocks": ["Osage"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x104B0, 0x104FF)],
    },
    ScriptISO("ROHG"): {
        "optional_blocks": ["Arabic"],
        "unicode_max_ranges": [(0x10D00, 0x10D3F)],
    },
    ScriptISO("SOGO"): {
        "required_blocks": ["Old Sogdian"],
        "optional_blocks": ["Sogdian"],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("SOGD"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0x10F00, 0x10F2F)],
    },
    ScriptISO("SAUR"): {
        "required_blocks": ["Saurashtra"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("DEVA"), ScriptISO("LATN")],
        "preferred_over": [ScriptISO("DEVA"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA880, 0xA8DF)],
    },
    ScriptISO("SOGD"): {
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x10F30, 0x10F6F)],
    },
    ScriptISO("SUND"): {
        "required_blocks": ["Sundanese"],
        "optional_blocks": ["Sundanese Supplement"],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x1B80, 0x1BBF)],
    },
    ScriptISO("SYLO"): {
        "required_blocks": ["Syloti Nagri"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("BENG"), ScriptISO("DEVA"), ScriptISO("LATN")],
        "preferred_over": [ScriptISO("BENG"), ScriptISO("DEVA"), ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA800, 0xA82F)],
    },
    ScriptISO("SYRC"): {
        "optional_blocks": ["Syriac Supplement"],
        "suppresses": [ScriptISO("ARAB")],
        "preferred_over": [ScriptISO("ARAB")],
        "unicode_max_ranges": [(0x0700, 0x074F)],
    },
    ScriptISO("TAGB"): {
        "suppresses": [ScriptISO("HANO")],
        "preferred_over": [ScriptISO("HANO")],
        "unicode_max_ranges": [(0x1760, 0x177F)],
    },
    ScriptISO("TGLG"): {
        "optional_blocks": ["Basic Latin"],
        "suppresses": [ScriptISO("HANO")],
        "preferred_over": [ScriptISO("HANO")],
        "unicode_max_ranges": [(0x1700, 0x171F)],
    },
    ScriptISO("LANA"): {
        "unicode_max_ranges": [(0x1A20, 0x1AAF)],
    },
    ScriptISO("TALE"): {
        "required_blocks": ["Tai Le"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN"), ScriptISO("MYMR")],
        "preferred_over": [ScriptISO("LATN"), ScriptISO("MYMR")],
        "unicode_max_ranges": [(0x1950, 0x197F)],
    },
    ScriptISO("TAVT"): {
        "unicode_max_ranges": [(0xAA80, 0xAADF)],
    },
    ScriptISO("TFNG"): {
        "unicode_max_ranges": [(0x2D30, 0x2D7F)],
    },
    ScriptISO("TIRH"): {
        "optional_blocks": ["Devanagari"],
        "suppresses": [ScriptISO("BENG"), ScriptISO("DEVA")],
        "preferred_over": [ScriptISO("BENG"), ScriptISO("DEVA")],
        "unicode_max_ranges": [(0x11480, 0x114DF)],
    },
    ScriptISO("TELU"): {
        "suppresses": [ScriptISO("DEVA")],
        "preferred_over": [ScriptISO("DEVA")],
        "unicode_max_ranges": [(0x0C00, 0x0C7F)],
    },
    ScriptISO("THAA"): {
        "required_blocks": ["Thaana"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("ARAB")],
        "preferred_over": [ScriptISO("ARAB")],
        "unicode_max_ranges": [(0x0780, 0x07BF)],
    },
    ScriptISO("VAII"): {
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0xA500, 0xA63F)],
    },
    ScriptISO("WARA"): {
        "required_blocks": ["Warang Citi"],
        "optional_blocks": [],
        "suppresses": [ScriptISO("LATN")],
        "preferred_over": [ScriptISO("LATN")],
        "unicode_max_ranges": [(0x118A0, 0x118FF)],
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
