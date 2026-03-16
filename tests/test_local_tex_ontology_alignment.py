"""
Audit ontology references against the local TeX installation.
"""

from __future__ import annotations

import re
from pathlib import Path

from fontshow.ontology.language_tables import SCRIPT_INFO


def test_ontology_fontspec_scripts_exist_in_local_fontspec_install():
    """
    Ensure every Script= value used by the ontology exists locally.

    Returns
    -------
    None
    """
    fontspec = Path(
        "/usr/share/texmf-dist/tex/latex/fontspec/fontspec-luatex.sty"
    ).read_text(errors="replace")
    local_scripts = {
        name.replace("~", " ")
        for name in re.findall(r"\\newfontscript\{([^}]+)\}\{", fontspec)
    }

    ontology_scripts = {
        info["fontspec_opts"][len("Script=") :].strip("{}")
        for info in SCRIPT_INFO.values()
        if info["fontspec_opts"].startswith("Script=")
    }

    assert ontology_scripts <= local_scripts


def test_ontology_polyglossia_languages_exist_in_local_modules():
    """
    Ensure every Polyglossia language referenced by the ontology is installed.

    Returns
    -------
    None
    """
    polyglossia_dir = Path("/usr/share/texmf-dist/tex/latex/polyglossia")
    local_modules = {
        path.stem.replace("gloss-", "") for path in polyglossia_dir.glob("gloss-*.ldf")
    }

    ontology_languages = {
        info["polyglossia_language"]
        for info in SCRIPT_INFO.values()
        if info["polyglossia_language"]
    }

    assert ontology_languages <= local_modules
