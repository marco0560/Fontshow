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
