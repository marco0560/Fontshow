"""
Verify legacy-format discovery behavior.

Responsibilities
----------------
- Ensure legacy font files are skipped during discovery.
- Ensure supported modern files still pass through discovery.
- Verify discovery skip accounting through observable behavior.

Design principles
-----------------
Tests use fake files and mocked discovery command output so behavior is
deterministic and independent of system font installations.
"""

import json
from types import SimpleNamespace

from fontshow.cli.dump_fonts import run_dump_fonts
from fontshow.platform.font_discovery import (
    get_installed_font_files_linux,
    get_last_discovery_stats,
)
from tests.helpers import (
    create_fake_font_file,
    simulate_dump_discovery,
    simulate_linux_discovery,
)


def test_legacy_font_file_is_skipped_during_linux_discovery(tmp_path, monkeypatch):
    """
    Ensure a legacy discovery candidate is skipped and counted.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to create deterministic fake files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the Fontconfig command execution.

    Returns
    -------
    None
    """
    modern = create_fake_font_file(tmp_path, "Modern-Regular.ttf")
    legacy = create_fake_font_file(tmp_path, "test_font.pfb")

    simulate_linux_discovery(monkeypatch, [modern, legacy])

    discovered = get_installed_font_files_linux()
    stats = get_last_discovery_stats()

    assert discovered == [modern.resolve()]
    assert stats["skipped_legacy_extension"] == 1


def test_legacy_font_skip_never_reaches_dump_inventory(tmp_path, monkeypatch):
    """
    Ensure a legacy candidate is absent from the final dump inventory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for fake input and output files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery and extraction helpers.

    Returns
    -------
    None
    """
    legacy = create_fake_font_file(tmp_path, "test_font.pfb")

    simulate_linux_discovery(monkeypatch, [legacy])
    discovered = get_installed_font_files_linux()
    stats = get_last_discovery_stats()

    simulate_dump_discovery(
        monkeypatch,
        discovered,
        skipped_legacy=stats["skipped_legacy_extension"],
    )

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
    assert stats["skipped_legacy_extension"] == 1
    assert json.loads(output.read_text())["fonts"] == []


def test_discovery_preserves_supported_modern_formats(tmp_path, monkeypatch):
    """
    Ensure supported modern formats still appear in discovery output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to create deterministic fake files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the Fontconfig command execution.

    Returns
    -------
    None
    """
    modern_paths = [
        create_fake_font_file(tmp_path, "Family-Regular.ttf"),
        create_fake_font_file(tmp_path, "Family-Italic.otf"),
        create_fake_font_file(tmp_path, "Collection.ttc"),
        create_fake_font_file(tmp_path, "Collection.otc"),
    ]

    simulate_linux_discovery(monkeypatch, modern_paths)

    discovered = get_installed_font_files_linux()
    stats = get_last_discovery_stats()

    assert discovered == sorted(path.resolve() for path in modern_paths)
    assert stats["skipped_legacy_extension"] == 0
