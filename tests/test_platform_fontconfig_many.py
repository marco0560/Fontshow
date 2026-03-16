"""
Exercise additional fontconfig chunking and charset branches.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fontshow.platform import fontconfig


def test_chunk_paths_for_fc_query_splits_large_argument_sets(monkeypatch):
    """
    Ensure very large path strings are chunked instead of emitted as one argv.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture present in the test signature for consistency.

    Returns
    -------
    None
    """
    base = Path("/tmp") / ("a" * 150000)
    paths = [base, Path(str(base) + "b")]

    chunks = fontconfig._chunk_paths_for_fc_query(paths)

    assert chunks == [[paths[0]], [paths[1]]]


def test_run_fc_query_many_maps_missing_blocks_to_empty_strings(monkeypatch):
    """
    Ensure chunked query output preserves input keys even when blocks are absent.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace fontconfig helpers and logging.

    Returns
    -------
    None
    """
    paths = [Path("/tmp/a.ttf"), Path("/tmp/b.ttf")]
    monkeypatch.setattr(
        fontconfig, "_chunk_paths_for_fc_query", lambda incoming: [incoming]
    )
    monkeypatch.setattr(
        fontconfig,
        "run_command",
        lambda argv: SimpleNamespace(
            returncode=0, stdout='file: "/tmp/a.ttf"\nfamily: A', stderr=""
        ),
    )
    monkeypatch.setattr(fontconfig, "log_trace_cat", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(fontconfig.log, "warning", lambda *args, **kwargs: None)

    result = fontconfig._run_fc_query_many(paths)

    assert result == {
        Path("/tmp/a.ttf"): "family: A",
        Path("/tmp/b.ttf"): "",
    }


def test_extract_fc_query_charset_handles_disabled_and_empty_blocks(monkeypatch):
    """
    Ensure charset extraction skips disabled mode and empty payloads.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture present in the test signature for consistency.

    Returns
    -------
    None
    """
    path = Path("/tmp/font.ttf")
    assert (
        fontconfig._extract_fc_query_charset(
            path, ["charset:", "(s)"], include_charset=False
        )
        is None
    )
    assert (
        fontconfig._extract_fc_query_charset(
            path, ["charset:", "(s)", "family: X"], include_charset=True
        )
        is None
    )


def test_parse_fc_query_output_includes_charset_when_requested(monkeypatch):
    """
    Ensure raw parsing combines core fields and charset extraction.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace parsing helpers and trace logging.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        fontconfig,
        "_parse_fc_query_core_fields",
        lambda path, lines: {
            "languages": ["en"],
            "scripts": ["latn"],
            "decorative": False,
            "color": True,
            "variable": False,
        },
    )
    monkeypatch.setattr(
        fontconfig,
        "_extract_fc_query_charset",
        lambda path, lines, include_charset: {"raw": "abcd", "ranges": ["0000-007F"]},
    )
    monkeypatch.setattr(fontconfig, "log_trace_cat", lambda *_args, **_kwargs: None)

    result = fontconfig._parse_fc_query_output(Path("/tmp/font.ttf"), "raw", True)

    assert result == {
        "languages": ["en"],
        "scripts": ["latn"],
        "charset": {"raw": "abcd", "ranges": ["0000-007F"]},
        "decorative": False,
        "color": True,
        "variable": False,
    }
