# tests/preflight/test_latex_policy.py

"""
Verify LaTeX capability policy.

This module tests the policy logic that determines how LaTeX toolchain
availability is evaluated during preflight checks.

Responsibilities
----------------
- Validate severity levels when LuaLaTeX is available or missing.
- Ensure policy decisions reflect supported execution environments.

Design principles
-----------------
Capability policy tests enumerate environment combinations explicitly
to guarantee deterministic verification of the toolchain policy.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
policy decisions implemented by the LaTeX capability preflight check.
"""

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
