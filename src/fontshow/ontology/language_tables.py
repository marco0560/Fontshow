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

import unicodedata
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
    description : str
        Short description (1-3 lines) of the script, including origin,
        usage, and notable characteristics.
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
    description: str
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


def _script_fontspec_opts(canonical_name: str) -> str:
    """
    Build deterministic fontspec script options for ontology-only rows.

    Parameters
    ----------
    canonical_name : str
        Canonical script name to expose through ``fontspec``.

    Returns
    -------
    str
        Fontspec ``Script`` option using braces when the name is not a
        single word.
    """
    if canonical_name.replace("-", "").isalpha():
        return f"Script={canonical_name}"
    return f"Script={{{canonical_name}}}"


def _script_specimen_from_blocks(block_names: list[str]) -> str:
    """
    Build a deterministic script specimen from Unicode block ranges.

    Parameters
    ----------
    block_names : list[str]
        Unicode block names used as primary evidence for the script.

    Returns
    -------
    str
        First printable non-combining characters found in the configured
        ranges, capped to keep catalog rows compact.
    """
    specimen: list[str] = []

    for block_name in block_names:
        start, end = UNICODE_BLOCK_RANGES[block_name]
        for codepoint in range(start, end + 1):
            character = chr(codepoint)
            category = unicodedata.category(character)
            if category[0] in {"C", "M"}:
                continue
            specimen.append(character)
            if len(specimen) >= 24:
                return "".join(specimen)

    return "".join(specimen)


def _script_rtl_from_specimen(specimen: str) -> bool:
    """
    Infer script direction from Unicode bidirectional classes.

    Parameters
    ----------
    specimen : str
        Representative script specimen.

    Returns
    -------
    bool
        True when the specimen contains right-to-left bidirectional
        evidence.
    """
    return any(
        unicodedata.bidirectional(character) in {"R", "AL"} for character in specimen
    )


def _script_unicode_max_ranges(block_names: list[str]) -> list[tuple[int, int]]:
    """
    Resolve Unicode block names to deterministic range tuples.

    Parameters
    ----------
    block_names : list[str]
        Unicode block names configured for script inference.

    Returns
    -------
    list[tuple[int, int]]
        Unicode ranges in the same order as ``block_names``.
    """
    return [UNICODE_BLOCK_RANGES[block_name] for block_name in block_names]


def _make_dedicated_script_info(
    canonical_name: str,
    display_language: str,
    required_blocks: list[str],
    *,
    optional_blocks: list[str] | None = None,
    inference_priority: int,
) -> ScriptInfo:
    """
    Create a fully populated ontology row for block-dedicated scripts.

    Parameters
    ----------
    canonical_name : str
        Human-readable script name.
    display_language : str
        Representative language code used for rendering fallback.
    required_blocks : list[str]
        Unicode blocks that identify this script.
    optional_blocks : list[str] | None, optional
        Additional Unicode blocks that support inference.
    inference_priority : int
        Deterministic priority used to order inference ties.

    Returns
    -------
    ScriptInfo
        Fully populated script ontology row.
    """
    optional = list(optional_blocks or [])
    specimen = _script_specimen_from_blocks(required_blocks)
    return {
        "canonical_name": canonical_name,
        "description": (
            f"{canonical_name} is a dedicated script ontology entry used by "
            "Fontshow for catalog labeling, Unicode-block script inference, "
            f"and deterministic specimen rendering from the "
            f"{', '.join(required_blocks)} block evidence."
        ),
        "display_language": display_language,
        "polyglossia_language": "",
        "fontspec_opts": _script_fontspec_opts(canonical_name),
        "rtl": _script_rtl_from_specimen(specimen),
        "requires_polyglossia": False,
        "specimen": specimen,
        "required_blocks": list(required_blocks),
        "optional_blocks": optional,
        "suppresses": [ScriptISO("LATN")],
        "inference_priority": inference_priority,
        "unicode_max_ranges": _script_unicode_max_ranges(required_blocks + optional),
        "block_match": "exact",
        "collapse_group": "",
        "preferred_over": [ScriptISO("LATN")],
    }


class LanguageInfo(TypedDict):
    """
    Canonical description of a language inference profile.

    Parameters
    ----------
    canonical_name : str
        Human readable language name.
    description : str
        Short description (1-3 lines) of the language, including
        geographic distribution, linguistic family, and writing system.
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
    description: str
    scripts: list[ScriptISO]
    primary_script: ScriptISO
    required_blocks: list[str]
    optional_blocks: list[str]
    sample: str | None


def _make_script_language_info(
    canonical_name: str,
    description: str,
    scripts: list[ScriptISO],
    required_blocks: list[str],
    *,
    optional_blocks: list[str] | None = None,
) -> LanguageInfo:
    """
    Create a fully populated language row backed by script specimens.

    Parameters
    ----------
    canonical_name : str
        Human-readable language name.
    description : str
        Short language description used in diagnostics and ontology dumps.
    scripts : list[ScriptISO]
        Scripts associated with the language profile.
    required_blocks : list[str]
        Unicode blocks used as primary language evidence.
    optional_blocks : list[str] | None, optional
        Additional Unicode blocks that support language inference.

    Returns
    -------
    LanguageInfo
        Fully populated language ontology row.

    Raises
    ------
    ValueError
        When the ``scripts`` list is empty, as a primary script is
        required to back language inference and specimen generation.
    """
    if not scripts:
        msg = "scripts must not be empty"
        raise ValueError(msg)

    primary_script = scripts[0]

    language_info: LanguageInfo = {
        "canonical_name": canonical_name,
        "description": description,
        "scripts": list(scripts),
        "primary_script": primary_script,
        "required_blocks": list(required_blocks),
        "optional_blocks": list(optional_blocks or []),
        "sample": SCRIPT_INFO[primary_script]["specimen"],
    }

    return language_info


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
        "description": "Adlam is a modern alphabet created in the 1980s for Fulani. It is used in West Africa and is notable for being a right-to-left script designed for a living African language.",
        "display_language": "ff",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Adlam",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𞤀𞤁𞤂𞤃𞤄𞤅𞤆𞤇𞤈𞤉𞤊𞤋𞤌𞤍𞤎𞤏𞤐𞤑𞤒𞤓𞤔𞤕𞤖𞤗",
    },
    ScriptISO("AGHB"): {
        "canonical_name": "Caucasian Albanian",
        "description": "Caucasian Albanian is an extinct script of the eastern Caucasus, used roughly between the 5th and 8th centuries CE. It is known mainly from inscriptions and palimpsests and is notable for preserving a lost regional literary tradition.",
        "display_language": "xag",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Caucasian Albanian}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐔰𐔱𐔲𐔳𐔴𐔵𐔶𐔷𐔸𐔹𐔺𐔻𐔼𐔽𐔾𐔿𐕀𐕁𐕂𐕃𐕄𐕅𐕆𐕇",
    },
    ScriptISO("AHOM"): {
        "canonical_name": "Ahom",
        "description": "Ahom is a Tai script historically used in Assam for the Ahom language. It survives mainly in manuscripts and is notable for recent scholarly and community revival.",
        "display_language": "aho",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Ahom",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑜀𑜁𑜂𑜃𑜄𑜅𑜆𑜇𑜈𑜉𑜊𑜋𑜌𑜍𑜎𑜏𑜐𑜑𑜒𑜓𑜔𑜕𑜖𑜗",
    },
    ScriptISO("ARAB"): {
        "canonical_name": "Arabic",
        "description": "Arabic is a right-to-left abjad that developed from the Nabataean branch of Aramaic. It is used for Arabic and many other languages and is notable for its cursive letterforms and consonantal base.",
        "display_language": "ar",
        "polyglossia_language": "arabic",
        "fontspec_opts": "Script=Arabic",
        "rtl": True,
        "requires_polyglossia": True,
        "specimen": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    },
    ScriptISO("ARMN"): {
        "canonical_name": "Armenian",
        "description": "Armenian is an alphabet created in the early 5th century for the Armenian language. It remains the standard script for Armenian and is notable for its distinct letter inventory and long literary continuity.",
        "display_language": "hy",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Armenian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    },
    ScriptISO("AVST"): {
        "canonical_name": "Avestan",
        "description": "Avestan is a right-to-left script created for Zoroastrian sacred texts. It was used for the Avestan language and is notable for representing phonology with unusual precision for an ancient script.",
        "display_language": "ae",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Avestan",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐬀𐬁𐬂𐬃𐬄𐬅𐬆𐬇𐬈𐬉𐬊𐬋𐬌𐬍𐬎𐬏𐬐𐬑𐬒𐬓𐬔𐬕𐬖𐬗",
    },
    ScriptISO("BALI"): {
        "canonical_name": "Balinese",
        "description": "Balinese is a Brahmic script of Indonesia used for Balinese and related liturgical texts. It is notable for complex consonant stacking and ornate manuscript forms.",
        "display_language": "ban",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Balinese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᬀᬁᬂᬃᬄᬅᬆᬇᬈᬉᬊᬋᬌᬍᬎᬏᬐᬑᬒᬓᬔᬕᬖᬗ",
    },
    ScriptISO("BATK"): {
        "canonical_name": "Batak",
        "description": "Batak is a traditional script of Sumatra used for Batak languages. It is notable for its Brahmic structure and historical use in letters, records, and ritual writing.",
        "display_language": "bbc",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Batak",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᯀᯁᯂᯃᯄᯅᯆᯇᯈᯉᯊᯋᯌᯍᯎᯏᯐᯑᯒᯓᯔᯕᯖᯗ",
    },
    ScriptISO("BAMU"): {
        "canonical_name": "Bamum",
        "description": "Bamum is a script created in the Bamum kingdom of Cameroon in the late 19th century. It is notable as an indigenous script with several documented stages of development.",
        "display_language": "bax",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Bamum",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꚠꚡꚢꚣꚤꚥꚦꚧꚨꚩꚪꚫꚬꚭꚮꚯꚰꚱꚲꚳꚴꚵꚶꚷ",
    },
    ScriptISO("BASS"): {
        "canonical_name": "Bassa Vah",
        "description": "Bassa Vah is a 20th-century script created for the Bassa language of Liberia and Sierra Leone. It is notable for marking tone explicitly in a language where tone is phonemic.",
        "display_language": "bsq",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Bassa Vah}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𖫐𖫑𖫒𖫓𖫔𖫕𖫖𖫗𖫘𖫙𖫚𖫛𖫜𖫝𖫞𖫟𖫠𖫡𖫢𖫣𖫤𖫥𖫦𖫧",
    },
    ScriptISO("BENG"): {
        "canonical_name": "Bengali",
        "description": "Bengali is an eastern Brahmic script used for Bengali, Assamese, and related languages. It is notable for its many conjunct forms and the absence of a continuous top line in ordinary text.",
        "display_language": "bn",
        "polyglossia_language": "bengali",
        "fontspec_opts": "Script=Bengali",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "বাংলা ভাষা একটি সমৃদ্ধ ভাষা।",
    },
    ScriptISO("BHKS"): {
        "canonical_name": "Bhaiksuki",
        "description": "Bhaiksuki is a historical Indic script used in Buddhist manuscripts in South Asia. It is notable for preserving Sanskrit and Pali material in manuscript transmission.",
        "display_language": "pli",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Bhaiksuki",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑰀𑰁𑰂𑰃𑰄𑰅𑰆𑰇𑰈𑰉𑰊𑰋𑰌𑰍𑰎𑰏𑰐𑰑𑰒𑰓𑰔𑰕𑰖𑰗",
    },
    ScriptISO("BOPO"): {
        "canonical_name": "Bopomofo",
        "description": "Bopomofo is a phonetic notation system developed in the early 20th century for Mandarin Chinese. It is notable for representing pronunciation directly rather than writing words with logographs.",
        "display_language": "zh",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Bopomofo",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄚㄛㄜ",
    },
    ScriptISO("BRAI"): {
        "canonical_name": "Braille",
        "description": "Braille is a tactile writing system encoded in Unicode as braille patterns. It is used across many languages and is notable for representing characters through raised-cell combinations rather than inked glyph shapes.",
        "display_language": "zxx",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "⠁⠃⠉⠙⠑⠋ ⠛⠓⠊⠚⠅⠇",
    },
    ScriptISO("BRAH"): {
        "canonical_name": "Brahmi",
        "description": "Brahmi is an ancient South Asian script attested from the 3rd century BCE. It is notable as the ancestor of most later Brahmic scripts used across South and Southeast Asia.",
        "display_language": "sa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Brahmi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑀀𑀁𑀂𑀃𑀄𑀅𑀆𑀇𑀈𑀉𑀊𑀋𑀌𑀍𑀎𑀏𑀐𑀑𑀒𑀓𑀔𑀕𑀖𑀗",
    },
    ScriptISO("BUGI"): {
        "canonical_name": "Buginese",
        "description": "Buginese is a traditional script of South Sulawesi used for Bugis and related languages. It is notable for its historical manuscript use and Brahmic abugida structure.",
        "display_language": "bug",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Buginese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᨀᨁᨂᨃᨄᨅᨆᨇᨈᨉᨊᨋᨌᨍᨎᨏᨐᨑᨒᨓᨔᨕᨖꧏ᨞᨟",
    },
    ScriptISO("BUHD"): {
        "canonical_name": "Buhid",
        "description": "Buhid is an indigenous Philippine script used by the Mangyan people of Mindoro. It is notable as one of the few precolonial Philippine scripts still used in cultural practice.",
        "display_language": "bku",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Buhid",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᝀᝁᝂᝃᝄᝅᝆᝇᝈᝉᝊᝋᝌᝍᝎᝏᝐᝑ᜵᜶",
    },
    ScriptISO("BYZM"): {
        "canonical_name": "Byzantine Music",
        "description": "Byzantine Music is a notation system for chant in the Eastern Christian liturgical tradition. It is not a general-purpose writing script and is notable for encoding melodic formulas rather than spoken language.",
        "display_language": "zxx",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Byzantine Music}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𝀀𝀁𝀂𝀃𝀄𝀅𝀆𝀇𝀈𝀉𝀊𝀋𝀌𝀍𝀎𝀏𝀐𝀑𝀒𝀓𝀔𝀕𝀖𝀗",
    },
    ScriptISO("CANS"): {
        "canonical_name": "Canadian Syllabics",
        "description": "Canadian Syllabics is a syllabary developed in the 19th century for Cree and later adapted for other Indigenous languages of Canada. It is notable for rotating symbols to mark vowel changes.",
        "display_language": "cr",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Canadian Syllabics",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "᐀ᐁᐂᐃᐄᐅᐆᐇᐈᐉᐊᐋᐌᐍᐎᐏᐐᐑᐒᐓᐔᐕᐖᐗ",
    },
    ScriptISO("CARI"): {
        "canonical_name": "Carian",
        "description": "Carian is an ancient script used in southwestern Anatolia for the Carian language. It is notable for being deciphered largely through inscriptions and bilingual evidence.",
        "display_language": "xcr",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Carian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐊠𐊡𐊢𐊣𐊤𐊥𐊦𐊧𐊨𐊩𐊪𐊫𐊬𐊭𐊮𐊯𐊰𐊱𐊲𐊳𐊴𐊵𐊶𐊷",
    },
    ScriptISO("CHAK"): {
        "canonical_name": "Chakma",
        "description": "Chakma is a Brahmic script used for the Chakma language in Bangladesh and India. It is notable for remaining in active community and educational use in the modern period.",
        "display_language": "ccp",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Chakma",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑄃𑄄𑄅𑄆𑄇𑄈𑄉𑄊𑄋𑄌𑄍𑄎𑄏𑄐𑄑𑄒𑄓𑄔𑄕𑄖𑄗𑄘𑄙𑄚",
    },
    ScriptISO("CHAM"): {
        "canonical_name": "Cham",
        "description": "Cham is a Brahmic script used for Cham languages in Vietnam and Cambodia. It is notable for preserving a long regional manuscript and inscriptional tradition.",
        "display_language": "cjm",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Cham",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꨀꨁꨂꨃꨄꨅꨆꨇꨈꨉꨊꨋꨌꨍꨎꨏꨐꨑꨒꨓꨔꨕꨖꨗ",
    },
    ScriptISO("CHER"): {
        "canonical_name": "Cherokee",
        "description": "Cherokee is a syllabary created by Sequoyah in the early 19th century for the Cherokee language. It is notable as one of the most successful independently invented scripts in regular literacy use.",
        "display_language": "chr",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Cherokee",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᎣᏏᏲ ᎠᏓᎨᏫᏍᏗ",
    },
    ScriptISO("CHRS"): {
        "canonical_name": "Chorasmian",
        "description": "Chorasmian is an extinct script of Central Asia derived from Aramaic for the Chorasmian language. It is notable for surviving mainly in fragments and documentary texts.",
        "display_language": "xco",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Chorasmian",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐾰𐾱𐾲𐾳𐾴𐾵𐾶𐾷𐾸𐾹𐾺𐾻𐾼𐾽𐾾𐾿𐿀𐿁𐿂𐿃𐿄𐿅𐿆𐿇",
    },
    ScriptISO("COPT"): {
        "canonical_name": "Coptic",
        "description": "Coptic is an alphabet based mainly on Greek with additional signs from Egyptian Demotic. It was used for the latest stage of Egyptian and is notable for its continuing liturgical role.",
        "display_language": "cop",
        "polyglossia_language": "coptic",
        "fontspec_opts": "Script=Coptic",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "ϢϣϤϥϦϧϨϩϪϫϬϭϮϯⲀⲁⲂⲃⲄⲅⲆⲇⲈⲉ",
    },
    ScriptISO("CPMN"): {
        "canonical_name": "Cypro-Minoan",
        "description": "Cypro-Minoan is an undeciphered Bronze Age script from Cyprus. It is notable because its inscriptions are short and the underlying language remains unknown.",
        "display_language": "und",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Cypro-Minoan}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𒾐𒾑𒾒𒾓𒾔𒾕𒾖𒾗𒾘𒾙𒾚𒾛𒾜𒾝𒾞𒾟𒾠𒾡𒾢𒾣𒾤𒾥𒾦𒾧",
    },
    ScriptISO("CPRT"): {
        "canonical_name": "Cypriot Syllabary",
        "description": "Cypriot Syllabary is an Iron Age script of Cyprus used for Greek and Eteocypriot. It is notable for representing syllables rather than individual consonants and vowels.",
        "display_language": "ecy",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Cypriot Syllabary}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐠀𐠁𐠂𐠃𐠄𐠅𐠆𐠇𐠈𐠉𐠊𐠋𐠌𐠍𐠎𐠏𐠐𐠑𐠒𐠓𐠔𐠕𐠖𐠗",
    },
    ScriptISO("CYRL"): {
        "canonical_name": "Cyrillic",
        "description": "Cyrillic is an alphabet developed in the medieval Slavic world, especially in the First Bulgarian Empire. It is used for many Slavic and non-Slavic languages and is notable for its adaptation of Greek letterforms.",
        "display_language": "ru",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Cyrillic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Съешь же ещё этих мягких французских булок",
    },
    ScriptISO("DEVA"): {
        "canonical_name": "Devanagari",
        "description": "Devanagari is a major South Asian Brahmic script used for Hindi, Sanskrit, Marathi, and other languages. It is notable for its headline and extensive consonant conjunct system.",
        "display_language": "hi",
        "polyglossia_language": "hindi",
        "fontspec_opts": "Script=Devanagari",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "नमस्ते दुनिया",
    },
    ScriptISO("DIAK"): {
        "canonical_name": "Dives Akuru",
        "description": "Dives Akuru is a historical script of the Maldives used for older stages of Dhivehi. It is notable as an earlier local writing tradition predating modern Thaana.",
        "display_language": "dv",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Dives Akuru}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑤀𑤂𑤄 𑤋𑤢𑤼",
    },
    ScriptISO("DSRT"): {
        "canonical_name": "Deseret",
        "description": "Deseret is a 19th-century alphabet devised in the Latter Day Saint movement for writing English. It is notable for its strongly phonemic design and limited historical adoption.",
        "display_language": "en",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Deseret",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐐀𐐁𐐂𐐃𐐄𐐅𐐆𐐇𐐈𐐉𐐊𐐋𐐌𐐍𐐎𐐏𐐐𐐑𐐒𐐓𐐔𐐕𐐖𐐗",
    },
    ScriptISO("DOGR"): {
        "canonical_name": "Dogra",
        "description": "Dogra is a historical script of the western Himalayas used for Dogri and related languages. It is notable for its modern recovery after long displacement by Devanagari and Perso-Arabic scripts.",
        "display_language": "doi",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Dogra",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑠖𑠮𑠝𑠳 𑠛𑠯𑠬𑠬𑠰",
    },
    ScriptISO("ETHI"): {
        "canonical_name": "Ethiopic",
        "description": "Ethiopic is an abugida of the Horn of Africa used for Ge'ez and several modern languages. It is notable for encoding consonant-vowel combinations as distinct graphic series.",
        "display_language": "ti",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Ethiopic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ሰላም እንታይ ከመይ ኢኻ",
    },
    ScriptISO("ELBA"): {
        "canonical_name": "Elbasan",
        "description": "Elbasan is an 18th-century alphabet created for Albanian. It is notable as a short-lived local attempt to provide Albanian with its own dedicated script.",
        "display_language": "sq",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Elbasan",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐔀𐔁𐔂𐔃𐔄𐔅𐔆𐔇𐔈𐔉𐔊𐔋𐔌𐔍𐔎𐔏𐔐𐔑𐔒𐔓𐔔𐔕𐔖𐔗",
    },
    ScriptISO("ELYM"): {
        "canonical_name": "Elymaic",
        "description": "Elymaic is a right-to-left script used in ancient southwestern Iran for the Elymaic language. It is notable for a small corpus of inscriptional evidence from the late Parthian period.",
        "display_language": "xly",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Elymaic",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐿠𐿡𐿢𐿣𐿤𐿥𐿦𐿧𐿨𐿩𐿪𐿫𐿬𐿭𐿮𐿯𐿰𐿱𐿲𐿳𐿴𐿵𐿶",
    },
    ScriptISO("GEOR"): {
        "canonical_name": "Georgian",
        "description": "Georgian is the script used for Georgian and some other Kartvelian and Caucasian languages. It is notable for its distinctive letterforms and long inscriptional history.",
        "display_language": "ka",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Georgian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ქართული ტექსტის მაგალითი",
    },
    ScriptISO("GOTH"): {
        "canonical_name": "Gothic",
        "description": "Gothic is an alphabet created in late antiquity for the Gothic language. It is notable for its association with the Gothic Bible and the small surviving corpus of the language.",
        "display_language": "got",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Gothic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐌰𐌱𐌲𐌳𐌴𐌵𐌶𐌷𐌸𐌹𐌺𐌻𐌼𐌽𐌾𐌿𐍀𐍁𐍂𐍃𐍄𐍅𐍆𐍇",
    },
    ScriptISO("GREK"): {
        "canonical_name": "Greek",
        "description": "Greek is an alphabet derived from Phoenician and used for Greek since the early 1st millennium BCE. It is notable for being the earliest alphabet to systematically represent vowels.",
        "display_language": "el",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Greek",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    },
    ScriptISO("GLAG"): {
        "canonical_name": "Glagolitic",
        "description": "Glagolitic is the oldest known Slavic alphabet, created in the 9th century for Christian texts. It is notable for preceding Cyrillic in the written tradition of Slavic liturgy.",
        "display_language": "cu",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Glagolitic",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ⰀⰁⰂⰃⰄⰅⰆⰇⰈⰉⰊⰋⰌⰍⰎⰏⰐⰑⰒⰓⰔⰕⰖⰗ",
    },
    ScriptISO("GRAN"): {
        "canonical_name": "Grantha",
        "description": "Grantha is a South Indian script traditionally used to write Sanskrit. It is notable for handling Sanskrit consonant clusters more fully than some neighboring regional scripts.",
        "display_language": "sa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Grantha",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑌀𑌁𑌂𑌃𑌅𑌆𑌇𑌈𑌉𑌊𑌋𑌌𑌏𑌐𑌓𑌔𑌕𑌖𑌗𑌘𑌙𑌚𑌛𑌜",
    },
    ScriptISO("GONG"): {
        "canonical_name": "Gunjala Gondi",
        "description": "Gunjala Gondi is a script used for the Gondi language and attested in manuscript sources from central India. It is notable as one of the two distinct Gondi scripts encoded in Unicode.",
        "display_language": "gon",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Gunjala Gondi}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑵠𑵡𑵢𑵣𑵤𑵥𑵦𑵧𑵨𑵩𑵪𑵫𑵬𑵭𑵮𑵯𑵰𑵱𑵲𑵳𑵴𑵵𑵶𑵷",
    },
    ScriptISO("GONM"): {
        "canonical_name": "Masaram Gondi",
        "description": "Masaram Gondi is a modern script created for the Gondi language in the 20th century. It is notable as a community-specific writing system separate from Gunjala Gondi.",
        "display_language": "gon",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Masaram Gondi}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑴀𑴁𑴂𑴃𑴄𑴅𑴆𑴇𑴈𑴉𑴊𑴋𑴌𑴍𑴎𑴏𑴐𑴑𑴒𑴓𑴔𑴕𑴖𑴗",
    },
    ScriptISO("GUJR"): {
        "canonical_name": "Gujarati",
        "description": "Gujarati is a western Indic script used for Gujarati and related languages. It is notable for omitting the continuous headline found in Devanagari.",
        "display_language": "gu",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Gujarati",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ઁંઃઅઆઇઈઉઊઋઌઍએઐઑઓઔકખગઘઙચછ",
    },
    ScriptISO("GURU"): {
        "canonical_name": "Gurmukhi",
        "description": "Gurmukhi is the standard script for Punjabi in India and was standardized in the Sikh tradition. It is notable for its central role in the transmission of Sikh scripture.",
        "display_language": "pa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Gurmukhi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ਁਂਃਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟ",
    },
    ScriptISO("KNDA"): {
        "canonical_name": "Kannada",
        "description": "Kannada is a South Indian Brahmic script used mainly for Kannada. It is notable for rounded shapes that reflect manuscript writing on palm leaf and paper.",
        "display_language": "kn",
        "polyglossia_language": "kannada",
        "fontspec_opts": "Script=Kannada",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞ",
    },
    ScriptISO("HANG"): {
        "canonical_name": "Hangul",
        "description": "Hangul is the Korean script created in the 15th century under King Sejong. It is notable for its featural design, with letter shapes reflecting articulation.",
        "display_language": "ko",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Hangul",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "키스의 고유조건은 입술끼리 만나야 한다",
    },
    ScriptISO("HANO"): {
        "canonical_name": "Hanunoo",
        "description": "Hanunoo is an indigenous Philippine script used by Mangyan communities of Mindoro. It is notable for continued traditional use, including writing on bamboo.",
        "display_language": "hnn",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Hanunoo",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᜠᜡᜢᜣᜤᜥᜦᜧᜨᜩᜪᜫᜬᜭᜮᜯᜰᜱᜲᜳ᜴",
    },
    ScriptISO("ROHG"): {
        "canonical_name": "Hanifi Rohingya",
        "description": "Hanifi Rohingya is a modern script for the Rohingya language created in the 20th century. It is notable for being a right-to-left alphabet designed specifically for Rohingya literacy.",
        "display_language": "rhg",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Hanifi Rohingya}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐴀𐴁𐴂𐴃𐴄𐴅𐴆𐴇𐴈𐴉𐴊𐴋𐴌𐴍𐴎𐴏𐴐𐴑𐴒𐴓𐴔𐴕𐴖𐴗",
    },
    ScriptISO("HANI"): {
        "canonical_name": "Han",
        "description": "Han is the logographic script used for Chinese and historically adapted elsewhere in East Asia. It is notable for representing morphemes with characters rather than alphabetic sequences.",
        "display_language": "zh",
        "polyglossia_language": "chinese",
        "fontspec_opts": "Script=CJK",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "天地玄黃 宇宙洪荒",
    },
    ScriptISO("HEBR"): {
        "canonical_name": "Hebrew",
        "description": "Hebrew is a right-to-left abjad descended from the Aramaic script. It is used for Hebrew and historically for several Jewish languages and is notable for optional vowel pointing.",
        "display_language": "he",
        "polyglossia_language": "hebrew",
        "fontspec_opts": "Script=Hebrew",
        "rtl": True,
        "requires_polyglossia": True,
        "specimen": "דג סקרן שט בים מאוכזב",
    },
    ScriptISO("HLUW"): {
        "canonical_name": "Anatolian Hieroglyphs",
        "description": "Anatolian Hieroglyphs is a logo-syllabic script used mainly for Luwian in ancient Anatolia. It is notable for monumental inscriptions combining signs with syllabic and logographic values.",
        "display_language": "hlu",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Anatolian Hieroglyphs}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𔐀𔐁𔐂𔐃𔐄𔐅𔐆𔐇𔐈𔐉𔐊𔐋𔐌𔐍𔐎𔐏𔐐𔐑𔐒𔐓𔐔𔐕𔐖𔐗",
    },
    ScriptISO("HIRA"): {
        "canonical_name": "Hiragana",
        "description": "Hiragana is a Japanese syllabary derived from cursive Chinese characters. It is notable for marking native morphology and grammatical endings in modern Japanese writing.",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "Script=Kana",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "いろはにほへと ちりぬるを",
    },
    ScriptISO("KANA"): {
        "canonical_name": "Katakana",
        "description": "Katakana is a Japanese syllabary derived from shorthand components of Chinese characters. It is notable for its use with loanwords, scientific terms, and emphasis.",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "Script=Kana",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "アイウエオ カキクケコ",
    },
    ScriptISO("JPAN"): {
        "canonical_name": "Japanese",
        "description": "Japanese is a mixed writing system that combines kanji with hiragana and katakana. It is notable for using multiple script types in the same sentence as part of standard orthography.",
        "display_language": "ja",
        "polyglossia_language": "japanese",
        "fontspec_opts": "Script=Kana",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "いろはにほへと ちりぬるを",
    },
    ScriptISO("KHMR"): {
        "canonical_name": "Khmer",
        "description": "Khmer is a Southeast Asian Brahmic script used for Khmer. It is notable for its large vowel inventory and historically limited use of word spacing in continuous text.",
        "display_language": "km",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Khmer",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ភាសាខ្មែរ​ជា​ភាសា​ស្រស់ស្អាត",
    },
    ScriptISO("JAVA"): {
        "canonical_name": "Javanese",
        "description": "Javanese is a Brahmic script historically used on Java for Javanese and related texts. It is notable for elaborate consonant forms and stacked conjunct behavior.",
        "display_language": "jv",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Javanese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꦀꦁꦂꦃꦄꦅꦆꦇꦈꦉꦊꦋꦌꦍꦎꦏꦐꦑꦒꦓꦔꦕꦖꦗ",
    },
    ScriptISO("KAWI"): {
        "canonical_name": "Kawi",
        "description": "Kawi is a historical Brahmic script of maritime Southeast Asia used especially for Old Javanese and Sanskrit texts. It is notable for manuscript and inscriptional use across Java, Bali, and neighboring regions.",
        "display_language": "kaw",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Kawi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑼄𑼅𑼆𑼇𑼈𑼉𑼊𑼋𑼌𑼍𑼎𑼏𑼐𑼒𑼓𑼔𑼕𑼖𑼗𑼘𑼙𑼚𑼛𑼜",
    },
    ScriptISO("KTHI"): {
        "canonical_name": "Kaithi",
        "description": "Kaithi is a historical North Indian script once widely used for administrative and commercial documents. It is notable for its vernacular function outside elite manuscript traditions.",
        "display_language": "bho",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Kaithi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑂀𑂁𑂂𑂃𑂄𑂅𑂆𑂇𑂈𑂉𑂊𑂋𑂌𑂍𑂎𑂏𑂐𑂑𑂒𑂓𑂔𑂕𑂖𑂗",
    },
    ScriptISO("LAOO"): {
        "canonical_name": "Lao",
        "description": "Lao is the script used for Lao and related languages in Laos. It is notable for its close historical relationship to the Thai script.",
        "display_language": "lo",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Lao",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ພາສາລາວເປັນພາສາທີ່ສວຍງາມ",
    },
    ScriptISO("LATN"): {
        "canonical_name": "Latin",
        "description": "Latin is the alphabet that developed from the writing of ancient Rome. It is used for hundreds of languages worldwide and is notable as the most widely used writing system today.",
        "display_language": "en",
        "polyglossia_language": "",
        "fontspec_opts": "",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "The quick brown fox jumps over the lazy dog",
    },
    ScriptISO("LIMB"): {
        "canonical_name": "Limbu",
        "description": "Limbu is a script used for the Limbu language in Nepal and India. It is notable for its indigenous Himalayan tradition and structured vowel marking.",
        "display_language": "lif",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Limbu",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᤀᤁᤂᤃᤄᤅᤆᤇᤈᤉᤊᤋᤌᤍᤎᤏᤐᤑᤒᤓᤔᤕᤖᤗ",
    },
    ScriptISO("LISU"): {
        "canonical_name": "Lisu",
        "description": "Lisu is the script used for the Lisu language, based on the Fraser alphabet of the early 20th century. It is notable for using modified Latin-like letter shapes in a distinct inventory.",
        "display_language": "lis",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Lisu",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꓐꓑꓒꓓꓔꓕꓖꓗꓘꓙꓚꓛꓜꓝꓞꓟꓠꓡꓢꓣꓤꓥꓦꓧ",
    },
    ScriptISO("MLYM"): {
        "canonical_name": "Malayalam",
        "description": "Malayalam is a South Indian Brahmic script used for Malayalam. It is notable for rounded forms and a large set of consonant and vowel combinations.",
        "display_language": "ml",
        "polyglossia_language": "malayalam",
        "fontspec_opts": "Script=Malayalam",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞ",
    },
    ScriptISO("MYMR"): {
        "canonical_name": "Myanmar",
        "description": "Myanmar is a Brahmic script used for Burmese and several other languages of Myanmar. It is notable for stacked consonants and circular letterforms.",
        "display_language": "my",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Myanmar",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    },
    ScriptISO("MEDF"): {
        "canonical_name": "Medefaidrin",
        "description": "Medefaidrin is a script created by a Christian community in southeastern Nigeria for a liturgical language of the same name. It is notable as a modern community-designed writing system.",
        "display_language": "dmf",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Medefaidrin",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𖹀𖹁𖹂𖹃𖹄𖹅𖹆𖹇𖹈𖹉𖹊𖹋𖹌𖹍𖹎𖹏𖹐𖹑𖹒𖹓𖹔𖹕𖹖𖹗",
    },
    ScriptISO("MEND"): {
        "canonical_name": "Mende Kikakui",
        "description": "Mende Kikakui is a syllabary created in the 20th century for the Mende language of Sierra Leone. It is notable as an independently developed African script.",
        "display_language": "men",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Mende Kikakui}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𞠀𞠁𞠂𞠃𞠄𞠅𞠆𞠇𞠈𞠉𞠊𞠋𞠌𞠍𞠎𞠏𞠐𞠑𞠒𞠓𞠔𞠕𞠖𞠗",
    },
    ScriptISO("MONG"): {
        "canonical_name": "Mongolian",
        "description": "Mongolian is the traditional script used for Mongolian and related languages. It is notable for its vertical layout, written top to bottom in columns ordered left to right.",
        "display_language": "mn",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Mongolian",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᠠᠡᠢᠣᠤᠥᠦᠧᠨᠩᠪᠫᠬᠭᠮᠯᠰᠱᠲᠳᠴᠵᠶᠷ",
    },
    ScriptISO("MROO"): {
        "canonical_name": "Mro",
        "description": "Mro is a modern script used for the Mro language of the Chittagong Hill Tracts. It is notable for being a dedicated script distinct from surrounding Brahmic systems.",
        "display_language": "mro",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Mro",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𖩠𖩡𖩢𖩣𖩤𖩥𖩦𖩧𖩨𖩩𖩪𖩫𖩬𖩭𖩮𖩯𖩰𖩱𖩲𖩳𖩴𖩵𖩶𖩷",
    },
    ScriptISO("MAKA"): {
        "canonical_name": "Makasar",
        "description": "Makasar is a historical South Sulawesi script used for the Makassarese language. It is notable for a compact Brahmic-derived system preserved in manuscripts and a limited inscriptional record.",
        "display_language": "mak",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Makasar",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑻠𑻡𑻢𑻣𑻤𑻥𑻦𑻧𑻨𑻩𑻪𑻫𑻬𑻭𑻮𑻯𑻰𑻱𑻲𑻳𑻴𑻵𑻶",
    },
    ScriptISO("MTEI"): {
        "canonical_name": "Meetei Mayek",
        "description": "Meetei Mayek is the traditional script of the Manipuri language. It is notable for a modern revival after long replacement by the Bengali script.",
        "display_language": "mni",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Meitei Mayek}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꯀꯁꯂꯃꯄꯅꯆꯇꯈꯉꯊꯋꯌꯍꯎꯏꯐꯑꯒꯓꯔꯕꯖꯗ",
    },
    ScriptISO("NEWA"): {
        "canonical_name": "Newa",
        "description": "Newa is a historical Nepalese script used for Nepal Bhasa and Sanskrit. It is notable for its manuscript tradition in the Kathmandu Valley.",
        "display_language": "new",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Newa",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑐀𑐁𑐂𑐃𑐄𑐅𑐆𑐇𑐈𑐉𑐊𑐋𑐌𑐍𑐎𑐏𑐐𑐑𑐒𑐓𑐔𑐕𑐖𑐗",
    },
    ScriptISO("NKOO"): {
        "canonical_name": "NKo",
        "description": "NKo is a right-to-left script created in 1949 for Manding languages. It is notable for its role in a modern literacy movement spanning several West African languages.",
        "display_language": "nqo",
        "polyglossia_language": "",
        "fontspec_opts": "Script={N'Ko}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "߀߁߂߃߄߅߆߇߈߉ߊߋߌߍߎߏߐߑߒߓߔߕߖߗ",
    },
    ScriptISO("OSGE"): {
        "canonical_name": "Osage",
        "description": "Osage is a modern script standardized for the Osage language in the 21st century. It is notable as a recent community-led script design with bicameral letters.",
        "display_language": "osa",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Osage",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐒰𐒱𐒲𐒳𐒴𐒵𐒶𐒷𐒸𐒹𐒺𐒻𐒼𐒽𐒾𐒿𐓀𐓁𐓂𐓃𐓄𐓅𐓆𐓇",
    },
    ScriptISO("PERM"): {
        "canonical_name": "Old Permic",
        "description": "Old Permic is a medieval script created for Komi in northeastern Europe. It is notable for being one of the few historical scripts devised specifically for a Uralic language.",
        "display_language": "kv",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Old Permic}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𐍐𐍑𐍒𐍓𐍔𐍕𐍖𐍗𐍘𐍙𐍚𐍛𐍜𐍝𐍞𐍟𐍠𐍡𐍢𐍣𐍤𐍥𐍦𐍧",
    },
    ScriptISO("RJNG"): {
        "canonical_name": "Rejang",
        "description": "Rejang is a traditional Sumatran script used for the Rejang language. It is notable for its compact letterforms within the Brahmic family.",
        "display_language": "rej",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Rejang",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꤰꤱꤲꤳꤴꤵꤶꤷꤸꤹꤺꤻꤼꤽꤾꤿꥀꥁꥂꥃꥄꥅꥆꥇ",
    },
    ScriptISO("PHLP"): {
        "canonical_name": "Psalter Pahlavi",
        "description": "Psalter Pahlavi is a right-to-left script used for Middle Persian, especially in the manuscript tradition of the Psalter. It is notable as one of the distinct historical Pahlavi writing forms.",
        "display_language": "pal",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Psalter Pahlavi}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐮀𐮁𐮂𐮃𐮄𐮅𐮆𐮇𐮈𐮉𐮊𐮋𐮌𐮍𐮎𐮏𐮐𐮑𐮒𐮓𐮔𐮕𐮖𐮗",
    },
    ScriptISO("PHLI"): {
        "canonical_name": "Inscriptional Pahlavi",
        "description": "Inscriptional Pahlavi is a monumental script used for Middle Persian inscriptions. It is notable for its conservative forms and reliance on inherited Aramaic conventions.",
        "display_language": "pal",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Inscriptional Pahlavi}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐭠𐭡𐭢𐭣𐭤𐭥𐭦𐭧𐭨𐭩𐭪𐭫𐭬𐭭𐭮𐭯𐭰𐭱𐭲𐭳𐭴𐭵𐭶𐭷",
    },
    ScriptISO("ORYA"): {
        "canonical_name": "Oriya",
        "description": "Oriya, now usually called Odia script, is an eastern Indic script used for Odia. It is notable for rounded forms shaped by manuscript writing practice.",
        "display_language": "or",
        "polyglossia_language": "odia",
        "fontspec_opts": "Script=Oriya",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "ଅଆଇଈଉଊଋଏଐଓଔକଖଗଘଙଚଛଜଝଞ",
    },
    ScriptISO("SOGO"): {
        "canonical_name": "Old Sogdian",
        "description": "Old Sogdian is an early stage of the Sogdian script used in Central Asia. It is notable for preserving an earlier written form of an important Silk Road language.",
        "display_language": "sog",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Old Sogdian}",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐼀𐼁𐼂𐼃𐼄𐼅𐼆𐼇𐼈𐼉𐼊𐼋𐼌𐼍𐼎𐼏𐼐𐼑𐼒𐼓𐼔𐼕𐼖𐼗",
    },
    ScriptISO("SOGD"): {
        "canonical_name": "Sogdian",
        "description": "Sogdian is a right-to-left Iranian script used in Central Asia. It is notable for its historical influence on later scripts such as Old Uyghur and Mongolian.",
        "display_language": "sog",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Sogdian",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "𐼰𐼱𐼲𐼳𐼴𐼵𐼶𐼷𐼸𐼹𐼺𐼻𐼼𐼽𐼾𐼿𐽀𐽁𐽂𐽃𐽄𐽅𐽆𐽇",
    },
    ScriptISO("SAUR"): {
        "canonical_name": "Saurashtra",
        "description": "Saurashtra is a modern script used for the Saurashtra language in India. It is notable for preserving a distinct community writing tradition alongside more widespread regional scripts.",
        "display_language": "saz",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Saurashtra",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꢂꢃꢄꢅꢆꢇꢈꢉꢊꢋꢌꢍꢎꢏꢐꢑꢒꢓꢔꢕꢖꢗꢘꢙ",
    },
    ScriptISO("SUND"): {
        "canonical_name": "Sundanese",
        "description": "Sundanese is the traditional script of West Java used for the Sundanese language. It is notable for a modern standardized form that revived a historical regional script.",
        "display_language": "su",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Sundanese",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᮃᮄᮅᮆᮇᮈᮉᮊᮋᮌᮍᮎᮏᮐᮑᮒᮓᮔᮕᮖᮗᮘᮙᮚ",
    },
    ScriptISO("SYLO"): {
        "canonical_name": "Syloti Nagri",
        "description": "Syloti Nagri is a script historically used for Sylheti in the Bengal region. It is notable for its compact letter shapes and its role in regional print culture.",
        "display_language": "syl",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Syloti Nagri}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꠀꠁꠂꠃꠄꠅ꠆ꠇꠈꠉꠊꠋꠌꠍꠎꠏꠐꠑꠒꠓꠔꠕꠖꠗ",
    },
    ScriptISO("LEPC"): {
        "canonical_name": "Lepcha",
        "description": "Lepcha is a script of the eastern Himalayas used for the Lepcha language. It is notable for being an indigenous script rather than a direct regional derivative.",
        "display_language": "lep",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Lepcha",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᰀᰁᰂᰃᰄᰅᰆᰇᰈᰉᰊᰋᰌᰍᰎᰏᰐᰑᰒᰓᰔᰕᰖᰗ",
    },
    ScriptISO("SINH"): {
        "canonical_name": "Sinhala",
        "description": "Sinhala is the script used for Sinhala in Sri Lanka. It is notable for rounded forms and a long literary tradition tied to Buddhist culture.",
        "display_language": "si",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Sinhala",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "සිංහල භාෂාව ලස්සනයි",
    },
    ScriptISO("TAGB"): {
        "canonical_name": "Tagbanwa",
        "description": "Tagbanwa is an indigenous Philippine script used in Palawan. It is notable as one of the surviving native scripts of the archipelago.",
        "display_language": "tbw",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tagbanwa",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᝠᝡᝢᝣᝤᝥᝦᝧᝨᝩᝪᝫᝬᝮᝯᝰᝲᝳ᝴",
    },
    ScriptISO("TGLG"): {
        "canonical_name": "Tagalog",
        "description": "Tagalog, often called Baybayin in historical context, is an indigenous Philippine script formerly used for Tagalog and related languages. It is notable as a precolonial abugida with strong symbolic revival today.",
        "display_language": "tl",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tagalog",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᜀᜁᜂᜃᜄᜅᜆᜇᜈᜉᜊᜋᜌᜎᜏᜐᜑᜒᜓ᜔",
    },
    ScriptISO("LANA"): {
        "canonical_name": "Tai Tham",
        "description": "Tai Tham is a script of northern mainland Southeast Asia used for Northern Thai and related languages. It is notable for both vernacular and Buddhist manuscript use.",
        "display_language": "nod",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Tai Tham}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᨠᨡᨢᨣᨤᨥᨦᨧᨨᨩᨪᨫᨬᨭᨮᨯᨰᨱᨲᨳᨴᨵᨶᨷ",
    },
    ScriptISO("TAVT"): {
        "canonical_name": "Tai Viet",
        "description": "Tai Viet is a script used for Tai Dam and related languages in mainland Southeast Asia. It is notable for integrating tone marking into its orthography.",
        "display_language": "blt",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Tai Viet}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꪀꪁꪂꪃꪄꪅꪆꪇꪈꪉꪊꪋꪌꪍꪎꪏꪐꪑꪒꪓꪔꪕꪖꪗ",
    },
    ScriptISO("TALE"): {
        "canonical_name": "Tai Le",
        "description": "Tai Le is a script used for Tai Nua in China and neighboring regions. It is notable for its relatively simple modern standardized letterforms.",
        "display_language": "tdd",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Tai Le}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ᥐᥑᥒᥓᥔᥕᥖᥗᥘᥙᥚᥛᥜᥝᥞᥟᥠᥡᥢᥣᥤᥥᥦᥧ",
    },
    ScriptISO("TFNG"): {
        "canonical_name": "Tifinagh",
        "description": "Tifinagh is the script associated with Berber languages in North Africa. It is notable for its modern standardized form, Neo-Tifinagh, used officially in Morocco.",
        "display_language": "zgh",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tifinagh",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ⴰⴱⴲⴳⴴⴵⴶⴷⴸⴹⴺⴻⴼⴽⴾⴿⵀⵁⵂⵃⵄⵅⵆⵇ",
    },
    ScriptISO("TIRH"): {
        "canonical_name": "Tirhuta",
        "description": "Tirhuta is a historical eastern Indic script used for Maithili. It is notable for its close relationship to the Bengali-Assamese script group.",
        "display_language": "mai",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Tirhuta",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑒀𑒁𑒂𑒃𑒄𑒅𑒆𑒇𑒈𑒉𑒊𑒋𑒌𑒍𑒎𑒏𑒐𑒑𑒒𑒓𑒔𑒕𑒖𑒗",
    },
    ScriptISO("TAML"): {
        "canonical_name": "Tamil",
        "description": "Tamil is a South Indian script used for Tamil. It is notable for a long continuous literary record and a letter inventory adapted to Tamil phonology.",
        "display_language": "ta",
        "polyglossia_language": "tamil",
        "fontspec_opts": "Script=Tamil",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "யாதும் ஊரே யாவரும் கேளிர்",
    },
    ScriptISO("TELU"): {
        "canonical_name": "Telugu",
        "description": "Telugu is a South Indian Brahmic script used for Telugu. It is notable for rounded letterforms and clear vowel-sign patterns.",
        "display_language": "te",
        "polyglossia_language": "telugu",
        "fontspec_opts": "Script=Telugu",
        "rtl": False,
        "requires_polyglossia": True,
        "specimen": "అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞ",
    },
    ScriptISO("THAA"): {
        "canonical_name": "Thaana",
        "description": "Thaana is the right-to-left script used for Dhivehi in the Maldives. It is notable for an unusual historical development that incorporates forms derived from numerals and Arabic influence.",
        "display_language": "dv",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Thaana",
        "rtl": True,
        "requires_polyglossia": False,
        "specimen": "ހށނރބޅކއވމފދތލގޏސޑޒ",
    },
    ScriptISO("THAI"): {
        "canonical_name": "Thai",
        "description": "Thai is the script used for Thai and some related languages. It is notable for explicit tone marks and an Indic-derived consonant class system.",
        "display_language": "th",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Thai",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ภาษาไทยเป็นภาษาที่สวยงาม",
    },
    ScriptISO("SYRC"): {
        "canonical_name": "Syriac",
        "description": "Syriac is a right-to-left script used for the Syriac language and related liturgical traditions. It is notable for several major calligraphic styles, including Estrangela, Serto, and East Syriac.",
        "display_language": "syr",
        "polyglossia_language": "syriac",
        "fontspec_opts": "Script=Syriac",
        "rtl": True,
        "requires_polyglossia": True,
        "specimen": "ܐܒܓܕ ܗܘܙܚ ܛܝܟܠ ܡܢܣܥ",
    },
    ScriptISO("KALI"): {
        "canonical_name": "Kayah Li",
        "description": "Kayah Li is a 20th-century script created for Kayah and related Karenni languages. It is notable for being an alphabetic design independent of neighboring Brahmic scripts.",
        "display_language": "kyu",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Kayah Li}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "꤀꤁꤂꤃꤄꤅꤆꤇꤈꤉ꤊꤋꤌꤍꤎꤏꤐꤑꤒꤓꤔꤕꤖꤗ",
    },
    ScriptISO("WARA"): {
        "canonical_name": "Warang Citi",
        "description": "Warang Citi is a modern script created for the Ho language. It is notable as a community-designed alphabet intended to replace borrowed regional scripts.",
        "display_language": "hoc",
        "polyglossia_language": "",
        "fontspec_opts": "Script={Warang Citi}",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "𑢠𑢡𑢢𑢣𑢤𑢥𑢦𑢧𑢨𑢩𑢪𑢫𑢬𑢭𑢮𑢯𑢰𑢱𑢲𑢳𑢴𑢵𑢶𑢷",
    },
    ScriptISO("VAII"): {
        "canonical_name": "Vai",
        "description": "Vai is a syllabary used for the Vai language of Liberia and Sierra Leone. It is notable as an independently created script that remains in continuous use.",
        "display_language": "vai",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Vai",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꔀꔁꔂꔃꔄꔅꔆꔇꔈꔉꔊꔋꔌꔍꔎꔏꔐꔑꔒꔓꔔꔕꔖꔗ",
    },
    ScriptISO("YIII"): {
        "canonical_name": "Yi",
        "description": "Yi is a syllabic script used mainly for Nuosu in southwest China. It is notable for its large standardized inventory of syllable signs.",
        "display_language": "ii",
        "polyglossia_language": "",
        "fontspec_opts": "Script=Yi",
        "rtl": False,
        "requires_polyglossia": False,
        "specimen": "ꆈꌠꉙ ꉙꄜꐨ",
    },
}

SCRIPT_INFO.update(
    {
        ScriptISO("XSUX"): _make_dedicated_script_info(
            "Cuneiform",
            "und",
            ["Cuneiform"],
            optional_blocks=[
                "Cuneiform Numbers and Punctuation",
                "Early Dynastic Cuneiform",
            ],
            inference_priority=87,
        ),
        ScriptISO("EGYP"): _make_dedicated_script_info(
            "Egyptian Hieroglyphs",
            "und",
            ["Egyptian Hieroglyphs"],
            optional_blocks=[
                "Egyptian Hieroglyph Format Controls",
                "Egyptian Hieroglyphs Extended-A",
            ],
            inference_priority=88,
        ),
        ScriptISO("HATR"): _make_dedicated_script_info(
            "Hatran",
            "und",
            ["Hatran"],
            inference_priority=89,
        ),
        ScriptISO("ARMI"): _make_dedicated_script_info(
            "Imperial Aramaic",
            "und",
            ["Imperial Aramaic"],
            inference_priority=90,
        ),
        ScriptISO("PRTI"): _make_dedicated_script_info(
            "Inscriptional Parthian",
            "und",
            ["Inscriptional Parthian"],
            inference_priority=91,
        ),
        ScriptISO("KHAR"): _make_dedicated_script_info(
            "Kharoshthi",
            "und",
            ["Kharoshthi"],
            inference_priority=92,
        ),
        ScriptISO("SIND"): _make_dedicated_script_info(
            "Khudawadi",
            "und",
            ["Khudawadi"],
            inference_priority=93,
        ),
        ScriptISO("LINA"): _make_dedicated_script_info(
            "Linear A",
            "und",
            ["Linear A"],
            inference_priority=94,
        ),
        ScriptISO("LINB"): _make_dedicated_script_info(
            "Linear B",
            "und",
            ["Linear B Syllabary"],
            optional_blocks=["Linear B Ideograms"],
            inference_priority=95,
        ),
        ScriptISO("LYCI"): _make_dedicated_script_info(
            "Lycian",
            "und",
            ["Lycian"],
            inference_priority=96,
        ),
        ScriptISO("LYDI"): _make_dedicated_script_info(
            "Lydian",
            "und",
            ["Lydian"],
            inference_priority=97,
        ),
        ScriptISO("MAND"): _make_dedicated_script_info(
            "Mandaic",
            "und",
            ["Mandaic"],
            inference_priority=98,
        ),
        ScriptISO("MANI"): _make_dedicated_script_info(
            "Manichaean",
            "und",
            ["Manichaean"],
            inference_priority=99,
        ),
        ScriptISO("MARC"): _make_dedicated_script_info(
            "Marchen",
            "und",
            ["Marchen"],
            inference_priority=100,
        ),
        ScriptISO("MAYA"): _make_dedicated_script_info(
            "Mayan Numerals",
            "zxx",
            ["Mayan Numerals"],
            inference_priority=101,
        ),
        ScriptISO("MERO"): _make_dedicated_script_info(
            "Meroitic",
            "und",
            ["Meroitic Hieroglyphs"],
            optional_blocks=["Meroitic Cursive"],
            inference_priority=102,
        ),
        ScriptISO("PLRD"): _make_dedicated_script_info(
            "Miao",
            "und",
            ["Miao"],
            inference_priority=103,
        ),
        ScriptISO("MODI"): _make_dedicated_script_info(
            "Modi",
            "und",
            ["Modi"],
            inference_priority=104,
        ),
        ScriptISO("NBAT"): _make_dedicated_script_info(
            "Nabataean",
            "und",
            ["Nabataean"],
            inference_priority=105,
        ),
        ScriptISO("TALU"): _make_dedicated_script_info(
            "New Tai Lue",
            "und",
            ["New Tai Lue"],
            inference_priority=106,
        ),
        ScriptISO("NUSH"): _make_dedicated_script_info(
            "Nushu",
            "und",
            ["Nushu"],
            inference_priority=107,
        ),
        ScriptISO("OGAM"): _make_dedicated_script_info(
            "Ogham",
            "und",
            ["Ogham"],
            inference_priority=108,
        ),
        ScriptISO("OLCK"): _make_dedicated_script_info(
            "Ol Chiki",
            "und",
            ["Ol Chiki"],
            inference_priority=109,
        ),
        ScriptISO("HUNG"): _make_dedicated_script_info(
            "Old Hungarian",
            "und",
            ["Old Hungarian"],
            inference_priority=110,
        ),
        ScriptISO("ITAL"): _make_dedicated_script_info(
            "Old Italic",
            "und",
            ["Old Italic"],
            inference_priority=111,
        ),
        ScriptISO("NARB"): _make_dedicated_script_info(
            "Old North Arabian",
            "und",
            ["Old North Arabian"],
            inference_priority=112,
        ),
        ScriptISO("XPEO"): _make_dedicated_script_info(
            "Old Persian",
            "und",
            ["Old Persian"],
            inference_priority=113,
        ),
        ScriptISO("SARB"): _make_dedicated_script_info(
            "Old South Arabian",
            "und",
            ["Old South Arabian"],
            inference_priority=114,
        ),
        ScriptISO("ORKH"): _make_dedicated_script_info(
            "Old Turkic",
            "und",
            ["Old Turkic"],
            inference_priority=115,
        ),
        ScriptISO("OSMA"): _make_dedicated_script_info(
            "Osmanya",
            "und",
            ["Osmanya"],
            inference_priority=116,
        ),
        ScriptISO("HMNG"): _make_dedicated_script_info(
            "Pahawh Hmong",
            "und",
            ["Pahawh Hmong"],
            inference_priority=117,
        ),
        ScriptISO("PALM"): _make_dedicated_script_info(
            "Palmyrene",
            "und",
            ["Palmyrene"],
            inference_priority=118,
        ),
        ScriptISO("PAUC"): _make_dedicated_script_info(
            "Pau Cin Hau",
            "und",
            ["Pau Cin Hau"],
            inference_priority=119,
        ),
        ScriptISO("PHAG"): _make_dedicated_script_info(
            "Phags-pa",
            "und",
            ["Phags-pa"],
            inference_priority=120,
        ),
        ScriptISO("PHNX"): _make_dedicated_script_info(
            "Phoenician",
            "und",
            ["Phoenician"],
            inference_priority=121,
        ),
        ScriptISO("RUNR"): _make_dedicated_script_info(
            "Runic",
            "und",
            ["Runic"],
            inference_priority=122,
        ),
        ScriptISO("SAMR"): _make_dedicated_script_info(
            "Samaritan",
            "und",
            ["Samaritan"],
            inference_priority=123,
        ),
        ScriptISO("SHRD"): _make_dedicated_script_info(
            "Sharada",
            "und",
            ["Sharada"],
            optional_blocks=["Sharada Supplement"],
            inference_priority=124,
        ),
        ScriptISO("SHAW"): _make_dedicated_script_info(
            "Shavian",
            "und",
            ["Shavian"],
            inference_priority=125,
        ),
        ScriptISO("SIDD"): _make_dedicated_script_info(
            "Siddham",
            "und",
            ["Siddham"],
            inference_priority=126,
        ),
        ScriptISO("SGNW"): _make_dedicated_script_info(
            "SignWriting",
            "zxx",
            ["Sutton SignWriting"],
            inference_priority=127,
        ),
        ScriptISO("SORA"): _make_dedicated_script_info(
            "Sora Sompeng",
            "und",
            ["Sora Sompeng"],
            inference_priority=128,
        ),
        ScriptISO("SOYO"): _make_dedicated_script_info(
            "Soyombo",
            "und",
            ["Soyombo"],
            inference_priority=129,
        ),
        ScriptISO("TAKR"): _make_dedicated_script_info(
            "Takri",
            "und",
            ["Takri"],
            inference_priority=130,
        ),
        ScriptISO("TNSA"): _make_dedicated_script_info(
            "Tangsa",
            "und",
            ["Tangsa"],
            inference_priority=131,
        ),
        ScriptISO("UGAR"): _make_dedicated_script_info(
            "Ugaritic",
            "und",
            ["Ugaritic"],
            inference_priority=132,
        ),
        ScriptISO("ZANB"): _make_dedicated_script_info(
            "Zanabazar Square",
            "und",
            ["Zanabazar Square"],
            inference_priority=133,
        ),
        ScriptISO("HMNP"): _make_dedicated_script_info(
            "Nyiakeng Puachue Hmong",
            "und",
            ["Nyiakeng Puachue Hmong"],
            inference_priority=134,
        ),
        ScriptISO("OUGR"): _make_dedicated_script_info(
            "Old Uyghur",
            "und",
            ["Old Uyghur"],
            inference_priority=135,
        ),
        ScriptISO("OTSY"): _make_dedicated_script_info(
            "Ottoman Siyaq Numbers",
            "zxx",
            ["Ottoman Siyaq Numbers"],
            inference_priority=136,
        ),
        ScriptISO("TANG"): _make_dedicated_script_info(
            "Tangut",
            "und",
            ["Tangut"],
            optional_blocks=[
                "Tangut Components",
                "Tangut Supplement",
                "Tangut Components Supplement",
            ],
            inference_priority=137,
        ),
        ScriptISO("TOTO"): _make_dedicated_script_info(
            "Toto",
            "und",
            ["Toto"],
            inference_priority=138,
        ),
        ScriptISO("YEZI"): _make_dedicated_script_info(
            "Yezidi",
            "und",
            ["Yezidi"],
            inference_priority=139,
        ),
        ScriptISO("ZNAM"): _make_dedicated_script_info(
            "Znamenny Musical Notation",
            "zxx",
            ["Znamenny Musical Notation"],
            inference_priority=140,
        ),
        ScriptISO("PHAI"): _make_dedicated_script_info(
            "Phaistos Disc",
            "und",
            ["Phaistos Disc"],
            inference_priority=141,
        ),
    }
)

_SCRIPT_DISPLAY_LANGUAGE_OVERRIDES: dict[ScriptISO, str] = {
    ScriptISO("EGYP"): "egy",
    ScriptISO("ARMI"): "arc",
    ScriptISO("PRTI"): "xpr",
    ScriptISO("KHAR"): "pgd",
    ScriptISO("SIND"): "sd",
    ScriptISO("LINB"): "gmy",
    ScriptISO("LYCI"): "xlc",
    ScriptISO("LYDI"): "xld",
    ScriptISO("MAND"): "mid",
    ScriptISO("MANI"): "xmn",
    ScriptISO("MERO"): "xmr",
    ScriptISO("PLRD"): "hmd",
    ScriptISO("MODI"): "mr",
    ScriptISO("NBAT"): "arc",
    ScriptISO("TALU"): "khb",
    ScriptISO("OGAM"): "sga",
    ScriptISO("OLCK"): "sat",
    ScriptISO("HUNG"): "hu",
    ScriptISO("NARB"): "xna",
    ScriptISO("XPEO"): "peo",
    ScriptISO("SARB"): "xsa",
    ScriptISO("ORKH"): "otk",
    ScriptISO("OSMA"): "so",
    ScriptISO("HMNG"): "hmn",
    ScriptISO("PALM"): "arc",
    ScriptISO("PAUC"): "ctd",
    ScriptISO("PHAG"): "mn",
    ScriptISO("PHNX"): "phn",
    ScriptISO("SAMR"): "sam",
    ScriptISO("SHRD"): "ks",
    ScriptISO("SHAW"): "en",
    ScriptISO("SIDD"): "sa",
    ScriptISO("SORA"): "srb",
    ScriptISO("SOYO"): "mn",
    ScriptISO("TAKR"): "doi",
    ScriptISO("TNSA"): "nst",
    ScriptISO("UGAR"): "uga",
    ScriptISO("ZANB"): "mn",
    ScriptISO("HMNP"): "hnj",
    ScriptISO("OUGR"): "oui",
    ScriptISO("TANG"): "txg",
    ScriptISO("TOTO"): "txo",
    ScriptISO("YEZI"): "ku",
}

for _script_iso, _display_language in _SCRIPT_DISPLAY_LANGUAGE_OVERRIDES.items():
    SCRIPT_INFO[_script_iso]["display_language"] = _display_language


_SCRIPT_FONTSPEC_OPTION_OVERRIDES: dict[ScriptISO, str] = {
    ScriptISO("XSUX"): "Script={Sumero-Akkadian Cuneiform}",
    ScriptISO("KHAR"): "Script=Kharosthi",
    ScriptISO("MERO"): "Script={Meroitic Hieroglyphs}",
    ScriptISO("TALU"): "Script={Tai Lu}",
    ScriptISO("XPEO"): "Script={Old Persian Cuneiform}",
    ScriptISO("SGNW"): "Script={Sign Writing}",
    ScriptISO("UGAR"): "Script={Ugaritic Cuneiform}",
}

for _script_iso, _fontspec_opts in _SCRIPT_FONTSPEC_OPTION_OVERRIDES.items():
    SCRIPT_INFO[_script_iso]["fontspec_opts"] = _fontspec_opts


LANGUAGE_INFO: dict[str, LanguageInfo] = {
    "ae": LanguageInfo(
        canonical_name="Avestan",
        description="Avestan is an ancient Iranian language known primarily from Zoroastrian scripture. It is written in the Avestan script and is notable for surviving almost entirely in liturgical transmission.",
        scripts=[ScriptISO("AVST")],
        primary_script=ScriptISO("AVST"),
        required_blocks=["Avestan"],
        optional_blocks=[],
        sample="𐬀𐬁𐬂𐬃𐬄𐬅𐬆𐬇𐬈𐬉𐬊𐬋𐬌𐬍𐬎𐬏𐬐𐬑𐬒𐬓𐬔𐬕𐬖𐬗",
    ),
    "aho": LanguageInfo(
        canonical_name="Ahom",
        description="Ahom is a historical Tai language of Assam. It is written in the Ahom script in surviving manuscripts and is notable for its preservation in ritual and scholarly contexts after language shift.",
        scripts=[ScriptISO("AHOM")],
        primary_script=ScriptISO("AHOM"),
        required_blocks=["Ahom"],
        optional_blocks=["Ahom Supplement"],
        sample="𑜀𑜁𑜂𑜃𑜄𑜅𑜆𑜇𑜈𑜉𑜊𑜋𑜌𑜍𑜎𑜏𑜐𑜑𑜒𑜓𑜔𑜕𑜖𑜗",
    ),
    "am": LanguageInfo(
        canonical_name="Amharic",
        description="Amharic is an Ethiosemitic language spoken mainly in Ethiopia. It is written in the Ethiopic script and is notable as a major working language of the Ethiopian state.",
        scripts=[ScriptISO("ETHI")],
        primary_script=ScriptISO("ETHI"),
        required_blocks=["Ethiopic"],
        optional_blocks=["Ethiopic Supplement"],
        sample="ሰላም እንታይ ከመይ ኢኻ",
    ),
    "ar": LanguageInfo(
        canonical_name="Arabic",
        description="Arabic is a Semitic language spoken across the Middle East and North Africa. It is written in the Arabic script and is notable for its standardized written form alongside many regional spoken varieties.",
        scripts=[ScriptISO("ARAB")],
        primary_script=ScriptISO("ARAB"),
        required_blocks=["Arabic"],
        optional_blocks=["Arabic Supplement"],
        sample="صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    ),
    "ban": LanguageInfo(
        canonical_name="Balinese",
        description="Balinese is an Austronesian language spoken mainly on Bali. It is written today mostly in Latin, with the Balinese script preserved for traditional and cultural use.",
        scripts=[ScriptISO("BALI")],
        primary_script=ScriptISO("BALI"),
        required_blocks=["Balinese"],
        optional_blocks=[],
        sample="ᬀᬁᬂᬃᬄᬅᬆᬇᬈᬉᬊᬋᬌᬍᬎᬏᬐᬑᬒᬓᬔᬕᬖᬗ",
    ),
    "bax": LanguageInfo(
        canonical_name="Bamum",
        description="Bamum is a Grassfields language of Cameroon. It is written in Latin and historically in the Bamum script, which is notable as an indigenous royal creation.",
        scripts=[ScriptISO("BAMU")],
        primary_script=ScriptISO("BAMU"),
        required_blocks=["Bamum"],
        optional_blocks=[],
        sample="ꚠꚡꚢꚣꚤꚥꚦꚧꚨꚩꚪꚫꚬꚭꚮꚯꚰꚱꚲꚳꚴꚵꚶꚷ",
    ),
    "bbc": LanguageInfo(
        canonical_name="Batak Toba",
        description="Batak Toba is an Austronesian language of northern Sumatra. It is written mainly in Latin today and is notable for a historical literary tradition in the Batak script.",
        scripts=[ScriptISO("BATK")],
        primary_script=ScriptISO("BATK"),
        required_blocks=["Batak"],
        optional_blocks=[],
        sample="ᯀᯁᯂᯃᯄᯅᯆᯇᯈᯉᯊᯋᯌᯍᯎᯏᯐᯑᯒᯓᯔᯕᯖᯗ",
    ),
    "bho": LanguageInfo(
        canonical_name="Bhojpuri",
        description="Bhojpuri is an Indo-Aryan language of eastern India and Nepal. It is written mainly in Devanagari today and is notable for earlier documentary use of the Kaithi script.",
        scripts=[ScriptISO("KTHI"), ScriptISO("DEVA")],
        primary_script=ScriptISO("KTHI"),
        required_blocks=["Kaithi"],
        optional_blocks=["Devanagari"],
        sample="𑂀𑂁𑂂𑂃𑂄𑂅𑂆𑂇𑂈𑂉𑂊𑂋𑂌𑂍𑂎𑂏𑂐𑂑𑂒𑂓𑂔𑂕𑂖𑂗",
    ),
    "bn": LanguageInfo(
        canonical_name="Bengali",
        description="Bengali is an Indo-Aryan language spoken chiefly in Bangladesh and eastern India. It is written in the Bengali script and is notable for having one of the largest speaker populations in the world.",
        scripts=[ScriptISO("BENG")],
        primary_script=ScriptISO("BENG"),
        required_blocks=["Bengali"],
        optional_blocks=[],
        sample="আমি বাংলায় গান গাই",
    ),
    "bku": LanguageInfo(
        canonical_name="Buhid",
        description="Buhid is a Mangyan language of Mindoro in the Philippines. It is written in the Buhid script and is notable as part of a surviving indigenous Philippine writing tradition.",
        scripts=[ScriptISO("BUHD")],
        primary_script=ScriptISO("BUHD"),
        required_blocks=["Buhid"],
        optional_blocks=[],
        sample="ᝀᝁᝂᝃᝄᝅᝆᝇᝈᝉᝊᝋᝌᝍᝎᝏᝐᝑ᜵᜶",
    ),
    "bug": LanguageInfo(
        canonical_name="Buginese",
        description="Buginese is an Austronesian language of South Sulawesi. It is written mainly in Latin today and is notable for a substantial earlier manuscript tradition in the Buginese script.",
        scripts=[ScriptISO("BUGI")],
        primary_script=ScriptISO("BUGI"),
        required_blocks=["Buginese"],
        optional_blocks=[],
        sample="ᨀᨁᨂᨃᨄᨅᨆᨇᨈᨉᨊᨋᨌᨍᨎᨏᨐᨑᨒᨓᨔᨕᨖꧏ᨞᨟",
    ),
    "bsq": LanguageInfo(
        canonical_name="Bassa",
        description="Bassa is a Niger-Congo language of Liberia and Sierra Leone. It is written in Latin and Bassa Vah and is notable for the dedicated modern script created for it.",
        scripts=[ScriptISO("BASS")],
        primary_script=ScriptISO("BASS"),
        required_blocks=["Bassa Vah"],
        optional_blocks=[],
        sample="𖫐𖫑𖫒𖫓𖫔𖫕𖫖𖫗𖫘𖫙𖫚𖫛𖫜𖫝𖫞𖫟𖫠𖫡𖫢𖫣𖫤𖫥𖫦𖫧",
    ),
    "cop": LanguageInfo(
        canonical_name="Coptic",
        description="Coptic is the latest recorded stage of the Egyptian language. It is written in the Coptic script and is notable for continuing as a liturgical language of the Coptic Church.",
        scripts=[ScriptISO("COPT")],
        primary_script=ScriptISO("COPT"),
        required_blocks=["Coptic"],
        optional_blocks=["Coptic Epact Numbers"],
        sample="ϢϣϤϥϦϧϨϩϪϫϬϭϮϯⲀⲁⲂⲃⲄⲅⲆⲇⲈⲉ",
    ),
    "ccp": LanguageInfo(
        canonical_name="Chakma",
        description="Chakma is an Indo-Aryan language spoken in Bangladesh and northeastern India. It is written in the Chakma script and is notable for maintaining a distinct script alongside dominant regional writing systems.",
        scripts=[ScriptISO("CHAK")],
        primary_script=ScriptISO("CHAK"),
        required_blocks=["Chakma"],
        optional_blocks=[],
        sample="𑄃𑄄𑄅𑄆𑄇𑄈𑄉𑄊𑄋𑄌𑄍𑄎𑄏𑄐𑄑𑄒𑄓𑄔𑄕𑄖𑄗𑄘𑄙𑄚",
    ),
    "cr": LanguageInfo(
        canonical_name="Cree",
        description="Cree is a continuum of Algonquian varieties spoken across Canada. It is written in Canadian syllabics and Latin orthographies and is notable for broad regional adaptation of the syllabic system.",
        scripts=[ScriptISO("CANS"), ScriptISO("LATN")],
        primary_script=ScriptISO("CANS"),
        required_blocks=["Unified Canadian Aboriginal Syllabics"],
        optional_blocks=["Unified Canadian Aboriginal Syllabics Extended"],
        sample="᐀ᐁᐂᐃᐄᐅᐆᐇᐈᐉᐊᐋᐌᐍᐎᐏᐐᐑᐒᐓᐔᐕᐖᐗ",
    ),
    "cu": LanguageInfo(
        canonical_name="Church Slavic",
        description="Church Slavic is a liturgical Slavic language used in Orthodox Christian traditions. It is written historically in Glagolitic and Cyrillic and is notable for its religious rather than vernacular function.",
        scripts=[ScriptISO("GLAG"), ScriptISO("CYRL")],
        primary_script=ScriptISO("GLAG"),
        required_blocks=["Glagolitic"],
        optional_blocks=["Glagolitic Supplement"],
        sample="ⰀⰁⰂⰃⰄⰅⰆⰇⰈⰉⰊⰋⰌⰍⰎⰏⰐⰑⰒⰓⰔⰕⰖⰗ",
    ),
    "cjm": LanguageInfo(
        canonical_name="Eastern Cham",
        description="Eastern Cham is an Austronesian language of Vietnam and Cambodia. It is written in the Cham script and is notable for preserving one branch of the older Cham literary tradition.",
        scripts=[ScriptISO("CHAM")],
        primary_script=ScriptISO("CHAM"),
        required_blocks=["Cham"],
        optional_blocks=[],
        sample="ꨀꨁꨂꨃꨄꨅꨆꨇꨈꨉꨊꨋꨌꨍꨎꨏꨐꨑꨒꨓꨔꨕꨖꨗ",
    ),
    "ecy": LanguageInfo(
        canonical_name="Eteocypriot",
        description="Eteocypriot is an extinct language of ancient Cyprus. It is written in the Cypriot Syllabary and is notable because its linguistic affiliation remains uncertain.",
        scripts=[ScriptISO("CPRT")],
        primary_script=ScriptISO("CPRT"),
        required_blocks=["Cypriot Syllabary"],
        optional_blocks=[],
        sample="𐠀𐠁𐠂𐠃𐠄𐠅𐠆𐠇𐠈𐠉𐠊𐠋𐠌𐠍𐠎𐠏𐠐𐠑𐠒𐠓𐠔𐠕𐠖𐠗",
    ),
    "chr": LanguageInfo(
        canonical_name="Cherokee",
        description="Cherokee is an Iroquoian language of the southeastern United States. It is written in the Cherokee syllabary and Latin and is notable for the successful script created by Sequoyah.",
        scripts=[ScriptISO("CHER")],
        primary_script=ScriptISO("CHER"),
        required_blocks=["Cherokee"],
        optional_blocks=["Cherokee Supplement"],
        sample="ᎣᏏᏲ",
    ),
    "de": LanguageInfo(
        canonical_name="German",
        description="German is a West Germanic language spoken mainly in Germany, Austria, and Switzerland. It is written in the Latin script and is notable for productive word compounding and a standardized written norm.",
        scripts=[ScriptISO("LATN")],
        primary_script=ScriptISO("LATN"),
        required_blocks=["Basic Latin"],
        optional_blocks=["Latin-1 Supplement", "Latin Extended-A"],
        sample="Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
    ),
    "doi": LanguageInfo(
        canonical_name="Dogri",
        description="Dogri is an Indo-Aryan language of the Jammu region. It is written mainly in Devanagari today and is notable for historical use of the Dogra script.",
        scripts=[ScriptISO("DOGR"), ScriptISO("DEVA")],
        primary_script=ScriptISO("DOGR"),
        required_blocks=["Dogra"],
        optional_blocks=["Devanagari", "Devanagari Extended-A"],
        sample="𑠖𑠮𑠝𑠳 𑠛𑠯𑠬𑠬𑠰",
    ),
    "dv": LanguageInfo(
        canonical_name="Dhivehi",
        description="Dhivehi is an Indo-Aryan language of the Maldives. It is written in Thaana and historically in Dives Akuru and is notable for using a modern right-to-left script in South Asia.",
        scripts=[ScriptISO("DIAK"), ScriptISO("THAA")],
        primary_script=ScriptISO("DIAK"),
        required_blocks=["Dives Akuru"],
        optional_blocks=["Thaana"],
        sample="𑤀𑤂𑤄 𑤋𑤢𑤼",
    ),
    "el": LanguageInfo(
        canonical_name="Greek",
        description="Greek is the principal Hellenic language of Greece and Cyprus. It is written in the Greek alphabet and is notable for an exceptionally long continuous written history.",
        scripts=[ScriptISO("GREK")],
        primary_script=ScriptISO("GREK"),
        required_blocks=["Greek and Coptic"],
        optional_blocks=[],
        sample="Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    ),
    "xly": LanguageInfo(
        canonical_name="Elymaic",
        description="Elymaic is an extinct Iranian language attested in a small number of inscriptions from ancient Elymais. It is written in the Elymaic script and is notable for sparse documentary survival within the late Parthian world.",
        scripts=[ScriptISO("ELYM")],
        primary_script=ScriptISO("ELYM"),
        required_blocks=["Elymaic"],
        optional_blocks=[],
        sample="𐿠𐿡𐿢𐿣𐿤𐿥𐿦𐿧𐿨𐿩𐿪𐿫𐿬𐿭𐿮𐿯𐿰𐿱𐿲𐿳𐿴𐿵𐿶",
    ),
    "en": LanguageInfo(
        canonical_name="English",
        description="English is a West Germanic language with global use as a first or second language. It is written in the Latin script and is notable for its worldwide role in education, science, and commerce.",
        scripts=[ScriptISO("LATN"), ScriptISO("DSRT")],
        primary_script=ScriptISO("LATN"),
        required_blocks=["Basic Latin"],
        optional_blocks=["Latin-1 Supplement"],
        sample="The quick brown fox jumps over the lazy dog",
    ),
    "es": LanguageInfo(
        canonical_name="Spanish",
        description="Spanish is a Romance language spoken in Spain and much of the Americas. It is written in the Latin script and is notable for its large transcontinental speech community.",
        scripts=[ScriptISO("LATN")],
        primary_script=ScriptISO("LATN"),
        required_blocks=["Basic Latin"],
        optional_blocks=["Latin-1 Supplement"],
        sample="El veloz murciélago hindú comía feliz cardillo y kiwi",
    ),
    "fr": LanguageInfo(
        canonical_name="French",
        description="French is a Romance language spoken in France and many other parts of the world. It is written in the Latin script and is notable for its broad international institutional use.",
        scripts=[ScriptISO("LATN")],
        primary_script=ScriptISO("LATN"),
        required_blocks=["Basic Latin"],
        optional_blocks=["Latin-1 Supplement"],
        sample="Portez ce vieux whisky au juge blond qui fume",
    ),
    "ff": LanguageInfo(
        canonical_name="Fulah",
        description="Fulah is a Niger-Congo language continuum spoken across the Sahel and West Africa. It is written in Latin, Arabic, and Adlam and is notable for the recent spread of a dedicated modern script.",
        scripts=[ScriptISO("ADLM"), ScriptISO("LATN")],
        primary_script=ScriptISO("ADLM"),
        required_blocks=["Adlam"],
        optional_blocks=["Arabic"],
        sample="𞤀𞤁𞤂𞤃𞤄𞤅𞤆𞤇𞤈𞤉𞤊𞤋𞤌𞤍𞤎𞤏𞤐𞤑𞤒𞤓𞤔𞤕𞤖𞤗",
    ),
    "gu": LanguageInfo(
        canonical_name="Gujarati",
        description="Gujarati is an Indo-Aryan language of western India and the Gujarati diaspora. It is written in the Gujarati script and is notable for a long mercantile and literary tradition.",
        scripts=[ScriptISO("GUJR")],
        primary_script=ScriptISO("GUJR"),
        required_blocks=["Gujarati"],
        optional_blocks=["Gujarati Supplement"],
        sample="ઁંઃઅઆઇઈઉઊઋઌઍએઐઑઓઔકખગઘઙચછ",
    ),
    "got": LanguageInfo(
        canonical_name="Gothic",
        description="Gothic is an extinct East Germanic language. It is written in the Gothic script and is notable for being known mainly from a relatively small corpus of biblical translation material.",
        scripts=[ScriptISO("GOTH")],
        primary_script=ScriptISO("GOTH"),
        required_blocks=["Gothic"],
        optional_blocks=[],
        sample="𐌰𐌱𐌲𐌳𐌴𐌵𐌶𐌷𐌸𐌹𐌺𐌻𐌼𐌽𐌾𐌿𐍀𐍁𐍂𐍃𐍄𐍅𐍆𐍇",
    ),
    "hlu": LanguageInfo(
        canonical_name="Hieroglyphic Luwian",
        description="Hieroglyphic Luwian is an extinct Anatolian language of the late Bronze and Iron Ages. It is written in Anatolian Hieroglyphs and is notable for monumental inscriptions in ancient Anatolia.",
        scripts=[ScriptISO("HLUW")],
        primary_script=ScriptISO("HLUW"),
        required_blocks=["Anatolian Hieroglyphs"],
        optional_blocks=[],
        sample="𔐀𔐁𔐂𔐃𔐄𔐅𔐆𔐇𔐈𔐉𔐊𔐋𔐌𔐍𔐎𔐏𔐐𔐑𔐒𔐓𔐔𔐕𔐖𔐗",
    ),
    "gon": LanguageInfo(
        canonical_name="Gondi",
        description="Gondi is a Dravidian language spoken in central India. It is written in several scripts, including Gunjala Gondi and Masaram Gondi, and is notable for having more than one dedicated modern encoded script.",
        scripts=[ScriptISO("GONG"), ScriptISO("GONM")],
        primary_script=ScriptISO("GONG"),
        required_blocks=["Gunjala Gondi"],
        optional_blocks=["Masaram Gondi"],
        sample="𑵠𑵡𑵢𑵣𑵤𑵥𑵦𑵧𑵨𑵩𑵪𑵫𑵬𑵭𑵮𑵯𑵰𑵱𑵲𑵳𑵴𑵵𑵶𑵷",
    ),
    "hoc": LanguageInfo(
        canonical_name="Ho",
        description="Ho is an Austroasiatic language spoken mainly in eastern India. It is written in Warang Citi and other regional scripts and is notable for its community-created modern alphabet.",
        scripts=[ScriptISO("WARA")],
        primary_script=ScriptISO("WARA"),
        required_blocks=["Warang Citi"],
        optional_blocks=[],
        sample="𑢠𑢡𑢢𑢣𑢤𑢥𑢦𑢧𑢨𑢩𑢪𑢫𑢬𑢭𑢮𑢯𑢰𑢱𑢲𑢳𑢴𑢵𑢶𑢷",
    ),
    "hnn": LanguageInfo(
        canonical_name="Hanunoo",
        description="Hanunoo is a Mangyan language of Mindoro in the Philippines. It is written in the Hanunoo script and is notable for continued traditional writing practices.",
        scripts=[ScriptISO("HANO")],
        primary_script=ScriptISO("HANO"),
        required_blocks=["Hanunoo"],
        optional_blocks=[],
        sample="ᜠᜡᜢᜣᜤᜥᜦᜧᜨᜩᜪᜫᜬᜭᜮᜯᜰᜱᜲᜳ᜴",
    ),
    "he": LanguageInfo(
        canonical_name="Hebrew",
        description="Hebrew is a Northwest Semitic language used in Israel and Jewish communities worldwide. It is written in the Hebrew script and is notable for combining ancient liturgical continuity with modern vernacular revival.",
        scripts=[ScriptISO("HEBR")],
        primary_script=ScriptISO("HEBR"),
        required_blocks=["Hebrew"],
        optional_blocks=[],
        sample="דג סקרן שט בים מאוכזב ולפתע מצא לו חברה",
    ),
    "hi": LanguageInfo(
        canonical_name="Hindi",
        description="Hindi is an Indo-Aryan language spoken mainly in northern and central India. It is written in Devanagari and is notable as one of the major standardized languages of modern India.",
        scripts=[ScriptISO("DEVA")],
        primary_script=ScriptISO("DEVA"),
        required_blocks=["Devanagari"],
        optional_blocks=[],
        sample="सभी मनुष्य जन्म से स्वतंत्र और समान अधिकारों वाले हैं",
    ),
    "hy": LanguageInfo(
        canonical_name="Armenian",
        description="Armenian is an Indo-European language spoken in Armenia and the Armenian diaspora. It is written in the Armenian alphabet and is notable for a literary tradition extending back to late antiquity.",
        scripts=[ScriptISO("ARMN")],
        primary_script=ScriptISO("ARMN"),
        required_blocks=["Armenian"],
        optional_blocks=[],
        sample="Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    ),
    "ii": LanguageInfo(
        canonical_name="Nuosu (Yi)",
        description="Nuosu is a Loloish language spoken mainly in southwest China. It is written in the Yi script and is notable for the modern standardization of a large syllabary.",
        scripts=[ScriptISO("YIII")],
        primary_script=ScriptISO("YIII"),
        required_blocks=["Yi Syllables"],
        optional_blocks=[],
        sample="ꆈꌠꉙ ꉙꄜꐨ",
    ),
    "it": LanguageInfo(
        canonical_name="Italian",
        description="Italian is a Romance language spoken mainly in Italy and nearby regions. It is written in the Latin script and is notable for continuity with the literary prestige of Tuscan.",
        scripts=[ScriptISO("LATN")],
        primary_script=ScriptISO("LATN"),
        required_blocks=["Basic Latin"],
        optional_blocks=["Latin-1 Supplement"],
        sample="Ma la volpe col suo balzo ha raggiunto il quieto Fido",
    ),
    "ja": LanguageInfo(
        canonical_name="Japanese",
        description="Japanese is a Japonic language spoken mainly in Japan. It uses a mixed writing system of kanji, hiragana, and katakana and is notable for routine multi-script text.",
        scripts=[ScriptISO("JPAN"), ScriptISO("HIRA"), ScriptISO("KANA")],
        primary_script=ScriptISO("JPAN"),
        required_blocks=["Hiragana"],
        optional_blocks=["Katakana", "CJK Unified Ideographs"],
        sample="いろはにほへと ちりぬるを",
    ),
    "jv": LanguageInfo(
        canonical_name="Javanese",
        description="Javanese is an Austronesian language of Java. It is written mainly in Latin today and is notable for a historical literary tradition in the Javanese script.",
        scripts=[ScriptISO("JAVA")],
        primary_script=ScriptISO("JAVA"),
        required_blocks=["Javanese"],
        optional_blocks=[],
        sample="ꦀꦁꦂꦃꦄꦅꦆꦇꦈꦉꦊꦋꦌꦍꦎꦏꦐꦑꦒꦓꦔꦕꦖꦗ",
    ),
    "kaw": LanguageInfo(
        canonical_name="Old Javanese",
        description="Old Javanese, also known as Kawi, is a historical Austronesian language of Java and Bali. It is written in the Kawi script and is notable for a major corpus of literary, epigraphic, and courtly texts.",
        scripts=[ScriptISO("KAWI")],
        primary_script=ScriptISO("KAWI"),
        required_blocks=["Kawi"],
        optional_blocks=[],
        sample="𑼄𑼅𑼆𑼇𑼈𑼉𑼊𑼋𑼌𑼍𑼎𑼏𑼐𑼒𑼓𑼔𑼕𑼖𑼗𑼘𑼙𑼚𑼛𑼜",
    ),
    "ka": LanguageInfo(
        canonical_name="Georgian",
        description="Georgian is a Kartvelian language spoken mainly in Georgia. It is written in the Georgian script and is notable for a long native literary and inscriptional tradition.",
        scripts=[ScriptISO("GEOR")],
        primary_script=ScriptISO("GEOR"),
        required_blocks=["Georgian"],
        optional_blocks=[],
        sample="ქართული ტექსტის მაგალითი",
    ),
    "km": LanguageInfo(
        canonical_name="Khmer",
        description="Khmer is an Austroasiatic language spoken mainly in Cambodia. It is written in the Khmer script and is notable for one of the oldest continuous inscriptional traditions in mainland Southeast Asia.",
        scripts=[ScriptISO("KHMR")],
        primary_script=ScriptISO("KHMR"),
        required_blocks=["Khmer"],
        optional_blocks=[],
        sample="មនុស្សទាំងអស់កើតមកមានសេរីភាព",
    ),
    "kn": LanguageInfo(
        canonical_name="Kannada",
        description="Kannada is a Dravidian language spoken mainly in Karnataka. It is written in the Kannada script and is notable for a long literary history in South India.",
        scripts=[ScriptISO("KNDA")],
        primary_script=ScriptISO("KNDA"),
        required_blocks=["Kannada"],
        optional_blocks=["Kannada Supplement"],
        sample="ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞ",
    ),
    "ko": LanguageInfo(
        canonical_name="Korean",
        description="Korean is the principal Koreanic language of the Korean Peninsula. It is written in Hangul and is notable for a scientifically designed script organized into syllable blocks.",
        scripts=[ScriptISO("HANG")],
        primary_script=ScriptISO("HANG"),
        required_blocks=["Hangul Syllables"],
        optional_blocks=[],
        sample="키스의 고유조건은 입술끼리 만나야 하고 특별한 기술은 필요치 않다",
    ),
    "lo": LanguageInfo(
        canonical_name="Lao",
        description="Lao is a Kra-Dai language spoken mainly in Laos. It is written in the Lao script and is notable for close historical and structural ties to Thai.",
        scripts=[ScriptISO("LAOO")],
        primary_script=ScriptISO("LAOO"),
        required_blocks=["Lao"],
        optional_blocks=[],
        sample="ພາສາລາວເປັນພາສາທີ່ສວຍງາມ",
    ),
    "lep": LanguageInfo(
        canonical_name="Lepcha",
        description="Lepcha is a Tibeto-Burman language of Sikkim and nearby Himalayan regions. It is written in the Lepcha script and is notable for an indigenous regional writing tradition.",
        scripts=[ScriptISO("LEPC")],
        primary_script=ScriptISO("LEPC"),
        required_blocks=["Lepcha"],
        optional_blocks=[],
        sample="ᰀᰁᰂᰃᰄᰅᰆᰇᰈᰉᰊᰋᰌᰍᰎᰏᰐᰑᰒᰓᰔᰕᰖᰗ",
    ),
    "lif": LanguageInfo(
        canonical_name="Limbu",
        description="Limbu is a Kiranti language spoken in eastern Nepal and India. It is written in Limbu and Devanagari and is notable for preservation of its own script tradition.",
        scripts=[ScriptISO("LIMB")],
        primary_script=ScriptISO("LIMB"),
        required_blocks=["Limbu"],
        optional_blocks=[],
        sample="ᤀᤁᤂᤃᤄᤅᤆᤇᤈᤉᤊᤋᤌᤍᤎᤏᤐᤑᤒᤓᤔᤕᤖᤗ",
    ),
    "lis": LanguageInfo(
        canonical_name="Lisu",
        description="Lisu is a Tibeto-Burman language spoken in China, Myanmar, Thailand, and neighboring regions. It is written in the Lisu script and is notable for a missionary-era alphabet that became a standard orthography.",
        scripts=[ScriptISO("LISU")],
        primary_script=ScriptISO("LISU"),
        required_blocks=["Lisu"],
        optional_blocks=[],
        sample="ꓐꓑꓒꓓꓔꓕꓖꓗꓘꓙꓚꓛꓜꓝꓞꓟꓠꓡꓢꓣꓤꓥꓦꓧ",
    ),
    "my": LanguageInfo(
        canonical_name="Burmese",
        description="Burmese is a Sino-Tibetan language spoken mainly in Myanmar. It is written in the Myanmar script and is notable as the dominant literary and administrative language of the country.",
        scripts=[ScriptISO("MYMR")],
        primary_script=ScriptISO("MYMR"),
        required_blocks=["Myanmar"],
        optional_blocks=["Myanmar Extended-A"],
        sample="မြန်မာစာသည် လှပသော ဘာသာဖြစ်သည်",
    ),
    "dmf": LanguageInfo(
        canonical_name="Medefaidrin",
        description="Medefaidrin is a planned liturgical language created by a Christian community in southeastern Nigeria. It is written in the Medefaidrin script and is notable for being both a constructed language and a community-specific script tradition.",
        scripts=[ScriptISO("MEDF")],
        primary_script=ScriptISO("MEDF"),
        required_blocks=["Medefaidrin"],
        optional_blocks=[],
        sample="𖹀𖹁𖹂𖹃𖹄𖹅𖹆𖹇𖹈𖹉𖹊𖹋𖹌𖹍𖹎𖹏𖹐𖹑𖹒𖹓𖹔𖹕𖹖𖹗",
    ),
    "men": LanguageInfo(
        canonical_name="Mende",
        description="Mende is a Mande language spoken mainly in Sierra Leone. It is written in Latin and Mende Kikakui and is notable for one of the better known modern indigenous African syllabaries.",
        scripts=[ScriptISO("MEND")],
        primary_script=ScriptISO("MEND"),
        required_blocks=["Mende Kikakui"],
        optional_blocks=[],
        sample="𞠀𞠁𞠂𞠃𞠄𞠅𞠆𞠇𞠈𞠉𞠊𞠋𞠌𞠍𞠎𞠏𞠐𞠑𞠒𞠓𞠔𞠕𞠖𞠗",
    ),
    "mn": LanguageInfo(
        canonical_name="Mongolian",
        description="Mongolian is a Mongolic language spoken in Mongolia and parts of China. It is written in Cyrillic and the traditional Mongolian script and is notable for the survival of a vertical historical script.",
        scripts=[ScriptISO("MONG")],
        primary_script=ScriptISO("MONG"),
        required_blocks=["Mongolian"],
        optional_blocks=[],
        sample="ᠠᠡᠢᠣᠤᠥᠦᠧᠨᠩᠪᠫᠬᠭᠮᠯᠰᠱᠲᠳᠴᠵᠶᠷ",
    ),
    "mni": LanguageInfo(
        canonical_name="Manipuri",
        description="Manipuri, also called Meitei, is a Tibeto-Burman language of Manipur. It is written in Meetei Mayek and is notable for the modern restoration of its historical script.",
        scripts=[ScriptISO("MTEI")],
        primary_script=ScriptISO("MTEI"),
        required_blocks=["Meetei Mayek"],
        optional_blocks=["Meetei Mayek Extensions"],
        sample="ꯀꯁꯂꯃꯄꯅꯆꯇꯈꯉꯊꯋꯌꯍꯎꯏꯐꯑꯒꯓꯔꯕꯖꯗ",
    ),
    "new": LanguageInfo(
        canonical_name="Newar",
        description="Newar is a Tibeto-Burman language of the Kathmandu Valley. It is written today mainly in Devanagari and is notable for an older manuscript tradition in the Newa script.",
        scripts=[ScriptISO("NEWA")],
        primary_script=ScriptISO("NEWA"),
        required_blocks=["Newa"],
        optional_blocks=[],
        sample="𑐀𑐁𑐂𑐃𑐄𑐅𑐆𑐇𑐈𑐉𑐊𑐋𑐌𑐍𑐎𑐏𑐐𑐑𑐒𑐓𑐔𑐕𑐖𑐗",
    ),
    "nqo": LanguageInfo(
        canonical_name="NKo",
        description="NKo is a standardized written language form used for Manding varieties in West Africa. It is written in the NKo script and is notable for a modern literacy movement built around a dedicated orthography.",
        scripts=[ScriptISO("NKOO")],
        primary_script=ScriptISO("NKOO"),
        required_blocks=["NKo"],
        optional_blocks=[],
        sample="߀߁߂߃߄߅߆߇߈߉ߊߋߌߍߎߏߐߑߒߓߔߕߖߗ",
    ),
    "osa": LanguageInfo(
        canonical_name="Osage",
        description="Osage is a Dhegiha Siouan language of Oklahoma. It is written in the Osage script and is notable for a recent community-led orthographic standardization.",
        scripts=[ScriptISO("OSGE")],
        primary_script=ScriptISO("OSGE"),
        required_blocks=["Osage"],
        optional_blocks=[],
        sample="𐒰𐒱𐒲𐒳𐒴𐒵𐒶𐒷𐒸𐒹𐒺𐒻𐒼𐒽𐒾𐒿𐓀𐓁𐓂𐓃𐓄𐓅𐓆𐓇",
    ),
    "pli": LanguageInfo(
        canonical_name="Pali",
        description="Pali is a Middle Indo-Aryan language used mainly in Theravada Buddhist canon and scholarship. It is written in many Indic scripts and is notable more as a liturgical and textual language than as a vernacular.",
        scripts=[ScriptISO("BHKS")],
        primary_script=ScriptISO("BHKS"),
        required_blocks=["Bhaiksuki"],
        optional_blocks=[],
        sample="𑰀𑰁𑰂𑰃𑰄𑰅𑰆𑰇𑰈𑰉𑰊𑰋𑰌𑰍𑰎𑰏𑰐𑰑𑰒𑰓𑰔𑰕𑰖𑰗",
    ),
    "ml": LanguageInfo(
        canonical_name="Malayalam",
        description="Malayalam is a Dravidian language spoken mainly in Kerala. It is written in the Malayalam script and is notable for a substantial literary tradition and a distinct regional standard.",
        scripts=[ScriptISO("MLYM")],
        primary_script=ScriptISO("MLYM"),
        required_blocks=["Malayalam"],
        optional_blocks=["Malayalam Supplement"],
        sample="അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞ",
    ),
    "mro": LanguageInfo(
        canonical_name="Mro",
        description="Mro is a Tibeto-Burman language spoken in the Chittagong Hill Tracts and nearby areas. It is written in the Mro script and is notable for a recently adopted dedicated writing system.",
        scripts=[ScriptISO("MROO")],
        primary_script=ScriptISO("MROO"),
        required_blocks=["Mro"],
        optional_blocks=[],
        sample="𖩠𖩡𖩢𖩣𖩤𖩥𖩦𖩧𖩨𖩩𖩪𖩫𖩬𖩭𖩮𖩯𖩰𖩱𖩲𖩳𖩴𖩵𖩶𖩷",
    ),
    "kv": LanguageInfo(
        canonical_name="Komi",
        description="Komi is a Uralic language spoken in northeastern Europe. It is written mainly in Cyrillic and is notable for historical use of the Old Permic script.",
        scripts=[ScriptISO("PERM"), ScriptISO("CYRL")],
        primary_script=ScriptISO("PERM"),
        required_blocks=["Old Permic"],
        optional_blocks=["Cyrillic"],
        sample="𐍐𐍑𐍒𐍓𐍔𐍕𐍖𐍗𐍘𐍙𐍚𐍛𐍜𐍝𐍞𐍟𐍠𐍡𐍢𐍣𐍤𐍥𐍦𐍧",
    ),
    "pal": LanguageInfo(
        canonical_name="Middle Persian",
        description="Middle Persian is an extinct Southwestern Iranian language of the Sasanian era. It is written in Pahlavi scripts and is notable for its importance in royal, administrative, and Zoroastrian texts.",
        scripts=[ScriptISO("PHLP"), ScriptISO("PHLI")],
        primary_script=ScriptISO("PHLP"),
        required_blocks=["Psalter Pahlavi"],
        optional_blocks=["Inscriptional Pahlavi"],
        sample="𐮀𐮁𐮂𐮃𐮄𐮅𐮆𐮇𐮈𐮉𐮊𐮋𐮌𐮍𐮎𐮏𐮐𐮑𐮒𐮓𐮔𐮕𐮖𐮗",
    ),
    "or": LanguageInfo(
        canonical_name="Odia",
        description="Odia is an Indo-Aryan language spoken mainly in Odisha. It is written in the Odia script and is notable for a long literary tradition in eastern India.",
        scripts=[ScriptISO("ORYA")],
        primary_script=ScriptISO("ORYA"),
        required_blocks=["Oriya"],
        optional_blocks=[],
        sample="ଅଆଇଈଉଊଋଏଐଓଔକଖଗଘଙଚଛଜଝଞ",
    ),
    "sog": LanguageInfo(
        canonical_name="Sogdian",
        description="Sogdian is an extinct Eastern Iranian language of Central Asia. It is written in Sogdian and Old Sogdian and is notable for its role as a commercial lingua franca on the Silk Road.",
        scripts=[ScriptISO("SOGD"), ScriptISO("SOGO")],
        primary_script=ScriptISO("SOGD"),
        required_blocks=["Sogdian"],
        optional_blocks=["Old Sogdian"],
        sample="𐼰𐼱𐼲𐼳𐼴𐼵𐼶𐼷𐼸𐼹𐼺𐼻𐼼𐼽𐼾𐼿𐽀𐽁𐽂𐽃𐽄𐽅𐽆𐽇",
    ),
    "su": LanguageInfo(
        canonical_name="Sundanese",
        description="Sundanese is an Austronesian language of West Java. It is written mainly in Latin today and is notable for a revived regional script used in education and public signage.",
        scripts=[ScriptISO("SUND")],
        primary_script=ScriptISO("SUND"),
        required_blocks=["Sundanese"],
        optional_blocks=["Sundanese Supplement"],
        sample="ᮃᮄᮅᮆᮇᮈᮉᮊᮋᮌᮍᮎᮏᮐᮑᮒᮓᮔᮕᮖᮗᮘᮙᮚ",
    ),
    "syl": LanguageInfo(
        canonical_name="Sylheti",
        description="Sylheti is an Eastern Indo-Aryan language of northeastern Bangladesh and adjacent India. It is written mainly in Bengali today and is notable for a historical regional script, Syloti Nagri.",
        scripts=[ScriptISO("SYLO")],
        primary_script=ScriptISO("SYLO"),
        required_blocks=["Syloti Nagri"],
        optional_blocks=[],
        sample="ꠀꠁꠂꠃꠄꠅ꠆ꠇꠈꠉꠊꠋꠌꠍꠎꠏꠐꠑꠒꠓꠔꠕꠖꠗ",
    ),
    "syr": LanguageInfo(
        canonical_name="Syriac",
        description="Syriac is a Middle Aramaic language of Christian communities in the Middle East. It is written in the Syriac script and is notable for its liturgical and scholarly significance.",
        scripts=[ScriptISO("SYRC")],
        primary_script=ScriptISO("SYRC"),
        required_blocks=["Syriac"],
        optional_blocks=["Syriac Supplement"],
        sample="ܐܒܓܕ ܗܘܙܚ ܛܝܟܠ ܡܢܣܥ",
    ),
    "tl": LanguageInfo(
        canonical_name="Tagalog",
        description="Tagalog is an Austronesian language of the Philippines and a major base of the national language. It is written in Latin today and is notable for historical use of the Tagalog or Baybayin script.",
        scripts=[ScriptISO("TGLG"), ScriptISO("LATN")],
        primary_script=ScriptISO("TGLG"),
        required_blocks=["Tagalog"],
        optional_blocks=["Basic Latin"],
        sample="ᜀᜁᜂᜃᜄᜅᜆᜇᜈᜉᜊᜋᜌᜎᜏᜐᜑᜒᜓ᜔",
    ),
    "und": LanguageInfo(
        canonical_name="Undetermined",
        description="Undetermined is a placeholder code used when no specific language can be assigned. In this table it marks undeciphered or unidentified content associated with the Cypro-Minoan script.",
        scripts=[ScriptISO("CPMN")],
        primary_script=ScriptISO("CPMN"),
        required_blocks=["Cypro-Minoan"],
        optional_blocks=[],
        sample="𒾐𒾑𒾒𒾓𒾔𒾕𒾖𒾗𒾘𒾙𒾚𒾛𒾜𒾝𒾞𒾟𒾠𒾡𒾢𒾣𒾤𒾥𒾦𒾧",
    ),
    "tbw": LanguageInfo(
        canonical_name="Tagbanwa",
        description="Tagbanwa is an Austronesian language of Palawan in the Philippines. It is written in the Tagbanwa script and is notable as part of a surviving indigenous script tradition.",
        scripts=[ScriptISO("TAGB")],
        primary_script=ScriptISO("TAGB"),
        required_blocks=["Tagbanwa"],
        optional_blocks=[],
        sample="ᝠᝡᝢᝣᝤᝥᝦᝧᝨᝩᝪᝫᝬᝮᝯᝰᝲᝳ᝴",
    ),
    "nod": LanguageInfo(
        canonical_name="Northern Thai",
        description="Northern Thai is a Southwestern Tai language of northern Thailand. It is written in Tai Tham and is notable for a manuscript tradition shared with Buddhist texts in the region.",
        scripts=[ScriptISO("LANA")],
        primary_script=ScriptISO("LANA"),
        required_blocks=["Tai Tham"],
        optional_blocks=[],
        sample="ᨠᨡᨢᨣᨤᨥᨦᨧᨨᨩᨪᨫᨬᨭᨮᨯᨰᨱᨲᨳᨴᨵᨶᨷ",
    ),
    "blt": LanguageInfo(
        canonical_name="Tai Dam",
        description="Tai Dam is a Southwestern Tai language spoken in mainland Southeast Asia. It is written in Tai Viet and is notable for preserving a regional script with explicit tone marking.",
        scripts=[ScriptISO("TAVT")],
        primary_script=ScriptISO("TAVT"),
        required_blocks=["Tai Viet"],
        optional_blocks=[],
        sample="ꪀꪁꪂꪃꪄꪅꪆꪇꪈꪉꪊꪋꪌꪍꪎꪏꪐꪑꪒꪓꪔꪕꪖꪗ",
    ),
    "zgh": LanguageInfo(
        canonical_name="Standard Moroccan Tamazight",
        description="Standard Moroccan Tamazight is the standardized Berber language used in Moroccan education and administration. It is written in Neo-Tifinagh and is notable for its official modern standardization.",
        scripts=[ScriptISO("TFNG")],
        primary_script=ScriptISO("TFNG"),
        required_blocks=["Tifinagh"],
        optional_blocks=[],
        sample="ⴰⴱⴲⴳⴴⴵⴶⴷⴸⴹⴺⴻⴼⴽⴾⴿⵀⵁⵂⵃⵄⵅⵆⵇ",
    ),
    "mai": LanguageInfo(
        canonical_name="Maithili",
        description="Maithili is an Indo-Aryan language of eastern India and Nepal. It is written mainly in Devanagari today and is notable for historical use of the Tirhuta script.",
        scripts=[ScriptISO("TIRH"), ScriptISO("DEVA")],
        primary_script=ScriptISO("TIRH"),
        required_blocks=["Tirhuta"],
        optional_blocks=["Devanagari"],
        sample="𑒀𑒁𑒂𑒃𑒄𑒅𑒆𑒇𑒈𑒉𑒊𑒋𑒌𑒍𑒎𑒏𑒐𑒑𑒒𑒓𑒔𑒕𑒖𑒗",
    ),
    "mak": LanguageInfo(
        canonical_name="Makassarese",
        description="Makassarese is an Austronesian language of South Sulawesi. It is written mainly in Latin today and is notable here for historical manuscript use of the Makasar script.",
        scripts=[ScriptISO("MAKA")],
        primary_script=ScriptISO("MAKA"),
        required_blocks=["Makasar"],
        optional_blocks=[],
        sample="𑻠𑻡𑻢𑻣𑻤𑻥𑻦𑻧𑻨𑻩𑻪𑻫𑻬𑻭𑻮𑻯𑻰𑻱𑻲𑻳𑻴𑻵𑻶",
    ),
    "pt": LanguageInfo(
        canonical_name="Portuguese",
        description="Portuguese is a Romance language spoken in Portugal, Brazil, and several African and Asian states. It is written in the Latin script and is notable for its pluricentric global standard.",
        scripts=[ScriptISO("LATN")],
        primary_script=ScriptISO("LATN"),
        required_blocks=["Basic Latin"],
        optional_blocks=["Latin-1 Supplement"],
        sample="Luís argüia que o pingüim feliz tomava chá",
    ),
    "pa": LanguageInfo(
        canonical_name="Panjabi",
        description="Panjabi is an Indo-Aryan language of the Punjab region. It is written in Gurmukhi in this profile and is notable as a major cross-border language with parallel script traditions.",
        scripts=[ScriptISO("GURU")],
        primary_script=ScriptISO("GURU"),
        required_blocks=["Gurmukhi"],
        optional_blocks=["Gurmukhi Extensions"],
        sample="ਁਂਃਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟ",
    ),
    "rhg": LanguageInfo(
        canonical_name="Rohingya",
        description="Rohingya is an Indo-Aryan language spoken mainly in Rakhine State and the Rohingya diaspora. It is written in Hanifi Rohingya, Arabic, and Latin and is notable for a modern dedicated script tied to language activism.",
        scripts=[ScriptISO("ROHG"), ScriptISO("ARAB")],
        primary_script=ScriptISO("ROHG"),
        required_blocks=["Hanifi Rohingya"],
        optional_blocks=["Arabic"],
        sample="𐴀𐴁𐴂𐴃𐴄𐴅𐴆𐴇𐴈𐴉𐴊𐴋𐴌𐴍𐴎𐴏𐴐𐴑𐴒𐴓𐴔𐴕𐴖𐴗",
    ),
    "rej": LanguageInfo(
        canonical_name="Rejang",
        description="Rejang is an Austronesian language of Sumatra. It is written mainly in Latin today and is notable for a historical indigenous script of the same name.",
        scripts=[ScriptISO("RJNG")],
        primary_script=ScriptISO("RJNG"),
        required_blocks=["Rejang"],
        optional_blocks=[],
        sample="ꤰꤱꤲꤳꤴꤵꤶꤷꤸꤹꤺꤻꤼꤽꤾꤿꥀꥁꥂꥃꥄꥅꥆꥇ",
    ),
    "ru": LanguageInfo(
        canonical_name="Russian",
        description="Russian is an East Slavic language spoken across Russia and neighboring regions. It is written in Cyrillic and is notable for its broad geographic reach in Eurasia.",
        scripts=[ScriptISO("CYRL")],
        primary_script=ScriptISO("CYRL"),
        required_blocks=["Cyrillic"],
        optional_blocks=["Cyrillic Supplement"],
        sample="Съешь же ещё этих мягких французских булок",
    ),
    "sa": LanguageInfo(
        canonical_name="Sanskrit",
        description="Sanskrit is a classical Indo-Aryan language of South Asia. It is written in several Indic scripts and is notable for its central role in religious, philosophical, and scholarly traditions.",
        scripts=[ScriptISO("BRAH"), ScriptISO("GRAN"), ScriptISO("DEVA")],
        primary_script=ScriptISO("BRAH"),
        required_blocks=["Brahmi"],
        optional_blocks=["Grantha", "Devanagari"],
        sample="𑀀𑀁𑀂𑀃𑀄𑀅𑀆𑀇𑀈𑀉𑀊𑀋𑀌𑀍𑀎𑀏𑀐𑀑𑀒𑀓𑀔𑀕𑀖𑀗",
    ),
    "saz": LanguageInfo(
        canonical_name="Saurashtra",
        description="Saurashtra is an Indo-Aryan language spoken by a diaspora community in southern India. It is written in its own script as well as regional scripts and is notable for maintaining a distinct community identity through writing.",
        scripts=[ScriptISO("SAUR")],
        primary_script=ScriptISO("SAUR"),
        required_blocks=["Saurashtra"],
        optional_blocks=[],
        sample="ꢂꢃꢄꢅꢆꢇꢈꢉꢊꢋꢌꢍꢎꢏꢐꢑꢒꢓꢔꢕꢖꢗꢘꢙ",
    ),
    "si": LanguageInfo(
        canonical_name="Sinhala",
        description="Sinhala is an Indo-Aryan language spoken mainly in Sri Lanka. It is written in the Sinhala script and is notable as the only major modern Indo-Aryan language native to the island.",
        scripts=[ScriptISO("SINH")],
        primary_script=ScriptISO("SINH"),
        required_blocks=["Sinhala"],
        optional_blocks=[],
        sample="සියලු මිනිසුන් නිදහස්ව උපදින අතර",
    ),
    "sq": LanguageInfo(
        canonical_name="Albanian",
        description="Albanian is an Indo-European language of the Balkans. It is written in the Latin script today and is notable in this table for historical evidence from the Elbasan script.",
        scripts=[ScriptISO("ELBA"), ScriptISO("LATN")],
        primary_script=ScriptISO("ELBA"),
        required_blocks=["Elbasan"],
        optional_blocks=["Basic Latin"],
        sample="𐔀𐔁𐔂𐔃𐔄𐔅𐔆𐔇𐔈𐔉𐔊𐔋𐔌𐔍𐔎𐔏𐔐𐔑𐔒𐔓𐔔𐔕𐔖𐔗",
    ),
    "ta": LanguageInfo(
        canonical_name="Tamil",
        description="Tamil is a Dravidian language spoken in South India, Sri Lanka, and the global Tamil diaspora. It is written in the Tamil script and is notable for one of the oldest continuous literary traditions in Asia.",
        scripts=[ScriptISO("TAML")],
        primary_script=ScriptISO("TAML"),
        required_blocks=["Tamil"],
        optional_blocks=["Tamil Supplement"],
        sample="யாதும் ஊரே யாவரும் கேளிர்",
    ),
    "te": LanguageInfo(
        canonical_name="Telugu",
        description="Telugu is a Dravidian language spoken mainly in Andhra Pradesh and Telangana. It is written in the Telugu script and is notable for a large speaker base and a major literary tradition.",
        scripts=[ScriptISO("TELU")],
        primary_script=ScriptISO("TELU"),
        required_blocks=["Telugu"],
        optional_blocks=[],
        sample="అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞ",
    ),
    "kyu": LanguageInfo(
        canonical_name="Western Kayah",
        description="Western Kayah is a Karenni language of Myanmar and Thailand. It is written in Kayah Li and is notable for a dedicated 20th-century script created for local use.",
        scripts=[ScriptISO("KALI")],
        primary_script=ScriptISO("KALI"),
        required_blocks=["Kayah Li"],
        optional_blocks=[],
        sample="꤀꤁꤂꤃꤄꤅꤆꤇꤈꤉ꤊꤋꤌꤍꤎꤏꤐꤑꤒꤓꤔꤕꤖꤗ",
    ),
    "th": LanguageInfo(
        canonical_name="Thai",
        description="Thai is a Kra-Dai language spoken mainly in Thailand. It is written in the Thai script and is notable for an orthography that marks tone and preserves historical consonant classes.",
        scripts=[ScriptISO("THAI")],
        primary_script=ScriptISO("THAI"),
        required_blocks=["Thai"],
        optional_blocks=[],
        sample="ภาษาไทยเป็นภาษาที่สวยงาม",
    ),
    "ti": LanguageInfo(
        canonical_name="Tigrinya",
        description="Tigrinya is an Ethiosemitic language of Eritrea and northern Ethiopia. It is written in the Ethiopic script and is notable as a major modern Semitic language of the Horn of Africa.",
        scripts=[ScriptISO("ETHI")],
        primary_script=ScriptISO("ETHI"),
        required_blocks=["Ethiopic"],
        optional_blocks=[],
        sample="ሰላም እንታይ ከመይ ኢኻ",
    ),
    "tdd": LanguageInfo(
        canonical_name="Tai Nua",
        description="Tai Nua is a Southwestern Tai language spoken mainly in southwestern China and nearby regions. It is written in Tai Le and is notable for a modern standardized script in the Chinese context.",
        scripts=[ScriptISO("TALE")],
        primary_script=ScriptISO("TALE"),
        required_blocks=["Tai Le"],
        optional_blocks=[],
        sample="ᥐᥑᥒᥓᥔᥕᥖᥗᥘᥙᥚᥛᥜᥝᥞᥟᥠᥡᥢᥣᥤᥥᥦᥧ",
    ),
    "zh": LanguageInfo(
        canonical_name="Chinese",
        description="Chinese is a Sinitic language group written primarily with Han characters. In this profile it also includes Bopomofo as supporting evidence and is notable for a logographic writing tradition of great historical depth.",
        scripts=[ScriptISO("HANI"), ScriptISO("BOPO")],
        primary_script=ScriptISO("HANI"),
        required_blocks=["CJK Unified Ideographs"],
        optional_blocks=["Bopomofo", "Bopomofo Extended"],
        sample="天地玄黃 宇宙洪荒",
    ),
    "vai": LanguageInfo(
        canonical_name="Vai",
        description="Vai is a Mande language spoken mainly in Liberia and Sierra Leone. It is written in the Vai syllabary and is notable for one of the rare indigenous scripts still used in daily practice.",
        scripts=[ScriptISO("VAII")],
        primary_script=ScriptISO("VAII"),
        required_blocks=["Vai"],
        optional_blocks=[],
        sample="ꔀꔁꔂꔃꔄꔅꔆꔇꔈꔉꔊꔋꔌꔍꔎꔏꔐꔑꔒꔓꔔꔕꔖꔗ",
    ),
    "xag": LanguageInfo(
        canonical_name="Aghwan",
        description="Aghwan is the conventional name for the extinct Caucasian Albanian language. It is known mainly from palimpsests and inscriptions and is notable for preserving a poorly documented language of the ancient Caucasus.",
        scripts=[ScriptISO("AGHB")],
        primary_script=ScriptISO("AGHB"),
        required_blocks=["Caucasian Albanian"],
        optional_blocks=[],
        sample="𐔰𐔱𐔲𐔳𐔴𐔵𐔶𐔷𐔸𐔹𐔺𐔻𐔼𐔽𐔾𐔿𐕀𐕁𐕂𐕃𐕄𐕅𐕆𐕇",
    ),
    "xco": LanguageInfo(
        canonical_name="Chorasmian",
        description="Chorasmian is an extinct Eastern Iranian language of Central Asia. It is written in the Chorasmian script and is notable for surviving mainly in fragmentary documentary material.",
        scripts=[ScriptISO("CHRS")],
        primary_script=ScriptISO("CHRS"),
        required_blocks=["Chorasmian"],
        optional_blocks=[],
        sample="𐾰𐾱𐾲𐾳𐾴𐾵𐾶𐾷𐾸𐾹𐾺𐾻𐾼𐾽𐾾𐾿𐿀𐿁𐿂𐿃𐿄𐿅𐿆𐿇",
    ),
    "xcr": LanguageInfo(
        canonical_name="Carian",
        description="Carian is an extinct Anatolian language once spoken in southwestern Asia Minor. It is written in the Carian script and is notable for being reconstructed largely from inscriptions.",
        scripts=[ScriptISO("CARI")],
        primary_script=ScriptISO("CARI"),
        required_blocks=["Carian"],
        optional_blocks=[],
        sample="𐊠𐊡𐊢𐊣𐊤𐊥𐊦𐊧𐊨𐊩𐊪𐊫𐊬𐊭𐊮𐊯𐊰𐊱𐊲𐊳𐊴𐊵𐊶𐊷",
    ),
    "zxx": LanguageInfo(
        canonical_name="No linguistic content",
        description="No linguistic content is a placeholder category for symbols that are not tied to a spoken language. In this table it covers Byzantine musical notation, which is notable for encoding chant rather than ordinary text.",
        scripts=[ScriptISO("BYZM")],
        primary_script=ScriptISO("BYZM"),
        required_blocks=["Byzantine Musical Symbols"],
        optional_blocks=[],
        sample="𝀀𝀁𝀂𝀃𝀄𝀅𝀆𝀇𝀈𝀉𝀊𝀋𝀌𝀍𝀎𝀏𝀐𝀑𝀒𝀓𝀔𝀕𝀖𝀗",
    ),
}

LANGUAGE_INFO.update(
    {
        "egy": _make_script_language_info(
            "Egyptian",
            "Egyptian is an ancient Afroasiatic language of the Nile Valley. In this profile it is represented by Egyptian Hieroglyphs and related hieroglyphic Unicode blocks.",
            [ScriptISO("EGYP")],
            ["Egyptian Hieroglyphs"],
            optional_blocks=[
                "Egyptian Hieroglyph Format Controls",
                "Egyptian Hieroglyphs Extended-A",
            ],
        ),
        "arc": _make_script_language_info(
            "Official Aramaic",
            "Official Aramaic is an ancient Northwest Semitic language. In this profile it covers Aramaic-script evidence represented by Imperial Aramaic, Nabataean, and Palmyrene blocks.",
            [ScriptISO("ARMI"), ScriptISO("NBAT"), ScriptISO("PALM")],
            ["Imperial Aramaic"],
            optional_blocks=["Nabataean", "Palmyrene"],
        ),
        "xpr": _make_script_language_info(
            "Parthian",
            "Parthian is an extinct Iranian language. In this profile it is represented by the Inscriptional Parthian script block used for deterministic script-language fallback.",
            [ScriptISO("PRTI")],
            ["Inscriptional Parthian"],
        ),
        "pgd": _make_script_language_info(
            "Gandhari",
            "Gandhari is an extinct Indo-Aryan language associated with Kharoshthi manuscript and inscriptional traditions. In this profile it is represented by the Kharoshthi block.",
            [ScriptISO("KHAR")],
            ["Kharoshthi"],
        ),
        "gmy": _make_script_language_info(
            "Mycenaean Greek",
            "Mycenaean Greek is the earliest attested form of Greek. In this profile it is represented by Linear B syllabic and ideographic Unicode blocks.",
            [ScriptISO("LINB")],
            ["Linear B Syllabary"],
            optional_blocks=["Linear B Ideograms"],
        ),
        "xlc": _make_script_language_info(
            "Lycian",
            "Lycian is an extinct Anatolian language. In this profile it is represented by the Lycian script block.",
            [ScriptISO("LYCI")],
            ["Lycian"],
        ),
        "xld": _make_script_language_info(
            "Lydian",
            "Lydian is an extinct Anatolian language. In this profile it is represented by the Lydian script block.",
            [ScriptISO("LYDI")],
            ["Lydian"],
        ),
        "mid": _make_script_language_info(
            "Mandaic",
            "Mandaic is an Eastern Aramaic language associated with Mandaean religious tradition. In this profile it is represented by the Mandaic script block.",
            [ScriptISO("MAND")],
            ["Mandaic"],
        ),
        "xmn": _make_script_language_info(
            "Manichaean Middle Persian",
            "Manichaean Middle Persian is an extinct Iranian language attested in Manichaean texts. In this profile it is represented by the Manichaean script block.",
            [ScriptISO("MANI")],
            ["Manichaean"],
        ),
        "xmr": _make_script_language_info(
            "Meroitic",
            "Meroitic is an extinct language of the ancient Nile Valley. In this profile it is represented by Meroitic Hieroglyphs with Meroitic Cursive as supporting evidence.",
            [ScriptISO("MERO")],
            ["Meroitic Hieroglyphs"],
            optional_blocks=["Meroitic Cursive"],
        ),
        "hmd": _make_script_language_info(
            "Large Flowery Miao",
            "Large Flowery Miao is a Hmong-Mien language. In this profile it is represented by the Miao block used for Pollard-script coverage.",
            [ScriptISO("PLRD")],
            ["Miao"],
        ),
        "sd": _make_script_language_info(
            "Sindhi",
            "Sindhi is an Indo-Aryan language of Sindh and neighboring regions. In this profile it is represented by Khudawadi script coverage.",
            [ScriptISO("SIND")],
            ["Khudawadi"],
        ),
        "mr": _make_script_language_info(
            "Marathi",
            "Marathi is an Indo-Aryan language of western India. In this profile it is represented by Modi, a historical administrative script associated with Marathi.",
            [ScriptISO("MODI")],
            ["Modi"],
        ),
        "khb": _make_script_language_info(
            "Lü",
            "Lü is a Southwestern Tai language. In this profile it is represented by the New Tai Lue script block.",
            [ScriptISO("TALU")],
            ["New Tai Lue"],
        ),
        "sga": _make_script_language_info(
            "Old Irish",
            "Old Irish is an early Goidelic language. In this profile it is represented by Ogham as a deterministic fallback for Ogham-script fonts.",
            [ScriptISO("OGAM")],
            ["Ogham"],
        ),
        "sat": _make_script_language_info(
            "Santali",
            "Santali is an Austroasiatic language of eastern India and neighboring regions. In this profile it is represented by the Ol Chiki script block.",
            [ScriptISO("OLCK")],
            ["Ol Chiki"],
        ),
        "hu": _make_script_language_info(
            "Hungarian",
            "Hungarian is a Uralic language spoken mainly in Hungary and neighboring regions. In this profile it is represented by Old Hungarian script coverage.",
            [ScriptISO("HUNG")],
            ["Old Hungarian"],
        ),
        "xna": _make_script_language_info(
            "Ancient North Arabian",
            "Ancient North Arabian is a historical Semitic language grouping. In this profile it is represented by the Old North Arabian block.",
            [ScriptISO("NARB")],
            ["Old North Arabian"],
        ),
        "peo": _make_script_language_info(
            "Old Persian",
            "Old Persian is an extinct Iranian language of Achaemenid inscriptions. In this profile it is represented by the Old Persian cuneiform block.",
            [ScriptISO("XPEO")],
            ["Old Persian"],
        ),
        "xsa": _make_script_language_info(
            "Sabaean",
            "Sabaean is a historical South Semitic language. In this profile it is represented by the Old South Arabian block.",
            [ScriptISO("SARB")],
            ["Old South Arabian"],
        ),
        "otk": _make_script_language_info(
            "Old Turkish",
            "Old Turkish is a historical Turkic language. In this profile it is represented by the Old Turkic script block.",
            [ScriptISO("ORKH")],
            ["Old Turkic"],
        ),
        "so": _make_script_language_info(
            "Somali",
            "Somali is a Cushitic language of the Horn of Africa. In this profile it is represented by Osmanya, one of the dedicated scripts created for Somali.",
            [ScriptISO("OSMA")],
            ["Osmanya"],
        ),
        "hmn": _make_script_language_info(
            "Hmong",
            "Hmong is a Hmong-Mien language cluster. In this profile it is represented by Pahawh Hmong script coverage.",
            [ScriptISO("HMNG")],
            ["Pahawh Hmong"],
        ),
        "ctd": _make_script_language_info(
            "Tedim Chin",
            "Tedim Chin is a Kuki-Chin language of Myanmar and neighboring regions. In this profile it is represented by Pau Cin Hau script coverage.",
            [ScriptISO("PAUC")],
            ["Pau Cin Hau"],
        ),
        "phn": _make_script_language_info(
            "Phoenician",
            "Phoenician is a historical Northwest Semitic language. In this profile it is represented by the Phoenician script block.",
            [ScriptISO("PHNX")],
            ["Phoenician"],
        ),
        "sam": _make_script_language_info(
            "Samaritan Aramaic",
            "Samaritan Aramaic is an Aramaic language associated with Samaritan tradition. In this profile it is represented by the Samaritan block.",
            [ScriptISO("SAMR")],
            ["Samaritan"],
        ),
        "ks": _make_script_language_info(
            "Kashmiri",
            "Kashmiri is an Indo-Aryan language of Kashmir. In this profile it is represented by Sharada as a historical script fallback.",
            [ScriptISO("SHRD")],
            ["Sharada"],
            optional_blocks=["Sharada Supplement"],
        ),
        "srb": _make_script_language_info(
            "Sora",
            "Sora is a Munda language of eastern India. In this profile it is represented by the Sora Sompeng script block.",
            [ScriptISO("SORA")],
            ["Sora Sompeng"],
        ),
        "nst": _make_script_language_info(
            "Tangsa",
            "Tangsa is a Tibeto-Burman language cluster of northeast India and Myanmar. In this profile it is represented by Tangsa script coverage.",
            [ScriptISO("TNSA")],
            ["Tangsa"],
        ),
        "uga": _make_script_language_info(
            "Ugaritic",
            "Ugaritic is a historical Northwest Semitic language. In this profile it is represented by the Ugaritic cuneiform alphabet block.",
            [ScriptISO("UGAR")],
            ["Ugaritic"],
        ),
        "hnj": _make_script_language_info(
            "Hmong Njua",
            "Hmong Njua is a Hmong-Mien language. In this profile it is represented by Nyiakeng Puachue Hmong script coverage.",
            [ScriptISO("HMNP")],
            ["Nyiakeng Puachue Hmong"],
        ),
        "oui": _make_script_language_info(
            "Old Uyghur",
            "Old Uyghur is a historical Turkic language. In this profile it is represented by the Old Uyghur script block.",
            [ScriptISO("OUGR")],
            ["Old Uyghur"],
        ),
        "txg": _make_script_language_info(
            "Tangut",
            "Tangut is an extinct Sino-Tibetan language of the Western Xia state. In this profile it is represented by Tangut and related component blocks.",
            [ScriptISO("TANG")],
            ["Tangut"],
            optional_blocks=[
                "Tangut Components",
                "Tangut Supplement",
                "Tangut Components Supplement",
            ],
        ),
        "txo": _make_script_language_info(
            "Toto",
            "Toto is a Tibeto-Burman language of the eastern Himalayas. In this profile it is represented by the Toto script block.",
            [ScriptISO("TOTO")],
            ["Toto"],
        ),
        "ku": _make_script_language_info(
            "Kurdish",
            "Kurdish is an Iranian language cluster of western Asia. In this profile it is represented by Yezidi script coverage.",
            [ScriptISO("YEZI")],
            ["Yezidi"],
        ),
    }
)

LANGUAGE_INFO["doi"]["scripts"] = [
    ScriptISO("DOGR"),
    ScriptISO("TAKR"),
    ScriptISO("DEVA"),
]
LANGUAGE_INFO["doi"]["optional_blocks"] = [
    "Takri",
    "Devanagari",
    "Devanagari Extended-A",
]
LANGUAGE_INFO["en"]["scripts"] = [
    ScriptISO("LATN"),
    ScriptISO("DSRT"),
    ScriptISO("SHAW"),
]
LANGUAGE_INFO["en"]["optional_blocks"] = [
    "Latin-1 Supplement",
    "Shavian",
]
LANGUAGE_INFO["mn"]["scripts"] = [
    ScriptISO("MONG"),
    ScriptISO("PHAG"),
    ScriptISO("SOYO"),
    ScriptISO("ZANB"),
]
LANGUAGE_INFO["mn"]["optional_blocks"] = [
    "Phags-pa",
    "Soyombo",
    "Zanabazar Square",
]
LANGUAGE_INFO["sa"]["scripts"] = [
    ScriptISO("BRAH"),
    ScriptISO("GRAN"),
    ScriptISO("SIDD"),
    ScriptISO("DEVA"),
]
LANGUAGE_INFO["sa"]["optional_blocks"] = [
    "Grantha",
    "Siddham",
    "Devanagari",
]
LANGUAGE_INFO["und"] = LanguageInfo(
    canonical_name="Undetermined",
    description=(
        "Undetermined is a placeholder code used when no specific "
        "language can be assigned. In this table it covers "
        "undeciphered, multi-language, or script-only catalog fallbacks."
    ),
    scripts=[
        ScriptISO("CPMN"),
        ScriptISO("XSUX"),
        ScriptISO("HATR"),
        ScriptISO("LINA"),
        ScriptISO("MARC"),
        ScriptISO("NUSH"),
        ScriptISO("ITAL"),
        ScriptISO("RUNR"),
        ScriptISO("PHAI"),
    ],
    primary_script=ScriptISO("CPMN"),
    required_blocks=["Cypro-Minoan"],
    optional_blocks=[
        "Cuneiform",
        "Hatran",
        "Linear A",
        "Marchen",
        "Nushu",
        "Old Italic",
        "Runic",
        "Phaistos Disc",
    ],
    sample="𒾐𒾑𒾒𒾓𒾔𒾕𒾖𒾗𒾘𒾙𒾚𒾛𒾜𒾝𒾞𒾟𒾠𒾡𒾢𒾣𒾤𒾥𒾦𒾧",
)
LANGUAGE_INFO["zxx"] = LanguageInfo(
    canonical_name="No linguistic content",
    description=(
        "No linguistic content is a placeholder category for symbols "
        "and notation that are not tied to a spoken language."
    ),
    scripts=[
        ScriptISO("BYZM"),
        ScriptISO("BRAI"),
        ScriptISO("MAYA"),
        ScriptISO("SGNW"),
        ScriptISO("OTSY"),
        ScriptISO("ZNAM"),
    ],
    primary_script=ScriptISO("BYZM"),
    required_blocks=["Byzantine Musical Symbols"],
    optional_blocks=[
        "Braille Patterns",
        "Mayan Numerals",
        "Sutton SignWriting",
        "Ottoman Siyaq Numbers",
        "Znamenny Musical Notation",
    ],
    sample="𝀀𝀁𝀂𝀃𝀄𝀅𝀆𝀇𝀈𝀉𝀊𝀋𝀌𝀍𝀎𝀏𝀐𝀑𝀒𝀓𝀔𝀕𝀖𝀗",
)


_SCRIPT_INFERENCE_PRIORITY: dict[ScriptISO, int] = {
    ScriptISO("LATN"): 0,
    ScriptISO("ARAB"): 1,
    ScriptISO("ARMN"): 2,
    ScriptISO("BENG"): 3,
    ScriptISO("BOPO"): 4,
    ScriptISO("BRAI"): 5,
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
    ScriptISO("BENG"): {
        "suppresses": [ScriptISO("DEVA")],
        "preferred_over": [ScriptISO("DEVA")],
    },
    ScriptISO("BOPO"): {
        "required_blocks": ["Bopomofo"],
        "optional_blocks": ["Bopomofo Extended"],
        "block_match": "exact",
        "unicode_max_ranges": [(0x3100, 0x312F), (0x31A0, 0x31BF)],
    },
    ScriptISO("BRAI"): {
        "required_blocks": ["Braille Patterns"],
        "optional_blocks": [],
        "suppresses": [],
        "preferred_over": [],
        "unicode_max_ranges": [(0x2800, 0x28FF)],
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
        "preferred_over": [],
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
    ScriptISO("LAOO"): {
        "suppresses": [ScriptISO("THAI")],
        "preferred_over": [ScriptISO("THAI")],
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
    ScriptISO("TAML"): {
        "required_blocks": ["Tamil", "Tamil Supplement"],
        "optional_blocks": [],
        "unicode_max_ranges": [(0x0B80, 0x0BFF), (0x11FC0, 0x11FFF)],
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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for index, script_iso in enumerate(SCRIPT_INFO):
        info = SCRIPT_INFO[script_iso]
        if "required_blocks" in info and "optional_blocks" in info:
            required_blocks = list(info["required_blocks"])
            optional_blocks = list(info["optional_blocks"])
        else:
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
        info["suppresses"] = list(
            overrides.get("suppresses", info.get("suppresses", []))
        )
        info["inference_priority"] = int(
            overrides.get(
                "inference_priority",
                info.get(
                    "inference_priority",
                    _SCRIPT_INFERENCE_PRIORITY.get(script_iso, index + 100),
                ),
            )
        )
        info["block_match"] = overrides.get(
            "block_match", info.get("block_match", "exact")
        )
        info["unicode_max_ranges"] = list(
            overrides.get(
                "unicode_max_ranges",
                info.get(
                    "unicode_max_ranges",
                    _derive_unicode_max_ranges(
                        info["required_blocks"],
                        info["block_match"],
                    ),
                ),
            )
        )
        info["collapse_group"] = str(
            overrides.get("collapse_group", info.get("collapse_group", ""))
        )
        info["preferred_over"] = list(
            overrides.get("preferred_over", info.get("preferred_over", []))
        )


_finalize_language_info()
_finalize_script_info()
