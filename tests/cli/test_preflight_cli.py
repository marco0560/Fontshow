import sys
from io import StringIO

from fontshow.__main__ import main


def run_cli(main_func, argv):
    old_argv, old_stdout = sys.argv, sys.stdout
    sys.argv = argv
    sys.stdout = StringIO()
    try:
        code = main_func()
        output = sys.stdout.getvalue()
        return code, output
    finally:
        sys.argv, sys.stdout = old_argv, old_stdout


def _fake_preflight_ok():
    return type(
        "PreflightResult",
        (),
        {
            "results": [],
            "overall_severity": type(
                "Severity",
                (),
                {"name": "OK"},
            )(),
        },
    )()


def test_quiet_produces_no_output(monkeypatch):
    # Force preflight to succeed regardless of environment (CI-safe)
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda *args, **kwargs: _fake_preflight_ok(),
    )

    code, out = run_cli(main, ["fontshow", "preflight", "--quiet"])

    assert out == ""
    assert code == 0


def test_default_prints_summary(monkeypatch):
    # Force preflight to succeed regardless of environment (CI-safe)
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda *args, **kwargs: _fake_preflight_ok(),
    )

    code, out = run_cli(main, ["fontshow", "preflight"])

    assert "Preflight passed." in out
    assert code == 0
