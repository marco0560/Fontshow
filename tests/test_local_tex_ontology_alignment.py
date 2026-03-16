"""
Audit ontology references against the local TeX installation.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from fontshow.ontology.language_tables import SCRIPT_INFO

_FONT_SPEC_PATH = Path("/usr/share/texmf-dist/tex/latex/fontspec/fontspec-luatex.sty")
_POLYGLOSSIA_DIR = Path("/usr/share/texmf-dist/tex/latex/polyglossia")


def _locate_tex_file(filename: str, fallback: Path) -> Path:
    """
    Locate a TeX resource via ``kpsewhich`` with a deterministic filesystem fallback.

    Parameters
    ----------
    filename : str
        TeX resource name resolved through the Kpathsea database.
    fallback : pathlib.Path
        Filesystem path used when ``kpsewhich`` is unavailable or returns no match.

    Returns
    -------
    pathlib.Path
        Resolved filesystem path for the requested resource or the fallback path.
    """
    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich is None:
        return fallback

    result = subprocess.run(
        [kpsewhich, filename],
        check=False,
        capture_output=True,
        text=True,
    )
    resolved = result.stdout.strip()
    if result.returncode == 0 and resolved:
        return Path(resolved)
    return fallback


def _fontspec_path() -> Path:
    """
    Resolve the local ``fontspec-luatex.sty`` path.

    Returns
    -------
    pathlib.Path
        Resolved path to the local ``fontspec`` style file.
    """
    return _locate_tex_file("fontspec-luatex.sty", _FONT_SPEC_PATH)


def _polyglossia_dir() -> Path:
    """
    Resolve the local Polyglossia module directory.

    Returns
    -------
    pathlib.Path
        Directory expected to contain ``gloss-*.ldf`` language modules.
    """
    gloss_english = _locate_tex_file("gloss-english.ldf", _POLYGLOSSIA_DIR)
    if gloss_english.name.startswith("gloss-") and gloss_english.suffix == ".ldf":
        return gloss_english.parent
    return _POLYGLOSSIA_DIR


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
    fontspec_path = _fontspec_path()
    _require_local_tex_installation(fontspec_path, str(fontspec_path))
    fontspec = fontspec_path.read_text(errors="replace")
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
    polyglossia_dir = _polyglossia_dir()
    _require_local_tex_installation(polyglossia_dir, str(polyglossia_dir))
    local_modules = {
        path.stem.replace("gloss-", "") for path in polyglossia_dir.glob("gloss-*.ldf")
    }

    ontology_languages = {
        info["polyglossia_language"]
        for info in SCRIPT_INFO.values()
        if info["polyglossia_language"]
    }

    assert ontology_languages <= local_modules
