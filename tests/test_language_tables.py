"""
Exercise ontology additions for newly supported scripts and languages.
"""

from fontshow.common.specimens import choose_language_sample
from fontshow.core.types import ScriptISO
from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO


def test_script_info_includes_dogra_and_dives_akuru_rendering_entries():
    """
    Ensure dedicated render-policy entries exist for DOGR and DIAK.

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


def test_language_info_primary_script_is_present_in_scripts():
    """
    Ensure every language row exposes a valid primary script.

    Returns
    -------
    None
    """
    for info in LANGUAGE_INFO.values():
        assert info["primary_script"] in info["scripts"]


def test_script_info_exposes_inference_metadata():
    """
    Ensure every script row carries the data-driven inference fields.

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
