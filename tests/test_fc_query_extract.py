from pathlib import Path

from fontshow.platform.fontconfig import fc_query_extract
from tests.helpers import make_fc_query_output


def test_fc_query_extract_basic(monkeypatch):
    monkeypatch.setattr(
        "fontshow.platform.fontconfig.run_command",
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
        "fontshow.platform.fontconfig.run_command",
        lambda cmd: make_fc_query_output(lang="en"),
    )

    result = fc_query_extract(Path("/fake/font.ttf"))

    assert result["languages"] == ["en"]
    assert result["scripts"] == []


def test_fc_query_extract_empty_output(monkeypatch):
    monkeypatch.setattr(
        "fontshow.platform.fontconfig.run_command",
        lambda cmd: make_fc_query_output(),
    )

    result = fc_query_extract(Path("/fake/font.ttf"))

    assert result["languages"] == []
    assert result["scripts"] == []
    assert result["decorative"] is False
    assert result["color"] is False
    assert result["variable"] is False
