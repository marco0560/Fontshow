from pathlib import Path

from helpers import make_fc_query_output

from fontshow.dump_fonts import fc_query_extract


def test_fc_query_extract_basic(monkeypatch):
    monkeypatch.setattr(
        "fontshow.dump_fonts.run_command",
        lambda cmd: make_fc_query_output(
            lang="en|it",
            scripts=["latn", "grek"],
            decorative=False,
            color=False,
            variable=True,
        ),
    )

    result = fc_query_extract(Path("/fake/font.ttf"))

    assert result["languages"] == ["en", "it"]
    assert set(result["scripts"]) == {"latn", "grek"}
    assert result["decorative"] is False
    assert result["color"] is False
    assert result["variable"] is True


def test_fc_query_extract_no_capability(monkeypatch):
    monkeypatch.setattr(
        "fontshow.dump_fonts.run_command",
        lambda cmd: make_fc_query_output(lang="en"),
    )

    result = fc_query_extract(Path("/fake/font.ttf"))

    assert result["languages"] == ["en"]
    assert result["scripts"] == []


def test_fc_query_extract_empty_output(monkeypatch):
    monkeypatch.setattr(
        "fontshow.dump_fonts.run_command",
        lambda cmd: make_fc_query_output(),
    )

    result = fc_query_extract(Path("/fake/font.ttf"))

    assert result["languages"] == []
    assert result["scripts"] == []
    assert result["decorative"] is False
    assert result["color"] is False
    assert result["variable"] is False
