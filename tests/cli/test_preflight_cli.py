from fontshow.__main__ import main
from tests.helpers import run_cli


def test_quiet_produces_no_output(monkeypatch):
    # Force CLI behavior directly, bypassing environment-dependent rendering
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "fontshow.__main__.render_preflight_results",
        lambda *args, **kwargs: (0, ""),
    )

    code, out = run_cli(main, ["fontshow", "preflight", "--quiet"])

    assert out == ""
    assert code == 0


def test_default_prints_summary(monkeypatch):
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "fontshow.__main__.render_preflight_results",
        lambda *args, **kwargs: (0, "Preflight passed.\n"),
    )

    code, out = run_cli(main, ["fontshow", "preflight"])

    assert "Preflight passed." in out
    assert code == 0
