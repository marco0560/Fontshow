# tests/preflight/test_latex_policy.py

"""
Verify LaTeX capability policy.

This module tests the policy logic that determines how LaTeX toolchain
availability is evaluated during preflight checks.

Responsibilities
----------------
- Validate severity levels when LuaLaTeX is available or missing.
- Ensure policy decisions reflect supported execution environments.
- Verify ontology-driven TeX capability gaps are reported deterministically.

Design principles
-----------------
Capability policy tests enumerate environment combinations explicitly
and use mocks or temporary files to keep verification deterministic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
policy decisions implemented by the LaTeX capability preflight check.
"""

from __future__ import annotations

import pytest

from fontshow.preflight import runner
from fontshow.preflight.checks import latex
from fontshow.preflight.model import Severity


@pytest.mark.parametrize(
    "os_name, execution_mode, has_lua, expected_severity",
    [
        ("linux", "bare-metal", True, Severity.OK),
        ("linux", "bare-metal", False, Severity.ERROR),
        ("linux", "ci", True, Severity.INFO),
        ("windows", "bare-metal", True, Severity.WARN),
        ("windows", "bare-metal", False, Severity.ERROR),
        ("macos", "bare-metal", False, Severity.ERROR),
    ],
)
def test_lualatex_capability_policy(
    monkeypatch,
    os_name,
    execution_mode,
    has_lua,
    expected_severity,
):
    """
    Verify the LuaLaTeX severity matrix across platform combinations.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to override environment and LuaLaTeX capability checks.
    os_name : str
        Parameterized operating-system classification under test.
    execution_mode : str
        Parameterized execution-mode classification under test.
    has_lua : bool
        Parameterized LuaLaTeX availability flag.
    expected_severity : Severity
        Expected preflight severity for the parameter set.

    Returns
    -------
    None
    """
    monkeypatch.setattr(runner.environment, "detect_os", lambda: os_name)
    monkeypatch.setattr(
        runner.environment, "detect_execution_mode", lambda: execution_mode
    )
    monkeypatch.setattr(latex, "has_lualatex", lambda: has_lua)
    monkeypatch.setattr(
        latex,
        "audit_ontology_tex_capabilities",
        lambda: latex._TeXOntologyCapabilityGap((), ()),
    )

    result = runner.run_preflight()

    severities = [
        r.severity for r in result.results if r.check_id == "latex.capability"
    ]
    assert severities[-1] is expected_severity


def test_has_lualatex_uses_windows_fallback_candidates(monkeypatch):
    """
    Verify that Windows fallback candidates are checked when PATH lookup fails.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace PATH lookup, OS detection, and fallback probing.

    Returns
    -------
    None
    """
    candidate = latex.Path("C:/texlive/2025/bin/windows/lualatex.exe")

    monkeypatch.setattr(latex.shutil, "which", lambda _name: None)
    monkeypatch.setattr(latex.environment, "detect_os", lambda: "windows")
    monkeypatch.setattr(latex, "_windows_lualatex_candidates", lambda: [candidate])
    monkeypatch.setattr(latex.Path, "is_file", lambda path: path == candidate)

    assert latex.has_lualatex() is True


def test_has_lualatex_skips_windows_fallback_on_non_windows(monkeypatch):
    """
    Verify that non-Windows platforms do not consult Windows fallback paths.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace PATH lookup, OS detection, and fallback probing.

    Returns
    -------
    None
    """
    monkeypatch.setattr(latex.shutil, "which", lambda _name: None)
    monkeypatch.setattr(latex.environment, "detect_os", lambda: "linux")

    def fail_if_called():
        """
        Fail deterministically if the Windows fallback is consulted.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            Always raised because Linux should not consult Windows paths.
        """
        msg = "Windows fallback should not be used on Linux"
        raise AssertionError(msg)

    monkeypatch.setattr(latex, "_windows_lualatex_candidates", fail_if_called)

    assert latex.has_lualatex() is False


def test_extract_fontspec_scripts_normalizes_tilde_and_deduplicates():
    """
    Verify that local fontspec script extraction is deterministic.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    text = r"""
    \newfontscript{Arabic}{arab}
    \newfontscript{Dives~Akuru}{diak}
    \newfontscript{Arabic}{arab}
    """

    assert latex._extract_fontspec_scripts(text) == ["Arabic", "Dives Akuru"]


def test_audit_ontology_tex_capabilities_detects_missing_items(tmp_path, monkeypatch):
    """
    Verify that the TeX audit reports missing ontology capabilities.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage mock TeX resources.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace ontology requirements for the test.

    Returns
    -------
    None
    """
    fontspec_path = tmp_path / "fontspec-luatex.sty"
    fontspec_path.write_text(
        "\\newfontscript{Arabic}{arab}\n",
        encoding="utf-8",
    )
    polyglossia_dir = tmp_path / "polyglossia"
    polyglossia_dir.mkdir()
    (polyglossia_dir / "gloss-arabic.ldf").write_text("", encoding="utf-8")

    monkeypatch.setattr(
        latex,
        "SCRIPT_INFO",
        {
            "arab": {
                "fontspec_opts": "Script=Arabic",
                "polyglossia_language": "arabic",
            },
            "kawi": {
                "fontspec_opts": "Script=Kawi",
                "polyglossia_language": "odia",
            },
            "none": {
                "fontspec_opts": "",
                "polyglossia_language": "",
            },
        },
    )

    gap = latex.audit_ontology_tex_capabilities(
        fontspec_path=fontspec_path,
        polyglossia_dir=polyglossia_dir,
    )

    assert gap.missing_fontspec_scripts == ("Kawi",)
    assert gap.missing_polyglossia_languages == ("odia",)


def test_lualatex_capability_reports_missing_ontology_support_on_linux(monkeypatch):
    """
    Verify that Linux preflight fails on missing ontology TeX capabilities.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace environment and TeX capability helpers.

    Returns
    -------
    None
    """
    monkeypatch.setattr(runner.environment, "detect_os", lambda: "linux")
    monkeypatch.setattr(
        runner.environment, "detect_execution_mode", lambda: "bare-metal"
    )
    monkeypatch.setattr(latex, "has_lualatex", lambda: True)
    monkeypatch.setattr(
        latex,
        "audit_ontology_tex_capabilities",
        lambda: latex._TeXOntologyCapabilityGap(("Kawi",), ("odia",)),
    )

    result = runner.run_preflight()

    latex_result = next(r for r in result.results if r.check_id == "latex.capability")
    assert latex_result.severity is Severity.ERROR
    assert "missing fontspec scripts: Kawi" in latex_result.message
    assert "missing Polyglossia modules: odia" in latex_result.message


def test_lualatex_capability_reports_missing_ontology_support_on_windows(monkeypatch):
    """
    Verify that Windows preflight downgrades ontology gaps to warnings.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace environment and TeX capability helpers.

    Returns
    -------
    None
    """
    monkeypatch.setattr(runner.environment, "detect_os", lambda: "windows")
    monkeypatch.setattr(
        runner.environment, "detect_execution_mode", lambda: "bare-metal"
    )
    monkeypatch.setattr(latex, "has_lualatex", lambda: True)
    monkeypatch.setattr(
        latex,
        "audit_ontology_tex_capabilities",
        lambda: latex._TeXOntologyCapabilityGap(("Cypro-Minoan",), ()),
    )

    result = runner.run_preflight()

    latex_result = next(r for r in result.results if r.check_id == "latex.capability")
    assert latex_result.severity is Severity.WARN
    assert "missing fontspec scripts: Cypro-Minoan" in latex_result.message
