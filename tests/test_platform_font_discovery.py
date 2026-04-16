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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace platform flags and backend functions.

    Returns
    -------
    None

    Raises
    ------
    PermissionError
        Raised by the nested unreadable-directory stub and ignored by discovery.
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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace platform flags.

    Returns
    -------
    None

    Raises
    ------
    PermissionError
        Raised by the nested unreadable-directory stub and ignored by discovery.
    """
    monkeypatch.setattr(font_discovery, "IS_LINUX", False)
    monkeypatch.setattr(font_discovery, "IS_WINDOWS", False)
    monkeypatch.setattr(font_discovery.sys, "platform", "plan9")

    with pytest.raises(RuntimeError, match="Unsupported platform: plan9"):
        font_discovery.get_installed_font_files()


def test_linux_discovery_raises_when_fc_list_fails(monkeypatch):
    """
    Ensure `fc-list` failures propagate as runtime errors.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the command runner and trace logger.

    Returns
    -------
    None

    Raises
    ------
    PermissionError
        Raised by the nested unreadable-directory stub and ignored by discovery.
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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace environment variables.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage Windows-like directories.

    Returns
    -------
    None

    Raises
    ------
    PermissionError
        Raised by the nested unreadable-directory stub and ignored by discovery.
    """
    windir = tmp_path / "WindowsRoot"
    system_fonts = windir / "Fonts"
    system_fonts.mkdir(parents=True)
    local_fonts = tmp_path / "Local" / "Microsoft" / "Windows" / "Fonts"
    local_fonts.mkdir(parents=True)

    monkeypatch.setenv("WINDIR", str(windir))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))

    dirs = font_discovery._windows_font_dirs()

    assert system_fonts in dirs
    assert local_fonts in dirs


def test_windows_discovery_skips_legacy_and_permission_errors(monkeypatch, tmp_path):
    """
    Ensure Windows scanning keeps modern fonts, skips legacy ones, and ignores bad dirs.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace Windows directory discovery.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage mock font files.

    Returns
    -------
    None

    Raises
    ------
    PermissionError
        Raised by the nested unreadable-directory stub and ignored by discovery.
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
            """
            Raise a deterministic permission error for the test.

            Parameters
            ----------
            _pattern : str
                Glob pattern accepted for interface compatibility.

            Returns
            -------
            None

            Raises
            ------
            PermissionError
                Always raised to emulate an unreadable directory.
            """
            msg = "denied"
            raise PermissionError(msg)

    monkeypatch.setattr(
        font_discovery, "_windows_font_dirs", lambda: [good_dir, BadDir()]
    )

    discovered = font_discovery._get_installed_font_files_windows()

    assert discovered == [modern.resolve()]
    assert font_discovery.get_last_discovery_stats()["skipped_legacy_extension"] == 1


def test_explicit_path_discovery_is_deterministic_and_deduplicated(tmp_path):
    """
    Ensure explicit directory discovery returns sorted unique modern font paths.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage controlled discovery roots.

    Returns
    -------
    None
    """
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    nested = root_b / "nested"
    nested.mkdir(parents=True)
    root_a.mkdir()

    zeta = root_a / "Zeta.ttf"
    alpha = nested / "Alpha.otf"
    legacy = nested / "Legacy.pcf"
    ignored = nested / "README.txt"
    for path in (zeta, alpha, legacy, ignored):
        path.write_text("", encoding="utf-8")

    discovered = font_discovery.get_font_files_from_paths([root_b, root_a, root_b])

    assert discovered == [zeta.resolve(), alpha.resolve()]
    assert font_discovery.get_last_discovery_stats()["skipped_legacy_extension"] == 1


def test_explicit_path_discovery_rejects_missing_path(tmp_path):
    """
    Ensure controlled discovery hard-fails missing roots.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to build a missing path.

    Returns
    -------
    None
    """
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="font discovery path does not exist"):
        font_discovery.get_font_files_from_paths([missing])


def test_explicit_path_discovery_rejects_file_path(tmp_path):
    """
    Ensure controlled discovery accepts only directory roots.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage a non-directory path.

    Returns
    -------
    None
    """
    file_path = tmp_path / "Alpha.ttf"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="font discovery path is not a directory"):
        font_discovery.get_font_files_from_paths([file_path])
