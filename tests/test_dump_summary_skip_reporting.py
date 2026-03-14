"""
Verify dump-fonts summary skip reporting.

Responsibilities
----------------
- Ensure summary reporting includes legacy and unloadable skip counters.
- Ensure summary data remains deterministic for mocked dump execution.

Design principles
-----------------
Tests capture logger inputs directly and avoid real font discovery or
font parsing so execution remains fast and stable.
"""

from types import SimpleNamespace

from fontshow.cli.dump_fonts import run_dump_fonts
from tests.helpers import (
    capture_dump_summary,
    create_fake_font_file,
    simulate_dump_discovery,
    simulate_unloadable_font,
)


def test_dump_summary_reports_skip_counters_in_stable_order(tmp_path, monkeypatch):
    """
    Ensure dump-fonts summary includes both skip counters in stable order.

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
    simulate_dump_discovery(monkeypatch, [font_path], skipped_legacy=1)
    simulate_unloadable_font(monkeypatch, faces=2)
    _warnings, infos = capture_dump_summary(monkeypatch)

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

    summary = next(extra for message, extra in infos if message == "dump-fonts summary")
    assert set(summary) == {
        "total_faces_seen",
        "total_font_files",
        "total_fonts",
        "skipped_legacy_extension",
        "skipped_structurally_unloadable",
        "skipped_non_opentype_faces",
        "style_leak_suspected",
    }
    assert summary["skipped_legacy_extension"] == 1
    assert summary["skipped_structurally_unloadable"] == 2
