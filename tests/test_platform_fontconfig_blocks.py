"""
Exercise fontconfig block-splitting edge cases.
"""

from pathlib import Path

import fontshow.platform.fontconfig as fontconfig
from fontshow.platform.fontconfig import _split_fc_query_blocks


def test_split_fc_query_blocks_returns_empty_mapping_without_defaults():
    """
    Ensure markerless output with no default paths remains empty.

    Returns
    -------
    None

    """
    assert _split_fc_query_blocks("family: Example", []) == {}


def test_split_fc_query_blocks_skips_invalid_file_markers_and_keeps_valid_ones(
    monkeypatch,
):
    """
    Ensure malformed file markers do not break subsequent valid blocks.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the `Path` constructor in the code under test.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        Raised by the nested fake path constructor for the sentinel invalid marker.
    """
    real_path = Path

    class FakePath:
        def __new__(cls, value: str):
            """
            Emulate a path constructor that rejects one specific marker.

            Parameters
            ----------
            cls : type
                Class being constructed.
            value : str
                Candidate path string extracted from fontconfig output.

            Returns
            -------
            pathlib.Path
                Real path object for valid values.

            Raises
            ------
            ValueError
                Raised for the sentinel invalid path used by the test.
            """
            if value == "bad":
                msg = "bad path"
                raise ValueError(msg)
            return real_path(value)

    raw = "\n".join(
        [
            'file: "bad"',
            "family: Broken",
            'file: "/tmp/good.ttf"',
            "family: Good",
        ]
    )

    monkeypatch.setattr(fontconfig, "Path", FakePath)
    blocks = _split_fc_query_blocks(raw, [])

    assert blocks == {Path("/tmp/good.ttf"): ["family: Good"]}
