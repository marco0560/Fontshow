from fontshow.preflight.model import CheckResult, Severity
from fontshow.preflight.render import render_preflight_results


def test_render_hides_ok_and_info_by_default():
    results = [
        CheckResult("a", Severity.OK, "ok"),
        CheckResult("b", Severity.INFO, "info"),
        CheckResult("c", Severity.ERROR, "error"),
    ]

    lines = render_preflight_results(results, verbose=False)

    assert len(lines) == 1
    assert "[ERROR]" in lines[0]


def test_render_shows_all_with_verbose():
    results = [
        CheckResult("a", Severity.OK, "ok"),
        CheckResult("b", Severity.INFO, "info"),
        CheckResult("c", Severity.ERROR, "error"),
    ]

    lines = render_preflight_results(results, verbose=True)

    assert len(lines) == 3
