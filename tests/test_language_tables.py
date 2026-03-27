"""
Exercise ontology additions for newly supported scripts and languages.
"""

from fontshow.common.specimens import choose_language_sample
from fontshow.core.types import ScriptISO
from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO


def test_script_info_includes_dogra_and_dives_akuru_rendering_entries():
    """
    Ensure dedicated render-policy entries exist for DOGR and DIAK.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    dogra = SCRIPT_INFO[ScriptISO("DOGR")]
    dives = SCRIPT_INFO[ScriptISO("DIAK")]

    assert dogra["fontspec_opts"] == "Script=Dogra"
    assert dogra["display_language"] == "doi"
    assert isinstance(dogra["specimen"], str) and dogra["specimen"]

    assert dives["fontspec_opts"] == "Script={Dives Akuru}"
    assert dives["display_language"] == "dv"
    assert isinstance(dives["specimen"], str) and dives["specimen"]


def test_language_info_includes_relative_samples_for_dogra_and_dives_akuru():
    """
    Ensure language-based specimen fallback uses script-appropriate samples.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert LANGUAGE_INFO["doi"]["scripts"][0] == ScriptISO("DOGR")
    assert LANGUAGE_INFO["dv"]["scripts"][0] == ScriptISO("DIAK")
    assert choose_language_sample(["doi"]) == "𑠖𑠮𑠝𑠳 𑠛𑠯𑠬𑠬𑠰"
    assert choose_language_sample(["dv"]) == "𑤀𑤂𑤄 𑤋𑤢𑤼"


def test_script_info_includes_buginese_and_buhid_rendering_entries():
    """
    Ensure dedicated render-policy entries exist for BUGI and BUHD.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    buginese = SCRIPT_INFO[ScriptISO("BUGI")]
    buhid = SCRIPT_INFO[ScriptISO("BUHD")]

    assert buginese["fontspec_opts"] == "Script=Buginese"
    assert buginese["display_language"] == "bug"
    assert isinstance(buginese["specimen"], str) and buginese["specimen"]

    assert buhid["fontspec_opts"] == "Script=Buhid"
    assert buhid["display_language"] == "bku"
    assert isinstance(buhid["specimen"], str) and buhid["specimen"]


def test_first_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the first 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "ADLM": ("ff", "Script=Adlam"),
        "AHOM": ("aho", "Script=Ahom"),
        "BALI": ("ban", "Script=Balinese"),
        "BATK": ("bbc", "Script=Batak"),
        "CHAM": ("cjm", "Script=Cham"),
        "GUJR": ("gu", "Script=Gujarati"),
        "GURU": ("pa", "Script=Gurmukhi"),
        "HANO": ("hnn", "Script=Hanunoo"),
        "JAVA": ("jv", "Script=Javanese"),
        "LEPC": ("lep", "Script=Lepcha"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_first_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the first 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "ff": ScriptISO("ADLM"),
        "aho": ScriptISO("AHOM"),
        "ban": ScriptISO("BALI"),
        "bbc": ScriptISO("BATK"),
        "cjm": ScriptISO("CHAM"),
        "gu": ScriptISO("GUJR"),
        "pa": ScriptISO("GURU"),
        "hnn": ScriptISO("HANO"),
        "jv": ScriptISO("JAVA"),
        "lep": ScriptISO("LEPC"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert info["scripts"][0] == script_iso
        assert isinstance(info["sample"], str) and info["sample"]


def test_second_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the second 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "BOPO": ("zh", "Script=Bopomofo"),
        "BRAH": ("sa", "Script=Brahmi"),
        "CANS": ("cr", "Script=Canadian Syllabics"),
        "COPT": ("cop", "Script=Coptic"),
        "DSRT": ("en", "Script=Deseret"),
        "ELBA": ("sq", "Script=Elbasan"),
        "GLAG": ("cu", "Script=Glagolitic"),
        "GRAN": ("sa", "Script=Grantha"),
        "ROHG": ("rhg", "Script={Hanifi Rohingya}"),
        "KTHI": ("bho", "Script=Kaithi"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_second_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the second 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "zh": ScriptISO("HANI"),
        "sa": ScriptISO("BRAH"),
        "cr": ScriptISO("CANS"),
        "cop": ScriptISO("COPT"),
        "en": ScriptISO("LATN"),
        "sq": ScriptISO("ELBA"),
        "cu": ScriptISO("GLAG"),
        "rhg": ScriptISO("ROHG"),
        "bho": ScriptISO("KTHI"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_third_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the third 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "MROO": ("mro", "Script=Mro"),
        "PERM": ("kv", "Script={Old Permic}"),
        "PHLP": ("pal", "Script={Psalter Pahlavi}"),
        "SOGD": ("sog", "Script=Sogdian"),
        "TAGB": ("tbw", "Script=Tagbanwa"),
        "TGLG": ("tl", "Script=Tagalog"),
        "LANA": ("nod", "Script={Tai Tham}"),
        "TAVT": ("blt", "Script={Tai Viet}"),
        "TFNG": ("zgh", "Script=Tifinagh"),
        "TIRH": ("mai", "Script=Tirhuta"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_third_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the third 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "mro": ScriptISO("MROO"),
        "kv": ScriptISO("PERM"),
        "pal": ScriptISO("PHLP"),
        "sog": ScriptISO("SOGD"),
        "tbw": ScriptISO("TAGB"),
        "tl": ScriptISO("TGLG"),
        "nod": ScriptISO("LANA"),
        "blt": ScriptISO("TAVT"),
        "zgh": ScriptISO("TFNG"),
        "mai": ScriptISO("TIRH"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_fourth_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the fourth 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "GOTH": ("got", "Script=Gothic"),
        "KNDA": ("kn", "Script=Kannada"),
        "MLYM": ("ml", "Script=Malayalam"),
        "ORYA": ("or", "Script=Oriya"),
        "TELU": ("te", "Script=Telugu"),
        "THAA": ("dv", "Script=Thaana"),
        "SYRC": ("syr", "Script=Syriac"),
        "SOGO": ("sog", "Script={Old Sogdian}"),
        "PHLI": ("pal", "Script={Inscriptional Pahlavi}"),
        "VAII": ("vai", "Script=Vai"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_fourth_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the fourth 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "got": ScriptISO("GOTH"),
        "kn": ScriptISO("KNDA"),
        "ml": ScriptISO("MLYM"),
        "or": ScriptISO("ORYA"),
        "te": ScriptISO("TELU"),
        "dv": ScriptISO("THAA"),
        "syr": ScriptISO("SYRC"),
        "sog": ScriptISO("SOGO"),
        "pal": ScriptISO("PHLI"),
        "vai": ScriptISO("VAII"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_fifth_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the fifth 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "KALI": ("kyu", "Script={Kayah Li}"),
        "LIMB": ("lif", "Script=Limbu"),
        "LISU": ("lis", "Script=Lisu"),
        "MEDF": ("dmf", "Script=Medefaidrin"),
        "MEND": ("men", "Script={Mende Kikakui}"),
        "MONG": ("mn", "Script=Mongolian"),
        "MTEI": ("mni", "Script={Meitei Mayek}"),
        "NEWA": ("new", "Script=Newa"),
        "NKOO": ("nqo", "Script={N'Ko}"),
        "OSGE": ("osa", "Script=Osage"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_fifth_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the fifth 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "kyu": ScriptISO("KALI"),
        "lif": ScriptISO("LIMB"),
        "lis": ScriptISO("LISU"),
        "dmf": ScriptISO("MEDF"),
        "men": ScriptISO("MEND"),
        "mn": ScriptISO("MONG"),
        "mni": ScriptISO("MTEI"),
        "new": ScriptISO("NEWA"),
        "nqo": ScriptISO("NKOO"),
        "osa": ScriptISO("OSGE"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_sixth_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the sixth 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "BAMU": ("bax", "Script=Bamum"),
        "CHAK": ("ccp", "Script=Chakma"),
        "GONG": ("gon", "Script={Gunjala Gondi}"),
        "GONM": ("gon", "Script={Masaram Gondi}"),
        "RJNG": ("rej", "Script=Rejang"),
        "SAUR": ("saz", "Script=Saurashtra"),
        "SUND": ("su", "Script=Sundanese"),
        "SYLO": ("syl", "Script={Syloti Nagri}"),
        "TALE": ("tdd", "Script={Tai Le}"),
        "WARA": ("hoc", "Script={Warang Citi}"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_sixth_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the sixth 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "bax": ScriptISO("BAMU"),
        "ccp": ScriptISO("CHAK"),
        "gon": ScriptISO("GONG"),
        "rej": ScriptISO("RJNG"),
        "saz": ScriptISO("SAUR"),
        "su": ScriptISO("SUND"),
        "syl": ScriptISO("SYLO"),
        "tdd": ScriptISO("TALE"),
        "hoc": ScriptISO("WARA"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_seventh_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the seventh 10-script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "AGHB": ("xag", "Script={Caucasian Albanian}"),
        "AVST": ("ae", "Script=Avestan"),
        "BASS": ("bsq", "Script={Bassa Vah}"),
        "BHKS": ("pli", "Script=Bhaiksuki"),
        "BYZM": ("zxx", "Script={Byzantine Music}"),
        "CARI": ("xcr", "Script=Carian"),
        "CHRS": ("xco", "Script=Chorasmian"),
        "CPMN": ("und", "Script={Cypro-Minoan}"),
        "CPRT": ("ecy", "Script={Cypriot Syllabary}"),
        "HLUW": ("hlu", "Script={Anatolian Hieroglyphs}"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_seventh_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the seventh 10-script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "xag": ScriptISO("AGHB"),
        "ae": ScriptISO("AVST"),
        "bsq": ScriptISO("BASS"),
        "pli": ScriptISO("BHKS"),
        "zxx": ScriptISO("BYZM"),
        "xcr": ScriptISO("CARI"),
        "xco": ScriptISO("CHRS"),
        "und": ScriptISO("CPMN"),
        "ecy": ScriptISO("CPRT"),
        "hlu": ScriptISO("HLUW"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_eighth_batch_script_entries_have_rendering_and_representative_languages():
    """
    Ensure the eighth script expansion batch is wired into the ontology.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "ELYM": ("xly", "Script=Elymaic"),
        "KAWI": ("kaw", "Script=Kawi"),
        "MAKA": ("mak", "Script=Makasar"),
    }

    for script_iso, (display_language, fontspec_opts) in expected.items():
        info = SCRIPT_INFO[ScriptISO(script_iso)]
        assert info["display_language"] == display_language
        assert info["fontspec_opts"] == fontspec_opts
        assert isinstance(info["specimen"], str) and info["specimen"]


def test_eighth_batch_language_entries_point_back_to_expected_scripts():
    """
    Ensure the eighth script expansion batch has reciprocal language rows.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = {
        "xly": ScriptISO("ELYM"),
        "kaw": ScriptISO("KAWI"),
        "mak": ScriptISO("MAKA"),
    }

    for language, script_iso in expected.items():
        info = LANGUAGE_INFO[language]
        assert script_iso in info["scripts"]
        assert isinstance(info["sample"], str) and info["sample"]


def test_language_info_primary_script_is_present_in_scripts():
    """
    Ensure every language row exposes a valid primary script.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for info in LANGUAGE_INFO.values():
        assert info["primary_script"] in info["scripts"]


def test_script_info_exposes_inference_metadata():
    """
    Ensure every script row carries the data-driven inference fields.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for info in SCRIPT_INFO.values():
        assert isinstance(info["required_blocks"], list)
        assert isinstance(info["optional_blocks"], list)
        assert isinstance(info["suppresses"], list)
        assert isinstance(info["inference_priority"], int)
        assert isinstance(info["unicode_max_ranges"], list)
        assert info["block_match"] in {"exact", "prefix"}
        assert isinstance(info["collapse_group"], str)
        assert isinstance(info["preferred_over"], list)
