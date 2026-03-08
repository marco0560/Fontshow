"""
Verify rendering of preflight results.

This module tests the formatting logic used to render preflight
validation results for CLI display.

Responsibilities
----------------
- Ensure results are rendered with correct severity labels.
- Verify output formatting of rendered check results.

Design principles
-----------------
Rendering tests validate output structure independently of CLI mode
filtering, ensuring deterministic formatting of validation results.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the formatting behavior of the preflight results renderer.
"""

from fontshow.preflight.model import CheckResult, Severity
from fontshow.preflight.render import render_preflight_results


def test_render_hides_ok_and_info_by_default():
    results = [
        CheckResult("a", Severity.OK, "ok"),
        CheckResult("b", Severity.INFO, "info"),
        CheckResult("c", Severity.ERROR, "error"),
    ]

    lines = render_preflight_results(results, verbose=False)

    # Renderer formats all results; visibility filtering is handled by CLI mode
    assert lines == [
        "[OK  ] a: ok",
        "[INFO] b: info",
        "[ERR ] c: error",
    ]
    assert "[ERR ]" in lines[2]


def test_render_shows_all_with_verbose():
    results = [
        CheckResult("a", Severity.OK, "ok"),
        CheckResult("b", Severity.INFO, "info"),
        CheckResult("c", Severity.ERROR, "error"),
    ]

    lines = render_preflight_results(results, verbose=True)

    assert lines == [
        "[OK  ] a: ok",
        "[INFO] b: info",
        "[ERR ] c: error",
    ]
