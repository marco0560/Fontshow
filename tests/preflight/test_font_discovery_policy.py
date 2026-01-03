# tests/preflight/test_font_discovery_policy.py

import pytest

import fontshow.preflight.checks.font_discovery as font_discovery
import fontshow.preflight.runner as runner
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
