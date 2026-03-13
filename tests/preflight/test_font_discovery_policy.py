# tests/preflight/test_font_discovery_policy.py

"""
Verify font discovery capability policy.

This module tests the environment policy governing the availability of
font discovery mechanisms used by the Fontshow pipeline.

Responsibilities
----------------
- Validate severity outcomes when Fontconfig is available or missing.
- Ensure environment policy decisions match the expected matrix of
  platform and execution modes.

Design principles
-----------------
Policy tests enumerate environment combinations explicitly so that
changes to platform capability rules are detected deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
policy decisions implemented by the font discovery preflight check.
"""

import pytest

from fontshow.preflight import runner
from fontshow.preflight.checks import font_discovery
from fontshow.preflight.model import Severity


@pytest.mark.parametrize(
    "os_name, execution_mode, has_fc, expected_severity",
    [
        ("linux", "bare-metal", True, Severity.OK),
        ("linux", "bare-metal", False, Severity.ERROR),
        ("linux", "ci", True, Severity.INFO),
        ("windows", "bare-metal", False, Severity.WARN),
        ("macos", "bare-metal", False, Severity.ERROR),
    ],
)
def test_font_discovery_capability_policy(
    monkeypatch,
    os_name,
    execution_mode,
    has_fc,
    expected_severity,
):
    """
    Verify the font-discovery severity matrix across platform combinations.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to override environment and Fontconfig capability checks.
    os_name : str
        Parameterized operating-system classification under test.
    execution_mode : str
        Parameterized execution-mode classification under test.
    has_fc : bool
        Parameterized Fontconfig availability flag.
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
    monkeypatch.setattr(font_discovery, "has_fontconfig", lambda: has_fc)

    result = runner.run_preflight()

    severities = [
        r.severity for r in result.results if r.check_id == "font_discovery.capability"
    ]
    assert severities[-1] is expected_severity
