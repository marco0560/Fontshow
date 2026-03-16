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
