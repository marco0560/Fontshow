import pytest

from fontshow.preflight.checks import environment
from fontshow.preflight.model import Severity
from fontshow.preflight.runner import run_preflight


def test_macos_is_error(monkeypatch):
    monkeypatch.setattr(environment, "detect_os", lambda: "macos")
    monkeypatch.setattr(environment, "detect_execution_mode", lambda: "bare-metal")

    result = run_preflight()
    assert result.overall_severity is Severity.ERROR


@pytest.mark.parametrize(
    "os_name, execution_mode, expected_severity",
    [
        # Linux
        ("linux", "bare-metal", Severity.OK),
        ("linux", "wsl", Severity.WARN),
        ("linux", "container", Severity.WARN),
        ("linux", "ci", Severity.WARN),
        # Windows (experimental)
        ("windows", "bare-metal", Severity.WARN),
        ("windows", "ci", Severity.WARN),
        # macOS (unsupported)
        ("macos", "bare-metal", Severity.ERROR),
        ("macos", "ci", Severity.ERROR),
        # Unknown OS
        ("unknown", "bare-metal", Severity.ERROR),
    ],
)
def test_environment_policy(
    monkeypatch,
    os_name,
    execution_mode,
    expected_severity,
):
    monkeypatch.setattr(environment, "detect_os", lambda: os_name)
    monkeypatch.setattr(
        environment,
        "detect_execution_mode",
        lambda: execution_mode,
    )

    result = run_preflight()

    severities = [
        r.severity for r in result.results if r.check_id == "environment.support"
    ]

    assert severities[-1] is expected_severity
