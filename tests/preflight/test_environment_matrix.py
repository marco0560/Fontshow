import pytest

from fontshow.preflight.model import Severity
from tests.helpers import run_preflight_with_environment


@pytest.mark.parametrize(
    "os_name, execution_mode, expected_severity",
    [
        # Linux (reference environment)
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
def test_environment_matrix(
    monkeypatch,
    os_name,
    execution_mode,
    expected_severity,
):
    result = run_preflight_with_environment(
        monkeypatch,
        os_name=os_name,
        execution_mode=execution_mode,
    )

    assert result.overall_severity is expected_severity
