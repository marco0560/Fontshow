"""
Audit ontology references against the local TeX installation.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fontshow.ontology.language_tables import SCRIPT_INFO

_FONT_SPEC_PATH = Path("/usr/share/texmf-dist/tex/latex/fontspec/fontspec-luatex.sty")
_POLYGLOSSIA_DIR = Path("/usr/share/texmf-dist/tex/latex/polyglossia")


def _require_local_tex_installation(path: Path, description: str) -> None:
    """
    Skip local-TeX alignment tests when the audited installation is absent.

    Parameters
    ----------
    path : pathlib.Path
        Filesystem path required by the local-installation audit.
    description : str
        Human-readable description of the required TeX resource.

    Returns
    -------
    None
    """
    if not path.exists():
        pytest.skip(f"local TeX installation not available: missing {description}")


def test_ontology_fontspec_scripts_exist_in_local_fontspec_install():
    """
    Ensure every Script= value used by the ontology exists locally.

    Returns
    -------
    None
    """
    _require_local_tex_installation(_FONT_SPEC_PATH, str(_FONT_SPEC_PATH))
    fontspec = _FONT_SPEC_PATH.read_text(errors="replace")
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
    _require_local_tex_installation(_POLYGLOSSIA_DIR, str(_POLYGLOSSIA_DIR))
    polyglossia_dir = _POLYGLOSSIA_DIR
    local_modules = {
        path.stem.replace("gloss-", "") for path in polyglossia_dir.glob("gloss-*.ldf")
    }

    ontology_languages = {
        info["polyglossia_language"]
        for info in SCRIPT_INFO.values()
        if info["polyglossia_language"]
    }

    assert ontology_languages <= local_modules
