import fontshow.preflight.checks.environment as environment
from fontshow.preflight.model import Severity
from fontshow.preflight.runner import run_preflight


def test_macos_is_error(monkeypatch):
    monkeypatch.setattr(environment, "detect_os", lambda: "macos")
    monkeypatch.setattr(environment, "detect_execution_mode", lambda: "bare-metal")

    result = run_preflight()
    assert result.overall_severity is Severity.ERROR
