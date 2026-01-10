import pytest


def test_fontshow_root_version(capsys, monkeypatch):
    from fontshow.__main__ import main

    monkeypatch.setattr("sys.argv", ["fontshow", "-V"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert out.startswith("fontshow ")
    assert "development" not in out


def test_fontshow_preflight_version(capsys, monkeypatch):
    from fontshow.__main__ import main

    monkeypatch.setattr("sys.argv", ["fontshow", "preflight", "-V"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert out.startswith("fontshow preflight ")
