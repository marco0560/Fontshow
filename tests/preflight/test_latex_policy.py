# tests/preflight/test_latex_policy.py

import pytest

import fontshow.preflight.checks.latex as latex
import fontshow.preflight.runner as runner
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
