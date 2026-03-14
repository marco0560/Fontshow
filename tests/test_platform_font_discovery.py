"""
Exercise font discovery dispatch and platform-specific edge cases.

Responsibilities
----------------
- Cover public dispatch and unsupported-platform failure.
- Verify Linux failure handling and Windows directory scanning behavior.
- Keep discovery deterministic with temporary directories and monkeypatching.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from fontshow.platform import font_discovery


def test_get_installed_font_files_dispatches_by_platform(monkeypatch):
    """
    Ensure the public dispatcher selects the active backend.
    """
    monkeypatch.setattr(font_discovery, "IS_LINUX", True)
    monkeypatch.setattr(font_discovery, "IS_WINDOWS", False)
    monkeypatch.setattr(
        font_discovery, "get_installed_font_files_linux", lambda: [Path("/linux.ttf")]
    )

    assert font_discovery.get_installed_font_files() == [Path("/linux.ttf")]

    monkeypatch.setattr(font_discovery, "IS_LINUX", False)
    monkeypatch.setattr(font_discovery, "IS_WINDOWS", True)
    monkeypatch.setattr(
        font_discovery,
        "_get_installed_font_files_windows",
        lambda: [Path("/windows.ttf")],
    )

    assert font_discovery.get_installed_font_files() == [Path("/windows.ttf")]


def test_get_installed_font_files_raises_for_unsupported_platform(monkeypatch):
    """
    Ensure unsupported platforms fail with a clear runtime error.
    """
    monkeypatch.setattr(font_discovery, "IS_LINUX", False)
    monkeypatch.setattr(font_discovery, "IS_WINDOWS", False)
    monkeypatch.setattr(font_discovery.sys, "platform", "plan9")

    with pytest.raises(RuntimeError, match="Unsupported platform: plan9"):
        font_discovery.get_installed_font_files()


def test_linux_discovery_raises_when_fc_list_fails(monkeypatch):
    """
    Ensure `fc-list` failures propagate as runtime errors.
    """
    monkeypatch.setattr(
        font_discovery,
        "run_command",
        lambda _cmd: SimpleNamespace(returncode=1, stdout="boom"),
    )
    monkeypatch.setattr(font_discovery, "log_trace_cat", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="fc-list failed:\nboom"):
        font_discovery.get_installed_font_files_linux()


def test_windows_font_dirs_filters_missing_directories(monkeypatch, tmp_path):
    """
    Ensure only existing Windows font directories are returned.
    """
    windir = tmp_path / "WindowsRoot"
    system_fonts = windir / "Fonts"
    system_fonts.mkdir(parents=True)
    local_fonts = tmp_path / "Local" / "Microsoft" / "Windows" / "Fonts"
    local_fonts.mkdir(parents=True)

    monkeypatch.setenv("WINDIR", str(windir))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))

    dirs = font_discovery._windows_font_dirs()

    assert dirs == [system_fonts, local_fonts]


def test_windows_discovery_skips_legacy_and_permission_errors(monkeypatch, tmp_path):
    """
    Ensure Windows scanning keeps modern fonts, skips legacy ones, and ignores bad dirs.
    """
    good_dir = tmp_path / "good"
    good_dir.mkdir()
    modern = good_dir / "Alpha.ttf"
    legacy = good_dir / "Legacy.pfb"
    ignored = good_dir / "Note.txt"
    modern.write_text("", encoding="utf-8")
    legacy.write_text("", encoding="utf-8")
    ignored.write_text("", encoding="utf-8")

    class BadDir:
        def rglob(self, _pattern: str):
            msg = "denied"
            raise PermissionError(msg)

    monkeypatch.setattr(
        font_discovery, "_windows_font_dirs", lambda: [good_dir, BadDir()]
    )

    discovered = font_discovery._get_installed_font_files_windows()

    assert discovered == [modern.resolve()]
    assert font_discovery.get_last_discovery_stats()["skipped_legacy_extension"] == 1
