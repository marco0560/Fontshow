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


def test_quiet_produces_no_output(monkeypatch):
    # forza preflight "OK" senza ERROR
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda: type(
            "R",
            (),
            {"results": [], "overall_severity": type("S", (), {"name": "OK"})()},
        )(),
    )

    code, out = run_cli(main, ["fontshow", "--quiet"])
    assert out == ""
    assert code == 0


def test_default_prints_summary(monkeypatch):
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda: type(
            "R",
            (),
            {"results": [], "overall_severity": type("S", (), {"name": "OK"})()},
        )(),
    )

    code, out = run_cli(main, ["fontshow"])
    assert "Preflight passed." in out
    assert code == 0
