"""
Verify environment compatibility matrix.

This module tests the behavior of the preflight environment checks
across different operating system and execution-mode combinations.

Responsibilities
----------------
- Validate that supported environments are accepted.
- Ensure unsupported environments produce the correct severity.
- Verify the environment compatibility matrix enforced by preflight.

Design principles
-----------------
Matrix tests enumerate environment combinations explicitly so that
policy regressions are detected deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the environment policy enforced by the preflight validation subsystem.
"""

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
        # Windows (experimental platform)
        ("windows", "bare-metal", Severity.WARN),
        ("windows", "ci", Severity.WARN),
        # macOS (unsupported platform)
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
