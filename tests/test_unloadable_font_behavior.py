"""
Verify structurally unloadable font behavior in dump-fonts.

Responsibilities
----------------
- Ensure unloadable fonts are skipped from the inventory.
- Ensure unloadable skip accounting increments deterministically.
- Ensure repeated warnings are deduplicated per font file.

Design principles
-----------------
Tests mock discovery and fontTools extraction so no real font parsing
or system font access is required.
"""

import json
from types import SimpleNamespace

from fontshow.cli.dump_fonts import run_dump_fonts
from tests.helpers import (
    capture_dump_summary,
    create_fake_font_file,
    simulate_dump_discovery,
    simulate_unloadable_font,
)


def test_unloadable_font_is_skipped_and_warned_once(tmp_path, monkeypatch):
    """
    Ensure a structurally unloadable font is skipped and warned once.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for fake input and output files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery, extraction, and logging helpers.

    Returns
    -------
    None
    """
    font_path = create_fake_font_file(tmp_path, "BrokenCollection.ttc")
    simulate_dump_discovery(monkeypatch, [font_path], skipped_legacy=0)
    simulate_unloadable_font(monkeypatch, faces=2)
    warnings, infos = capture_dump_summary(monkeypatch)

    output = tmp_path / "fonts.json"
    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        verbose=False,
    )

    ret = run_dump_fonts(args)

    assert ret == 0
    assert json.loads(output.read_text())["fonts"] == []
    assert warnings == [f"skipping structurally-unloadable font: {font_path}"]

    summary = next(extra for message, extra in infos if message == "dump-fonts summary")
    assert summary["skipped_structurally_unloadable"] == 2
    assert summary["total_fonts"] == 0
