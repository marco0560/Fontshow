"""
Fontshow – platform.font_discovery
==================================

Font discovery utilities used by the dump-fonts pipeline.

This module contains platform-specific logic used to locate font files
installed on the system. The goal is to isolate operating-system
interaction from the higher-level inventory pipeline.

Responsibilities
----------------
• Enumerate installed font files
• Implement platform-specific discovery logic
• Provide a uniform interface to the pipeline layer

Design principles
-----------------
• Platform-specific code lives only in the platform layer
• No dependency on inventory or catalog modules
• Pure discovery: no font parsing or metadata extraction
• Deterministic results based on the system environment

Supported platforms
-------------------
• Linux (via fontconfig and standard font directories)
• Windows (via system font directories)

Pipeline entrypoints such as dump_fonts.py rely on this module to obtain
the list of font files that will later be inspected and processed.
"""

import os
import sys
from pathlib import Path

from fontshow.constants.catalog import IS_LINUX, IS_WINDOWS
from fontshow.inventory.utils import run_command
from fontshow.logging_utils import log, log_trace_cat


def get_installed_font_files() -> list[Path]:
    """
    Dispatch font file discovery according to the current platform.

    Parameters
    ----------
    None

    Returns
    -------
    list[pathlib.Path]
        List of discovered font file paths for the current platform.

    Raises
    ------
    RuntimeError
        If the current platform is unsupported.
    """
    if IS_LINUX:
        return get_installed_font_files_linux()
    if IS_WINDOWS:
        return get_installed_font_files_windows()
    msg = f"Unsupported platform: {sys.platform}"
    raise RuntimeError(msg)


def get_installed_font_files_linux() -> list[Path]:
    """
    Discover installed font files on Linux using FontConfig (`fc-list`).

    Parameters
    ----------
    None

    Returns
    -------
    list[pathlib.Path]
        Sorted list of unique existing font file paths discovered via `fc-list`.

    Raises
    ------
    RuntimeError
        If `fc-list` execution fails.
    """
    from time import perf_counter

    t0 = perf_counter()
    proc = run_command(["fc-list", "--format=%{file}\n"])
    duration_ms = int((perf_counter() - t0) * 1000)

    log_trace_cat(
        log,
        "perf",
        "fc-list timing",
        extra={
            "duration_ms": duration_ms,
            "exit_code": proc.returncode,
        },
    )

    if proc.returncode != 0:
        msg = f"fc-list failed:\n{proc.stdout}"
        raise RuntimeError(msg)

    files: list[Path] = []
    for line in proc.stdout.splitlines():
        p = line.strip()
        if p:
            files.append(Path(p))

    # Resolve + unique
    return sorted({p.resolve() for p in files if p.exists()})


def _windows_font_dirs() -> list[Path]:
    """
    Return known Windows font directories (system and user scopes).

    Parameters
    ----------
    None

    Returns
    -------
    list[pathlib.Path]
        Existing directories that may contain installed fonts.

    Notes
    -----
    Windows supports per-user font installs under:
    %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts
    """
    dirs: list[Path] = []
    windir = os.environ.get("WINDIR") or os.environ.get("SYSTEMROOT")
    if windir:
        dirs.append(Path(windir) / "Fonts")

    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")

    # Fallback guess
    dirs.append(Path("C:/Windows/Fonts"))
    return [d for d in dirs if d.exists()]


def get_installed_font_files_windows() -> list[Path]:
    """
    Discover installed font files on Windows by scanning known font directories.

    Parameters
    ----------
    None

    Returns
    -------
    list[pathlib.Path]
        Sorted list of unique font file paths with recognized extensions.

    Notes
    -----
    Recognized extensions include: .ttf, .otf, .ttc, .otc, .woff, .woff2.
    Permission errors during directory traversal are ignored.
    """
    exts = {".ttf", ".otf", ".ttc", ".otc", ".woff", ".woff2"}
    found: set[Path] = set()
    for d in _windows_font_dirs():
        try:
            for p in d.rglob("*"):
                if p.is_file() and p.suffix.lower() in exts:
                    found.add(p.resolve())
        except (PermissionError, OSError):
            # ignore permission issues etc.
            continue
    return sorted(found)
