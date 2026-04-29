"""
Font discovery helpers.

This module implements platform-specific mechanisms used to locate
installed font files on the host system.

Responsibilities
----------------
- Enumerate installed font files.
- Implement platform-specific discovery strategies.
- Provide a uniform interface for higher-level pipeline modules.

Design principles
-----------------
Font discovery is limited to locating font files on the system and does
not perform font parsing or metadata extraction. Platform-specific code
is confined to the platform subsystem to keep the inventory pipeline
portable.

Architectural role
------------------
This module belongs to the **platform subsystem** and provides the font
discovery stage used by the `dump-fonts` workflow.

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
from fontshow.constants.discovery import (
    DISCOVERABLE_FONT_EXTENSIONS,
    LEGACY_FONT_EXTENSIONS,
)
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.inventory.utils import run_command

_LAST_DISCOVERY_STATS = {"skipped_legacy_extension": 0}


def _has_legacy_font_extension(path: Path) -> bool:
    """
    Return whether the path uses a legacy font extension.

    Parameters
    ----------
    path : pathlib.Path
        Candidate font path produced by the discovery backend.

    Returns
    -------
    bool
        True when the filename matches a known legacy extension.

    Notes
    -----
    Matching is case-insensitive and supports compound extensions such
    as ``.pcf.gz``.
    """
    name = path.name.lower()
    return any(name.endswith(ext) for ext in LEGACY_FONT_EXTENSIONS)


def get_last_discovery_stats() -> dict[str, int]:
    """
    Return metrics captured by the most recent discovery run.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, int]
        Copy of the latest discovery counters.
    """
    return dict(_LAST_DISCOVERY_STATS)


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

    Notes
    -----
    This is the public platform-dispatch entry point used by the
    inventory discovery workflow.
    """
    if IS_LINUX:
        return get_installed_font_files_linux()
    if IS_WINDOWS:
        return _get_installed_font_files_windows()
    msg = f"Unsupported platform: {sys.platform}"
    raise RuntimeError(msg)


def get_font_files_from_paths(paths: list[Path]) -> list[Path]:
    """
    Discover font files below explicit user-provided directories.

    Parameters
    ----------
    paths : list[pathlib.Path]
        Directory roots to scan recursively.

    Returns
    -------
    list[pathlib.Path]
        Sorted list of unique font file paths with recognized extensions.

    Raises
    ------
    ValueError
        If any provided path does not exist or is not a directory.
    OSError
        If resolving or traversing a provided directory fails.

    Notes
    -----
    This controlled-discovery path does not call platform system
    discovery backends. Traversal results are resolved, deduplicated,
    filtered, and sorted for deterministic downstream processing.
    """
    global _LAST_DISCOVERY_STATS

    roots: list[Path] = []
    for raw_path in paths:
        if not raw_path.exists():
            msg = f"font discovery path does not exist: {raw_path}"
            raise ValueError(msg)
        if not raw_path.is_dir():
            msg = f"font discovery path is not a directory: {raw_path}"
            raise ValueError(msg)
        roots.append(raw_path.resolve())

    found: set[Path] = set()
    skipped_legacy_extension = 0
    for root in sorted(set(roots)):
        for path in root.rglob("*"):
            if _has_legacy_font_extension(path):
                if path.is_file():
                    skipped_legacy_extension += 1
                continue
            if path.suffix.lower() in DISCOVERABLE_FONT_EXTENSIONS:
                if not path.is_file():
                    continue
                found.add(path.resolve())

    _LAST_DISCOVERY_STATS = {
        "skipped_legacy_extension": skipped_legacy_extension,
    }
    return sorted(found)


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

    Notes
    -----
    Results are resolved, deduplicated, filtered to existing paths, and
    returned in sorted order for deterministic downstream processing.
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

    global _LAST_DISCOVERY_STATS

    files: list[Path] = []
    skipped_legacy_extension = 0
    for line in proc.stdout.splitlines():
        p = line.strip()
        if p:
            path = Path(p)
            if _has_legacy_font_extension(path):
                skipped_legacy_extension += 1
                continue
            files.append(path)

    # Resolve + unique
    discovered = sorted({p.resolve() for p in files if p.exists()})
    _LAST_DISCOVERY_STATS = {
        "skipped_legacy_extension": skipped_legacy_extension,
    }
    return discovered


def _windows_font_dirs() -> list[Path]:
    r"""
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
    ``%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts``

    The returned list contains only directories that currently exist.
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


def _get_installed_font_files_windows() -> list[Path]:
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
    global _LAST_DISCOVERY_STATS

    found: set[Path] = set()
    skipped_legacy_extension = 0
    for d in _windows_font_dirs():
        try:
            for p in d.rglob("*"):
                if p.is_file() and _has_legacy_font_extension(p):
                    skipped_legacy_extension += 1
                    continue
                if p.is_file() and p.suffix.lower() in DISCOVERABLE_FONT_EXTENSIONS:
                    found.add(p.resolve())
        except (PermissionError, OSError):
            # ignore permission issues etc.
            continue
    _LAST_DISCOVERY_STATS = {
        "skipped_legacy_extension": skipped_legacy_extension,
    }
    return sorted(found)
