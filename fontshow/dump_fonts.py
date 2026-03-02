"""
Fontshow raw inventory generation.

This module produces a *raw* Fontshow inventory (schema_version = 1.0) by
collecting font metadata from system sources such as FontConfig.

The output of this stage is intentionally best-effort and informational:
- metadata may be incomplete or partially missing,
- no semantic interpretation or inference is performed here,
- extracted data is preserved verbatim for downstream enrichment.

In particular, FontConfig-derived charset metadata (when enabled) is extracted
and serialized but not interpreted at this stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fontshow import __version__
from fontshow.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.json_format import dumps_pretty
from fontshow.logging_utils import log, log_trace_cat
from fontshow.platform_metadata import collect_platform_metadata
from fontshow.types import Severity, WarningInfo
from fontshow.unicode_tables import UNICODE_BLOCK_RANGES

if TYPE_CHECKING:
    # Types only — no runtime side effects
    from fontTools.misc import timeTools
    from fontTools.ttLib import TTCollection, TTFont, TTLibError

    FONTTOOLS_AVAILABLE = True

else:
    try:
        from fontTools.misc import timeTools
        from fontTools.ttLib import TTCollection, TTFont, TTLibError

        FONTTOOLS_AVAILABLE = True

        # Silence fontTools timestamp sanity warnings (if supported)
        if hasattr(timeTools, "TIMESTAMP_WARNINGS"):
            timeTools.TIMESTAMP_WARNINGS = False

    except ImportError:
        FONTTOOLS_AVAILABLE = False

        class TTLibError(Exception):
            """Fallback error type when fontTools is not installed."""

            _MSG = "fontTools is not installed"

            def __init__(self) -> None:
                super().__init__(self._MSG)

        class TTFont:
            """Runtime placeholder to avoid NameError when fontTools is missing."""

            def __init__(self, *_args, **_kwargs) -> None:
                raise TTLibError

        class TTCollection:
            """Runtime placeholder to avoid NameError when fontTools is missing."""

            def __init__(self, *_args, **_kwargs) -> None:
                raise TTLibError


"""
Logging conventions
-------------------

This module uses the shared Fontshow logger (`fontshow.logging_utils.log`).

All log messages:
- are structured (use `extra={}`),
- never print directly to stdout,
- are intended to be machine-readable,
- may be formatted by the CLI layer.

Logging levels:
- INFO    → user-visible pipeline progress
- DEBUG   → internal state / diagnostics
- TRACE   → low-level execution tracing
- WARNING → recoverable errors
"""

# -----------------------
# fontTools extraction
# -----------------------
NAME_ID_FAMILY = 1
NAME_ID_SUBFAMILY = 2
NAME_ID_FULLNAME = 4
NAME_ID_POSTSCRIPT = 6
NAME_ID_VERSION = 5
NAME_ID_LICENSE = 13
NAME_ID_LICENSE_URL = 14
NAME_ID_SAMPLE_TEXT = 19

# -----------------------
# Platform helpers
# -----------------------
IS_LINUX = sys.platform.startswith("linux")
IS_WINDOWS = sys.platform.startswith("win")


def utc_now_iso() -> str:
    """
    Return the current UTC timestamp in ISO-8601 format (seconds precision).

    Parameters
    ----------
    None

    Returns
    -------
    str
        Current UTC time formatted as an ISO-8601 string without microseconds.
    """
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def run_command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Execute a subprocess command and capture combined stdout/stderr.

    Parameters
    ----------
    argv : list[str]
        Argument vector to pass to subprocess.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process object with stdout captured as text and
        stderr redirected to stdout. The process is not checked for
        non-zero exit status.
    """
    return subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def make_font_id(path: str, ttc_index: int | None) -> str:
    """
    Build a stable, reproducible identifier for a font face.

    Parameters
    ----------
    path : str
        Filesystem path to the font file.
    ttc_index : int | None
        Face index for TrueType Collections, or None for single-face fonts.

    Returns
    -------
    str
        Short hexadecimal identifier derived from path and TTC index.

    Notes
    -----
    Intended for comparison, caching, and debugging purposes.
    """
    key = f"{path}|{ttc_index if ttc_index is not None else 'single'}"
    return sha1(key.encode("utf-8")).hexdigest()[:12]


# -----------------------
# Font discovery
# -----------------------


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


# ----------------------------------------------------------------------
# Charset synthesis helpers (discovery phase)
# ----------------------------------------------------------------------


def _charset_ranges_from_ttfont(tt: TTFont) -> list[list[int]]:
    """
    Extract merged Unicode codepoint ranges from cmap tables.

    Returns
    -------
    list[list[int]]
        Sorted contiguous codepoint ranges [[start, end], ...].

    Notes
    -----
    Discovery-only helper:
    - performs no semantic interpretation
    - deterministic output
    """
    try:
        cmap = tt["cmap"]
    except KeyError:
        return []

    codepoints: set[int] = set()

    for table in cmap.tables:
        if not table.isUnicode():
            continue
        codepoints.update(table.cmap.keys())

    if not codepoints:
        return []

    sorted_cps = sorted(codepoints)

    ranges: list[list[int]] = []
    start = prev = sorted_cps[0]

    for cp in sorted_cps[1:]:
        if cp == prev + 1:
            prev = cp
            continue

        ranges.append([start, prev])
        start = prev = cp

    ranges.append([start, prev])
    return ranges


# -----------------------
# Container detection
# -----------------------


def detect_font_container(path: Path) -> str:
    """
    Detect font container format using file header and extension.

    Parameters
    ----------
    path : pathlib.Path
        Path to the font file.

    Returns
    -------
    str
        Detected container type: "TTF", "OTF", "TTC", "WOFF", "WOFF2",
        or "UNKNOWN" if not recognized.
    """
    ext = path.suffix.lower()
    try:
        with path.open("rb") as f:
            head = f.read(4)
    except OSError:
        head = b""

    if head == b"ttcf":
        return "TTC"
    if head == b"wOFF" or ext == ".woff":
        return "WOFF"
    if head == b"wOF2" or ext == ".woff2":
        return "WOFF2"
    if head == b"OTTO" or ext == ".otf":
        return "OTF"
    if head in (b"\x00\x01\x00\x00", b"true", b"typ1") or ext == ".ttf":
        return "TTF"
    if ext == ".ttc":
        return "TTC"
    return "UNKNOWN"


# -----------------------
# Cache
# -----------------------


def font_cache_key(path: Path, ttc_index: int | None = None) -> str:
    """
    Return a stable cache key for a font face.

    Parameters
    ----------
    path : pathlib.Path
        Path to the font file.
    ttc_index : int | None, optional
        Face index for TrueType Collections (None for single-face fonts).

    Returns
    -------
    str
        SHA-256 hexadecimal digest suitable for use as a cache filename.

    Notes
    -----
    The key combines:
    - absolute file path,
    - file modification time (nanoseconds),
    - file size,
    - optional TTC face index.

    Ensures cache invalidation when the font file changes.
    """
    st = path.stat()
    idx = "" if ttc_index is None else f"|ttc:{ttc_index}"
    key = f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}{idx}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# -----------------------
# Linux-only: FontConfig enrichment
# -----------------------


def extract_sample_text(font_path: str) -> list[str] | None:
    """
    Extract embedded sample text from a font file.

    Parameters
    ----------
    font_path : str
        Filesystem path to the font file.

    Returns
    -------
    list[str] | None
        List of unique embedded sample text strings if present,
        otherwise None.

    Notes
    -----
    Extraction is best-effort and silently ignores malformed
    or partially corrupted name table entries.
    """
    try:
        # Silence TTFont info logs, which can be noisy on malformed fonts
        # and are not relevant for sample text extraction. We want to preserve
        # any errors, however.
        tt = TTFont(font_path, lazy=True)
    except (OSError, ValueError, TTLibError):
        return None

    if "name" not in tt:
        tt.close()
        return None

    name_table = tt["name"]

    seen: set[str] = set()
    unique_samples: list[str] = []

    for record in name_table.names:
        if record.nameID != NAME_ID_SAMPLE_TEXT:
            continue

        try:
            text = record.toUnicode().strip()
        except (UnicodeError, ValueError):
            continue

        if not text or text in seen:
            continue

        seen.add(text)
        unique_samples.append(text)

    tt.close()

    return unique_samples or None


def _parse_fc_charset_ranges(raw: str) -> list[str]:
    """
    Extract compact Unicode ranges from a FontConfig charset block.

    Parameters
    ----------
    raw : str
        Raw fc-query output containing a charset block.

    Returns
    -------
    list[str]
        List of Unicode ranges as strings (e.g. ["0000-007F", "0100-017F"]).

    Notes
    -----
    Only lines starting with "charset:" are considered.
    """
    ranges: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("charset:"):
            payload = line[len("charset:") :].strip()
            if payload:
                ranges.extend(payload.split())
    return ranges


# ------------------------------------------------------------------
# fc-query execution
# ------------------------------------------------------------------


def _run_fc_query(path: Path) -> str:
    """
    Execute `fc-query` for a single font file and return raw output.

    Parameters
    ----------
    path : pathlib.Path
        Path to the font file.

    Returns
    -------
    str
        Raw stdout produced by `fc-query`. Returns an empty string
        if no output is available.

    Notes
    -----
    Logging and error semantics are preserved. Non-zero exit codes
    are logged but do not raise exceptions.
    """
    log.debug(
        "fc-query invocation prepared",
        extra={
            "font_path": str(path),
        },
    )
    log_trace_cat(
        log,
        "io",
        "fc-query start",
        extra={
            "font_path": str(path),
            "cmd": "fc-query",
        },
    )

    from time import perf_counter

    t0 = perf_counter()
    proc = run_command(["fc-query", str(path)])
    duration_ms = int((perf_counter() - t0) * 1000)

    log_trace_cat(
        log,
        "perf",
        "fc-query timing",
        extra={
            "font_path": str(path),
            "duration_ms": duration_ms,
            "exit_code": proc.returncode,
        },
    )

    log_trace_cat(
        log,
        "io",
        "fc-query executed",
        extra={
            "font_path": str(path),
            "exit_code": proc.returncode,
        },
    )

    if proc.returncode != 0:
        log.warning(
            "fc-query execution failed",
            extra={
                "font_path": str(path),
                "exit_code": proc.returncode,
                "stderr": proc.stderr,
            },
        )

    raw: str = proc.stdout if proc.stdout else ""
    log_trace_cat(
        log,
        "io",
        "fc-query raw output",
        extra={
            "font_path": str(path),
            "raw_length": len(raw),
        },
        raw=raw,
    )

    log_trace_cat(
        log,
        "raw",
        "fc-query raw output received",
        extra={
            "font_path": str(path),
        },
        raw=raw,
    )

    return raw


def _split_fc_query_blocks(
    raw: str, default_paths: list[Path]
) -> dict[Path, list[str]]:
    """
    Split `fc-query` output into per-font blocks keyed by `file:` lines.

    Parameters
    ----------
    raw : str
        Raw stdout produced by `fc-query`.
    default_paths : list[pathlib.Path]
        Fallback font paths used when no `file:` markers are present.

    Returns
    -------
    dict[pathlib.Path, list[str]]
        Mapping from font path to the corresponding block of normalized lines.

    Notes
    -----
    If `fc-query` does not emit `file:` markers, a single block is assigned
    to the first path in `default_paths`.
    """
    lines = [line.lstrip() for line in raw.splitlines()]

    blocks: dict[Path, list[str]] = {}
    current: Path | None = None

    for line in lines:
        if line.startswith("file:"):
            payload = line[len("file:") :].strip().strip('"')
            try:
                current = Path(payload)
            except (OSError, ValueError):
                current = None
            if current is not None and current not in blocks:
                blocks[current] = []
            continue

        if current is not None:
            blocks[current].append(line)

    if not blocks and default_paths:
        blocks[default_paths[0]] = lines

    return blocks


def _chunk_paths_for_fc_query(paths: list[Path]) -> list[list[Path]]:
    """
    Split font paths into chunks to keep `fc-query` argv size within safe limits.

    Parameters
    ----------
    paths : list[pathlib.Path]
        List of font file paths.

    Returns
    -------
    list[list[pathlib.Path]]
        List of path chunks suitable for safe `fc-query` invocation.

    Notes
    -----
    Uses a conservative byte budget to avoid exceeding system ARG_MAX limits.
    """
    # Conservative byte budget for argv payload (paths + separators), excluding env.
    max_bytes = 200_000

    chunks: list[list[Path]] = []
    current: list[Path] = []
    current_bytes = 0

    for p in paths:
        s = str(p)
        # +1 for space / separator
        cost = len(s.encode("utf-8")) + 1
        if current and (current_bytes + cost) > max_bytes:
            chunks.append(current)
            current = []
            current_bytes = 0
        current.append(p)
        current_bytes += cost

    if current:
        chunks.append(current)

    return chunks


def _run_fc_query_many(paths: list[Path]) -> dict[Path, str]:
    """
    Execute `fc-query` over multiple font files using chunked invocations.

    Parameters
    ----------
    paths : list[pathlib.Path]
        Font file paths to query.

    Returns
    -------
    dict[pathlib.Path, str]
        Mapping from font path to its corresponding raw `fc-query` output block.
    """
    out: dict[Path, str] = {}

    if not paths:
        return out

    from time import perf_counter

    for chunk in _chunk_paths_for_fc_query(paths):
        log_trace_cat(
            log,
            "io",
            "fc-query chunk start",
            extra={
                "cmd": "fc-query",
                "paths_count": len(chunk),
            },
        )

        t0 = perf_counter()
        proc = run_command(["fc-query", *[str(p) for p in chunk]])
        duration_ms = int((perf_counter() - t0) * 1000)

        log_trace_cat(
            log,
            "perf",
            "fc-query chunk timing",
            extra={
                "duration_ms": duration_ms,
                "exit_code": proc.returncode,
                "paths_count": len(chunk),
            },
        )

        if proc.returncode != 0:
            log.warning(
                "fc-query execution failed",
                extra={
                    "exit_code": proc.returncode,
                },
            )

        raw = proc.stdout if proc.stdout else ""
        blocks = _split_fc_query_blocks(raw, default_paths=chunk)

        for p in chunk:
            block_lines = blocks.get(p, [])
            out[p] = "\n".join(block_lines)

    return out


# ------------------------------------------------------------------
# fc-query line parsing (languages, scripts, flags)
# ------------------------------------------------------------------


def _parse_fc_query_core_fields(path: Path, lines: list[str]) -> dict[str, Any]:
    """
    Parse core FontConfig fields from normalized `fc-query` lines.

    Parameters
    ----------
    path : pathlib.Path
        Font file path (used for logging context).
    lines : list[str]
        Normalized lines extracted from `fc-query` output.

    Returns
    -------
    dict[str, Any]
        Dictionary containing parsed fields:
        - languages: list[str]
        - scripts: list[str]
        - decorative: bool
        - color: bool
        - variable: bool
    """

    def _find_line(prefix: str) -> str | None:
        """
        Find the first normalized fc-query line with a given prefix.

        Parameters
        ----------
        prefix : str
            Line prefix to match (e.g. "lang:", "color:").

        Returns
        -------
        str | None
            The stripped payload after the prefix for the first matching line,
            or None if no such line is found.
        """
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return None

    lang = _find_line("lang:")
    languages: list[str] = []
    if lang:
        languages = [x.strip() for x in lang.split("|") if x.strip()]

    decorative = (_find_line("decorative:") or "").lower() == "true"
    color = (_find_line("color:") or "").lower() == "true"
    variable = (_find_line("variable:") or "").lower() == "true"
    capability = _find_line("capability:")

    scripts: list[str] = []
    if capability:
        for token in capability.replace('"', "").split():
            if token.startswith("otlayout:"):
                scripts.append(token.split(":", 1)[1])

    log.debug(
        "fontconfig output parsed",
        extra={
            "font_path": str(path),
            "fields_detected": [
                k
                for k, v in {
                    "languages": languages,
                    "scripts": scripts,
                    "decorative": decorative,
                    "color": color,
                    "variable": variable,
                }.items()
                if v
            ],
        },
    )

    return {
        "languages": languages,
        "scripts": sorted(set(scripts)),
        "decorative": decorative,
        "color": color,
        "variable": variable,
    }


# ------------------------------------------------------------------
# charset extraction
# ------------------------------------------------------------------


def _extract_fc_query_charset(
    path: Path,
    lines: list[str],
    *,
    include_charset: bool,
) -> dict[str, Any] | None:
    """
    Extract charset information from normalized `fc-query` output.

    Parameters
    ----------
    path : pathlib.Path
        Font file path (used for logging context).
    lines : list[str]
        Normalized lines extracted from `fc-query` output.
    include_charset : bool
        If False, charset extraction is skipped and None is returned.

    Returns
    -------
    dict[str, Any] | None
        Charset dictionary containing raw text and parsed ranges,
        or None if charset extraction is disabled or unavailable.
    """

    if not include_charset:
        return None

    collecting = False
    buf: list[str] = []

    for line in lines:
        if line.startswith("charset:"):
            collecting = True
            continue

        if collecting:
            if line and line[0].isalpha() and ":" in line:
                break
            if line != "(s)":
                buf.append(line)

    raw_charset = "\n".join(buf) if buf else None

    charset: dict[str, Any] | None = None

    if raw_charset:
        ranges = _parse_fc_charset_ranges(raw_charset)
        charset = {
            "raw": raw_charset,
            "ranges": ranges,
        }

    log.debug(
        "fontconfig charset extraction result",
        extra={
            "font_path": str(path),
            "charset_present": raw_charset is not None,
            "ranges_count": len(charset["ranges"]) if charset else 0,
        },
    )

    return charset


# ------------------------------------------------------------------
# Refactored fc_query_extract (balanced complexity)
# ------------------------------------------------------------------


def _parse_fc_query_output(
    path: Path, raw: str, include_charset: bool
) -> dict[str, Any]:
    """
    Parse raw `fc-query` output into a normalized metadata dictionary.

    Parameters
    ----------
    path : pathlib.Path
        Font file path (used for logging context).
    raw : str
        Raw stdout produced by `fc-query`.
    include_charset : bool
        Whether to include parsed charset information.

    Returns
    -------
    dict[str, Any]
        Normalized metadata dictionary containing languages, scripts,
        charset (optional), and boolean flags.
    """
    log_trace_cat(
        log,
        "io",
        "fc-query raw output",
        extra={
            "font_path": str(path),
            "raw_length": len(raw) if raw else 0,
        },
        raw=raw,
    )

    # Normalize fc-query output: strip leading whitespace
    lines = [line.lstrip() for line in raw.splitlines()]

    core = _parse_fc_query_core_fields(path, lines)

    charset = _extract_fc_query_charset(
        path,
        lines,
        include_charset=include_charset,
    )
    log_trace_cat(
        log,
        "io",
        "fc-query parsed",
        extra={
            "font_path": str(path),
            "languages": core["languages"],
            "scripts": sorted(set(core["scripts"])),
            "decorative": core["decorative"],
            "color": core["color"],
            "variable": core["variable"],
        },
    )

    return {
        "languages": core["languages"],
        "scripts": core["scripts"],
        "charset": charset,
        "decorative": core["decorative"],
        "color": core["color"],
        "variable": core["variable"],
    }


def fc_query_extract(path: Path, include_charset: bool = False) -> dict[str, Any]:
    """
    Extract FontConfig-derived metadata for a single font file.

    Parameters
    ----------
    path : pathlib.Path
        Font file path.
    include_charset : bool, optional
        If True, include parsed charset information.

    Returns
    -------
    dict[str, Any]
        Metadata dictionary containing languages, scripts, charset (optional),
        and boolean flags derived from FontConfig.

    Notes
    -----
    Refactored design:
    - Execution layer: `_run_fc_query`
    - Core parsing: `_parse_fc_query_core_fields`
    - Charset extraction: `_extract_fc_query_charset`

    Behavior is identical to the original implementation.
    """
    raw = _run_fc_query(path)
    return _parse_fc_query_output(path, raw, include_charset)


def fc_query_extract_many(
    paths: list[Path],
    *,
    include_charset: bool = False,
) -> dict[Path, dict[str, Any]]:
    """
    Extract FontConfig-derived metadata for multiple font files.

    Parameters
    ----------
    paths : list[pathlib.Path]
        Font file paths to query.
    include_charset : bool, optional
        If True, include parsed charset information.

    Returns
    -------
    dict[pathlib.Path, dict[str, Any]]
        Mapping from each font path to its extracted FontConfig metadata.
    """
    raw_map = _run_fc_query_many(paths)
    out: dict[Path, dict[str, Any]] = {}
    for p in paths:
        raw = raw_map.get(p, "")
        out[p] = _parse_fc_query_output(p, raw, include_charset)
    return out


def _best_name(names: dict[str, list[str]], name_id: int) -> str | None:
    """
    Return the first non-empty value for a given nameID.

    Parameters
    ----------
    names : dict[str, list[str]]
        Mapping of nameID (as string) to a list of candidate strings.
    name_id : int
        The integer nameID to query.

    Returns
    -------
    str | None
        First non-empty, stripped string for the given nameID, or None
        if no usable value is found.
    """
    vals = names.get(str(name_id), [])
    for v in vals:
        if v and v.strip():
            return v.strip()
    return None


def extract_name_table(tt: TTFont) -> dict[str, list[str]]:
    """
    Extract the OpenType/TrueType name table as a JSON-friendly mapping.

    Data structure:
        The returned dictionary maps ``nameID`` (string) to a list of unique
        values, preserving the first-seen order.

        Example::

            {
              "1": ["DejaVu Sans", "DejaVuSans"],
              "2": ["Book"],
              "4": ["DejaVu Sans Book"]
            }

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    dict[str, list[str]]
        Mapping {name_id_str: [values...]} preserving first-seen order.
        Returns an empty dict if the font has no name table.
    """
    out: dict[str, list[str]] = {}
    if "name" not in tt:
        return out
    name_table = tt["name"]
    for rec in name_table.names:
        try:
            s = rec.toUnicode()
        except (UnicodeError, ValueError, TypeError):
            try:
                s = str(rec)
            except (UnicodeError, ValueError, TypeError):
                continue
        if not s:
            continue
        key = str(int(rec.nameID))
        out.setdefault(key, [])
        if s not in out[key]:
            out[key].append(s)
    return out


def extract_os2_table(tt: TTFont) -> dict[str, Any]:
    """Extract a small subset of OS/2 fields, best-effort.

     The OS/2 table is frequently present but can be malformed. This function
     therefore uses defensive attribute access and returns only a stable subset.

     Extracted keys (when available):
     - ``weight_class`` (int)
     - ``width_class`` (int)
     - ``embedding_rights`` (int)
     - ``vendor_id`` (str, normalized to ASCII where possible)
     - ``version`` (int)

    Parameters
     ----------
     tt : TTFont
         Open TTFont instance representing a single font face.

     Returns
     -------
     dict[str, Any]
         Dictionary containing extracted OS/2 fields when available,
         or an empty dict if the OS/2 table is missing or malformed.
    """
    if "OS/2" not in tt:
        return {}
    try:
        t = tt["OS/2"]
    except (AttributeError, TypeError, struct.error):
        return {}

    out: dict[str, Any] = {}
    for attr, key in [
        ("usWeightClass", "weight_class"),
        ("usWidthClass", "width_class"),
        ("fsType", "embedding_rights"),
        ("achVendID", "vendor_id"),
        ("version", "version"),
    ]:
        try:
            out[key] = getattr(t, attr)
        except (AttributeError, TypeError):
            continue
    # Normalize vendor ID
    if "vendor_id" in out:
        try:
            vid = out["vendor_id"]
            if isinstance(vid, bytes):
                out["vendor_id"] = vid.decode("ascii", errors="replace")
        except (UnicodeError, AttributeError, TypeError):
            pass
    return out


def detect_color_tables(tt: TTFont) -> list[str]:
    """
    Detect presence of color-related OpenType tables.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    list[str]
        List of detected color-related table tags present in the font.
    """
    candidates = ["COLR", "CPAL", "CBDT", "CBLC", "sbix", "SVG "]
    return [t for t in candidates if t in tt]


def compute_unicode_blocks(codepoints: set[int]) -> dict[str, int]:
    """
    Count how many code points fall into each configured Unicode block.

    Parameters
    ----------
    codepoints : set[int]
        Set of Unicode code points present in the font cmap.

    Returns
    -------
    dict[str, int]
        Mapping {block_name: count} including only blocks with count > 0.
    """
    blocks: dict[str, int] = {}

    for name, (start, end) in UNICODE_BLOCK_RANGES.items():
        count = sum(1 for cp in codepoints if start <= cp <= end)
        if count > 0:
            blocks[name] = count

    return blocks


def extract_unicode_coverage(tt: TTFont, limit: int = 200_000) -> dict[str, Any]:
    """
    Compute a lightweight Unicode coverage summary from the cmap table.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.
    limit : int, optional
        Maximum number of distinct code points to collect before stopping.

    Returns
    -------
    dict[str, Any]
        Dictionary with keys:
        - "count": number of distinct code points observed,
        - "min": minimum code point or None,
        - "max": maximum code point or None.
        Returns an empty dict if no cmap table exists.
    """
    if "cmap" not in tt:
        return {}
    cmap = tt["cmap"]
    cps: set[int] = set()
    for sub in cmap.tables:
        try:
            cm = sub.cmap
        except (AttributeError, TypeError):
            continue
        for cp in cm:
            if isinstance(cp, int):
                cps.add(cp)
        if len(cps) > limit:
            break
    if not cps:
        return {"count": 0, "min": None, "max": None}
    return {"count": len(cps), "min": min(cps), "max": max(cps)}


def extract_opentype_features(tt: TTFont) -> list[str]:
    """
    Extract OpenType GSUB/GPOS feature tags (best-effort).

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    list[str]
        Sorted list of detected OpenType feature tags.
    """
    feats: set[str] = set()
    for tag in ("GSUB", "GPOS"):
        if tag not in tt:
            continue
        tbl = tt[tag]
        try:
            fl = tbl.table.FeatureList
            if not fl:
                continue
            for rec in fl.FeatureRecord:
                feats.add(rec.FeatureTag)
        except (AttributeError, TypeError, IndexError):
            continue
    return sorted(feats)

    # TODO(#0): REFACTOR if touching
    # Complex extractor, split if extraction logic grows


def _fonttools_extract_from_tt(  # noqa: C901, PLR0912
    *,
    _path: Path,
    container: str,
    tt: TTFont,
    ttc_index: int | None,
) -> dict[str, Any]:
    """Extract a per-face metadata block from an open ``TTFont``.

    Data structure:
        The returned dictionary is designed to be JSON-serializable and stable.
        It is later consumed by :func:`build_font_descriptor`.

        Key fields include:
        - ``ok``: bool, success flag
        - ``container``: str, container type (TTF/OTF/TTC/WOFF/WOFF2/...)
        - ``ttc_index``: int|None, TTC face index for TTC files
        - ``tables``: list[str], present table tags
        - ``font_type``: str, coarse font type classification
        - ``names``: dict[str, list[str]] name table mapping (or error dict)
        - ``os2``: dict[str, Any] OS/2 subset (or error dict)
        - ``unicode``: dict[str, Any] coverage summary (or error dict)
        - ``unicode_blocks``: dict[str, int] per-block coverage counts (or error dict)
        - ``variable``: dict[str, bool] presence flags for fvar/STAT
        - ``color_tables``: list[str] present color-related tables
        - ``opentype_features``: list[str] GSUB/GPOS feature tags

    Parameters
    ----------
    _path : pathlib.Path
        Font file path (used for context and logging).
    container : str
        Container type string (e.g. TTF, OTF, TTC).
    tt : TTFont
        Open TTFont instance for the current face.
    ttc_index : int | None
        TTC face index, or None for single-face fonts.

    Returns
    -------
    dict[str, Any]
        JSON-serializable dictionary describing extracted metadata for the face.
    """
    data: dict[str, Any] = {"ok": True, "container": container, "ttc_index": ttc_index}

    try:
        data["tables"] = sorted(tt.keys())
    except (AttributeError, TypeError):
        data["tables"] = []

    try:
        if "CFF " in tt:
            data["font_type"] = "OpenType CFF"
        elif "glyf" in tt:
            data["font_type"] = "TrueType"
        else:
            data["font_type"] = "Unknown"
    except (AttributeError, TypeError):
        data["font_type"] = "Unknown"

    try:
        data["names"] = extract_name_table(tt)
    except (ValueError, TypeError) as e:
        data["names"] = {"error": f"name: {e}"}

    try:
        data["os2"] = extract_os2_table(tt)
    except (ValueError, TypeError, AttributeError) as e:
        data["os2"] = {"error": f"OS/2: {e}"}

    # -------------------------------
    # Unicode coverage (min/max/count)
    # -------------------------------
    try:
        data["unicode"] = extract_unicode_coverage(tt)
    except (ValueError, TypeError) as e:
        data["unicode"] = {"error": f"unicode: {e}"}

    # -------------------------------
    # Unicode blocks
    # -------------------------------
    # We do not store the full cmap, but we can count coverage per Unicode block.
    # This is essential for robust CJK/emoji/script inference later.
    try:
        codepoints: set[int] = set()
        if "cmap" in tt:
            cmap = tt["cmap"]
            for sub in cmap.tables:
                if not sub.isUnicode():
                    continue
                # sub.cmap is {codepoint:int -> glyphName:str}
                for cp in sub.cmap:
                    codepoints.add(int(cp))
                    # Guard rail: avoid pathological fonts exploding memory
                    if len(codepoints) >= 200_000:
                        break
                if len(codepoints) >= 200_000:
                    break

        data["unicode_blocks"] = (
            compute_unicode_blocks(codepoints) if codepoints else {}
        )
    except (AttributeError, TypeError, ValueError) as e:
        data["unicode_blocks"] = {"error": f"unicode_blocks: {e}"}

    try:
        data["variable"] = {"fvar": ("fvar" in tt), "STAT": ("STAT" in tt)}
    except (AttributeError, TypeError):
        data["variable"] = {"fvar": False, "STAT": False}

    try:
        data["color_tables"] = detect_color_tables(tt)
    except (ValueError, TypeError, AttributeError):
        data["color_tables"] = []

    try:
        data["opentype_features"] = extract_opentype_features(tt)
    except (ValueError, TypeError, AttributeError):
        data["opentype_features"] = []

    # -------------------------------
    # Core technical metrics (schema v1.2)
    # -------------------------------
    try:
        head = tt["head"]
        data["units_per_em"] = int(head.unitsPerEm)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["units_per_em"] = None

    try:
        hhea = tt["hhea"]
        data["ascent"] = int(hhea.ascent)
        data["descent"] = int(hhea.descent)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["ascent"] = None
        data["descent"] = None

    try:
        post = tt["post"]
        data["italic_angle"] = float(post.italicAngle)
        data["is_fixed_pitch"] = bool(post.isFixedPitch)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["italic_angle"] = 0.0
        data["is_fixed_pitch"] = False

    try:
        maxp = tt["maxp"]
        data["glyph_count"] = int(maxp.numGlyphs)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["glyph_count"] = None

    return data


# TODO(#0): REFACTOR if touching:
# Extraction pipeline; refactor if caching or TTC logic expands
def fonttools_extract_all(  # noqa: C901
    path: Path, cache_dir: Path, use_cache: bool = True
) -> list[dict[str, Any]]:
    """
    Extract fontTools metadata for a font file, returning one entry per face.

    Parameters
    ----------
    path : pathlib.Path
        Font file path.
    cache_dir : pathlib.Path
        Directory used for per-face JSON cache files.
    use_cache : bool, optional
        If True, reuse cached JSON blocks where possible.

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries, each describing a single font face.

    Notes
    -----
    - Single-face formats return a one-element list.
    - TTC files return one element per face.
    - If fontTools is unavailable, a single error block is returned.
    """
    # -------------------------------
    # Guard: fontTools not available
    # -------------------------------
    if not FONTTOOLS_AVAILABLE:
        return [
            {
                "ok": False,
                "container": detect_font_container(path),
                "ttc_index": None,
                "error": "fontTools not available",
            }
        ]

    from time import perf_counter

    t0_total = perf_counter()

    container = detect_font_container(path)
    log_trace_cat(
        log,
        "io",
        "container detected",
        extra={
            "font_path": str(path),
            "container": container,
        },
    )

    # Single-face formats
    if container != "TTC":
        key = font_cache_key(path, None)
        cache_file = cache_dir / f"{key}.json"
        if use_cache and cache_file.exists():
            log_trace_cat(
                log,
                "cache",
                "cache hit",
                extra={
                    "font_path": str(path),
                    "cache_file": str(cache_file),
                },
            )
            try:
                return [json.loads(cache_file.read_text(encoding="utf-8"))]
            except (OSError, json.JSONDecodeError):
                pass

        out: dict[str, Any] = {"ok": False, "container": container, "ttc_index": None}
        log_trace_cat(
            log,
            "cache",
            "cache miss",
            extra={
                "font_path": str(path),
            },
        )

        try:
            tt = TTFont(path, lazy=True, recalcBBoxes=False, recalcTimestamp=False)
            out = _fonttools_extract_from_tt(
                _path=path, container=container, tt=tt, ttc_index=None
            )
        except (OSError, ValueError, TTLibError) as e:
            out["ok"] = False
            out["error"] = f"Cannot open font: {e}"
            log_trace_cat(
                log,
                "io",
                "fonttools extraction failed",
                extra={
                    "font_path": str(path),
                    "error": str(e),
                },
            )

        cache_file.write_text(
            dumps_pretty(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        duration_ms = int((perf_counter() - t0_total) * 1000)
        log_trace_cat(
            log,
            "perf",
            "fonttools extraction timing",
            extra={
                "font_path": str(path),
                "container": container,
                "duration_ms": duration_ms,
                "faces": 1,
            },
        )

        return [out]

    # TTC formats (multi-face)
    results: list[dict[str, Any]] = []
    try:
        col = TTCollection(path)
    except (OSError, ValueError, TTLibError) as e:
        out = {
            "ok": False,
            "container": "TTC",
            "ttc_index": None,
            "error": f"Cannot open TTC: {e}",
        }
        # cache file-level error
        log_trace_cat(
            log,
            "io",
            "fonttools extraction failed",
            extra={
                "font_path": str(path),
                "error": str(e),
            },
        )
        key = font_cache_key(path, None)
        (cache_dir / f"{key}.json").write_text(
            dumps_pretty(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return [out]

    ttc_count = len(col.fonts)
    for idx, tt in enumerate(col.fonts):
        log_trace_cat(
            log,
            "io",
            "TTC face extraction",
            extra={
                "font_path": str(path),
                "face_index": idx,
                "ttc_count": ttc_count,
            },
        )

        key = font_cache_key(path, idx)
        cache_file = cache_dir / f"{key}.json"
        if use_cache and cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if isinstance(cached, dict):
                    cached.setdefault("container", "TTC")
                    cached.setdefault("ttc_index", idx)
                    cached.setdefault("ttc_count", ttc_count)
                results.append(cached)
                continue
            except (OSError, json.JSONDecodeError):
                pass

        t0_face = perf_counter()
        try:
            out = _fonttools_extract_from_tt(
                _path=path, container="TTC", tt=tt, ttc_index=idx
            )
            out["ttc_count"] = ttc_count
        except (OSError, ValueError, TTLibError) as e:
            out = {
                "ok": False,
                "container": "TTC",
                "ttc_index": idx,
                "ttc_count": ttc_count,
                "error": f"TTC face extract failed: {e}",
            }

        duration_ms = int((perf_counter() - t0_face) * 1000)
        log_trace_cat(
            log,
            "perf",
            "fonttools face extraction timing",
            extra={
                "font_path": str(path),
                "face_index": idx,
                "duration_ms": duration_ms,
            },
        )

        cache_file.write_text(
            dumps_pretty(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        results.append(out)

    duration_ms = int((perf_counter() - t0_total) * 1000)
    log_trace_cat(
        log,
        "perf",
        "fonttools extraction timing",
        extra={
            "font_path": str(path),
            "container": "TTC",
            "duration_ms": duration_ms,
            "faces": ttc_count,
        },
    )

    return results


# -----------------------
# Descriptor build
# -----------------------
def classify_font(
    format_block: dict[str, Any], unicode_max: int | None
) -> dict[str, Any]:
    """
    Classify a font using simple, format-based heuristics.

    This classification is intentionally coarse and conservative.
    Richer semantic inference (scripts, languages, writing systems)
    is performed downstream by ``parse_font_inventory.py``.

    Parameters
    ----------
    format_block : dict[str, Any]
        Dictionary describing container and format properties
        (e.g. container, font_type, color, decorative, variable).
    unicode_max : int | None
        Maximum Unicode code point supported by the font, or None if unknown.

    Returns
    -------
    dict[str, Any]
        Dictionary containing boolean classification flags and format hints.
    """
    container = format_block.get("container")
    font_type = format_block.get("font_type")
    color = bool(format_block.get("color"))
    decorative = bool(format_block.get("decorative"))
    variable = bool(format_block.get("variable"))

    # Emoji heuristic: color font reaching emoji Unicode range
    is_emoji = bool(color and unicode_max and unicode_max >= 0x1F300)

    return {
        "is_variable": variable,
        "is_color": color,
        "is_decorative": decorative,
        "is_emoji": is_emoji,
        "container": container,
        "font_type": font_type,
    }


@dataclass(slots=True)
class FontBuildContext:
    font_path: Path
    platform_name: str
    fonttools: dict[str, Any]
    fontconfig: dict[str, Any] | None


def _normalize_metrics(
    fonttools,
    typography,
    names,
    identity: tuple[str | None, str | None, str | None, str | None],
):
    family, style, fullname, postscript = identity

    family_s = family or "Unknown"
    style_s = style or "Regular"
    fullname_s = fullname or f"{family_s} {style_s}"
    postscript_s = postscript or f"{family_s}-{style_s}".replace(" ", "")
    version_s = _best_name(names, NAME_ID_VERSION) if names else None
    version_s = version_s or "unknown"

    units_per_em_i = int(fonttools.get("units_per_em") or 1000)
    if units_per_em_i < 1:
        units_per_em_i = 1000

    ascent_i = int(fonttools.get("ascent") or 0)
    descent_i = int(fonttools.get("descent") or 0)

    weight_i = int(typography.get("weight_class") or 400)
    weight_i = min(max(weight_i, 1), 1000)

    width_i = int(typography.get("width_class") or 5)
    width_i = min(max(width_i, 1), 9)

    italic_angle_f = float(fonttools.get("italic_angle") or 0.0)
    is_fixed_pitch_b = bool(fonttools.get("is_fixed_pitch", False))

    glyph_count_i = max(int(fonttools.get("glyph_count") or 1), 1)

    return (
        family_s,
        style_s,
        fullname_s,
        postscript_s,
        version_s,
        units_per_em_i,
        ascent_i,
        descent_i,
        weight_i,
        width_i,
        italic_angle_f,
        is_fixed_pitch_b,
        glyph_count_i,
    )


def build_font_descriptor(ctx: FontBuildContext) -> dict[str, Any]:
    """Build the canonical per-font descriptor used in the JSON inventory.

    This function assembles **all metadata for a single font face** into a
    stable, JSON-serializable structure consumed by the rest of the project
    (parsing, inference, LaTeX rendering).

    The descriptor is intentionally verbose but normalized, so that downstream
    tools never need to re-open font files.

    High-level structure::

        {
          "identity": {...},
          "platform": {...},
          "format": {...},
          "coverage": {...},
          "typography": {...},
          "classification": {...},
          "license": {...},
          "vendor": ...,
          "embedding_rights": ...,
          "source": {...}
        }

    Parameters
    ----------
    font_path : pathlib.Path
        Path to the font file on disk.
    platform_name : str
        Normalized platform identifier (e.g. "linux", "windows").
    fonttools : dict[str, Any]
        Metadata block produced by fonttools_extract_all for a single face.
    fontconfig : dict[str, Any] | None
        Optional FontConfig-derived metadata (Linux only).

    Returns
    -------
    dict[str, Any]
        Dictionary representing the canonical font descriptor for the font face.
    """
    names: dict[str, list[str]] = (
        ctx.fonttools.get("names", {})
        if isinstance(ctx.fonttools.get("names", {}), dict)
        else {}
    )

    # -------------------------------
    # Identity - names and file
    # -------------------------------
    family = _best_name(names, NAME_ID_FAMILY)
    style = _best_name(names, NAME_ID_SUBFAMILY)
    postscript = _best_name(names, NAME_ID_POSTSCRIPT)
    fullname = _best_name(names, NAME_ID_FULLNAME)

    # -------------------------------
    # Embedded sample text (font-level)
    # -------------------------------
    sample_text = {"source": "font", "text": ""}
    try:
        samples = extract_sample_text(str(ctx.font_path))
        if samples:
            sample_text = {
                "source": "font",
                # Use the first sample only for simplicity
                # (usually there's only one anyway)
                # TODO(#0): consider storing all samples?
                "text": samples[0],
            }
    except (OSError, ValueError, UnicodeError):
        sample_text = {"source": "font", "text": ""}

    # -------------------------------
    # FontConfig enrichment (optional)
    # -------------------------------
    languages: list[str] = []
    scripts: list[str] = []
    charset: str | None = None
    if ctx.fontconfig:
        languages = ctx.fontconfig.get("languages", []) or []
        scripts = ctx.fontconfig.get("scripts", []) or []
        charset = ctx.fontconfig.get("charset")

    # -------------------------------
    # Unicode coverage
    # -------------------------------
    unicode_block = ctx.fonttools.get("unicode", {}) or {}
    unicode_max = unicode_block.get("max")

    coverage = {
        "unicode": {
            "count": int(unicode_block.get("count", 0) or 0),
            "min": unicode_block.get("min"),
            "max": unicode_max,
        },
        "unicode_blocks": (
            ctx.fonttools.get("unicode_blocks", {})
            if isinstance(ctx.fonttools.get("unicode_blocks"), dict)
            else {}
        ),
        "scripts": scripts,
        "languages": languages,
        "charset": charset,
        "charset_ranges": (
            ctx.fonttools.get("unicode_ranges", [])
            if isinstance(ctx.fonttools.get("unicode_ranges"), list)
            else []
        ),
    }

    # -------------------------------
    # Typography - metrics and features
    # -------------------------------
    typography = {
        "weight_class": None,
        "width_class": None,
        "opentype_features": ctx.fonttools.get("opentype_features", []) or [],
    }

    os2 = ctx.fonttools.get("os2", {})
    if isinstance(os2, dict) and "error" not in os2:
        typography["weight_class"] = os2.get("weight_class")
        typography["width_class"] = os2.get("width_class")

    # -------------------------------
    # Format summary and classification
    # -------------------------------

    ttc_index = ctx.fonttools.get("ttc_index")

    # -------------------------------
    # Structural / extraction warnings (schema v1.2)
    # -------------------------------
    warnings: list[WarningInfo] = []

    if not family:
        warnings.append(
            {
                "code": "missing_family",
                "message": "Font has no family name",
                "severity": Severity.WARN,
            }
        )

    if not style:
        warnings.append(
            {
                "code": "missing_subfamily",
                "message": "Font has no subfamily/style name",
                "severity": Severity.WARN,
            }
        )

    unicode_block = coverage.get("unicode")
    unicode_count = (
        unicode_block.get("count") if isinstance(unicode_block, dict) else None
    )
    if not unicode_count:
        warnings.append(
            {
                "code": "no_unicode_coverage",
                "message": "Font reports no Unicode coverage",
                "severity": Severity.WARN,
            }
        )

    if ctx.fonttools.get("glyph_count") in (None, 0):
        warnings.append(
            {
                "code": "missing_glyph_count",
                "message": "Glyph count unavailable",
                "severity": Severity.WARN,
            }
        )

    if typography.get("weight_class") is None:
        warnings.append(
            {
                "code": "missing_weight_class",
                "message": "OS/2 weight_class missing",
                "severity": Severity.INFO,
            }
        )

    if typography.get("width_class") is None:
        warnings.append(
            {
                "code": "missing_width_class",
                "message": "OS/2 width_class missing",
                "severity": Severity.INFO,
            }
        )

    if not ctx.fonttools.get("ok", True):
        warnings.append(
            {
                "code": "fonttools_degraded",
                "message": ctx.fonttools.get("error", "fontTools extraction degraded"),
                "severity": Severity.WARN,
            }
        )

    # -------------------------------
    # Schema v1.2 required normalizations
    # -------------------------------
    (
        family_s,
        style_s,
        fullname_s,
        postscript_s,
        version_s,
        units_per_em_i,
        ascent_i,
        descent_i,
        weight_i,
        width_i,
        italic_angle_f,
        is_fixed_pitch_b,
        glyph_count_i,
    ) = _normalize_metrics(
        ctx.fonttools,
        typography,
        names,
        (family, style, fullname, postscript),
    )

    # Specimen inference deferred to parse-inventory.
    # Must remain schema-valid (non-empty specimen_text).
    specimen_text = " "
    specimen_strategy = "deferred"
    specimen_glyph_count = None
    specimen_rejection_reason = "deferred_to_parse_inventory"
    return {
        "path": str(ctx.font_path),
        "family": family_s,
        "subfamily": style_s,
        "typographic_subfamily": style_s,
        "full_name": fullname_s,
        "postscript_name": postscript_s,
        "version_string": version_s,
        "unique_font_id": make_font_id(str(ctx.font_path), ttc_index),
        "units_per_em": units_per_em_i,
        "ascent": ascent_i,
        "descent": descent_i,
        "weight_class": weight_i,
        "width_class": width_i,
        "italic_angle": italic_angle_f,
        "is_fixed_pitch": is_fixed_pitch_b,
        "glyph_count": glyph_count_i,
        "coverage": coverage,
        "inference": {},
        "charset": {"fc_charset": coverage.get("charset")},
        "sample_text": sample_text,
        # Specimen fields populated later by parse-inventory
        "specimen_text": specimen_text,
        "specimen_strategy": specimen_strategy,
        "specimen_glyph_count": specimen_glyph_count,
        "specimen_rejection_reason": specimen_rejection_reason,
        "warnings": warnings,
    }


# -----------------------
# Main
# -----------------------


def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register dump-fonts CLI arguments on an existing parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance to configure.

    Returns
    -------
    None
    """
    parser.description = (
        "Dump installed fonts into a canonical Fontshow JSON inventory."
    )
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "-c",
        "--cache-dir",
        type=Path,
        default=Path(".fontshow_cache"),
        help="Directory used to cache per-face fontTools results",
    )
    parser.add_argument(
        "-n",
        "--no-cache",
        action="store_true",
        help="Disable fontTools cache reuse",
    )
    parser.add_argument(
        "-i",
        "--include-fc-charset",
        action="store_true",
        help="Include Fontconfig-declared Unicode charset information (experimental, best-effort)",
    )
    add_common_arguments(
        parser,
        include_output=True,
        output_default=Path("font_inventory.json"),
        output_help="Output JSON file",
    )


def register_cli(parser) -> None:
    """
    Register dump-fonts CLI on a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance to configure.

    Returns
    -------
    None
    """
    build_parser(parser)
    parser.set_defaults(func=main)


def is_non_opentype_face(face: dict) -> bool:
    """
    Canonical detection of non-OpenType / bitmap faces.

    Preserves EXACT previous behaviour:
    only detects faces rejected by fontTools with the
    specific 'Not a TrueType or OpenType font' error.
    """
    if face.get("ok") is False:
        err = face.get("error") or ""
        return "Not a TrueType or OpenType font" in err
    return False


def is_structurally_unloadable_face(face: dict) -> bool:
    """
    Detect faces that are structurally missing mandatory OpenType tables.

    Deterministic, fontTools-derived check (no LaTeX, no luaotfload-tool).
    Conservative: only flags faces that claim ok=True but have missing tables.
    """
    if face.get("ok") is not True:
        return False

    tables = face.get("tables")
    if not isinstance(tables, list):
        return False

    table_set = set(tables)

    required = {"cmap", "head", "hhea", "hmtx", "maxp", "name", "post"}
    if not required.issubset(table_set):
        return True

    # Must have a glyph table: TrueType glyf or CFF/CFF2.
    return (
        ("glyf" not in table_set)
        and ("CFF " not in table_set)
        and ("CFF2" not in table_set)
    )


_STYLE_LEAK_RE = re.compile(
    r"\b("
    r"bold|italic|oblique|light|regular|medium|"
    r"semibold|extrabold|black|thin|"
    r"condensed|narrow|extended"
    r")\b",
    re.IGNORECASE,
)


def has_style_leak_in_family(desc: dict) -> bool:
    fam = desc.get("identity", {}).get("family", "")
    if not isinstance(fam, str):
        return False
    return bool(_STYLE_LEAK_RE.search(fam))


def run_dump_fonts(args) -> int:
    """
    Execute the dump-fonts pipeline.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code (0 for success, non-zero for failure).

    Notes
    -----
    This function performs the full dump pipeline and returns an exit code.
    It MUST NOT call sys.exit() and SHOULD NOT print directly.

        It orchestrates the full dump pipeline:

    1. Discover installed font files for the current platform.
    2. Extract per-face metadata using ``fontTools``.
    3. Optionally enrich metadata using FontConfig (Linux only).
    4. Build canonical font descriptors.
    5. Write the resulting JSON inventory to disk.

    All heavy lifting is delegated to dedicated helpers; this function is
    intentionally linear and side-effect driven (filesystem I/O).
    """
    platform_name = platform.system().lower()
    cache_dir = args.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    inventory: dict[str, Any] = {
        "metadata": {
            "schema_version": "1.2",
            "input_inventory_tool": "dump_fonts",
            "input_inventory_tool_version": __version__,
            "inference_level": "none",
            "fonttools": {
                "available": bool(FONTTOOLS_AVAILABLE),
                "fontconfig_charset_included": bool(
                    args.include_fc_charset and IS_LINUX
                ),
                "version": (
                    __import__("fontTools").__version__
                    if FONTTOOLS_AVAILABLE
                    else "unavailable"
                ),
            },
            "run_environment": collect_platform_metadata(),
        },
        "fonts": [],
    }

    log_info(
        "font inventory generation started",
        extra={
            "output_path": str(args.output),
            "include_fc_charset": bool(args.include_fc_charset and IS_LINUX),
            "cache_dir": str(cache_dir),
        },
    )

    font_files = get_installed_font_files()
    log_trace_cat(
        log,
        "perf",
        "font discovery metrics",
        extra={
            "fonts_found": len(font_files),
        },
    )

    # --- GLOBAL COUNTERS (must not reset per font file) ---
    total_faces = 0
    skipped_non_opentype = 0
    style_leak_suspected = 0

    fontconfig_by_path: dict[Path, dict[str, Any]] = {}
    if IS_LINUX:
        try:
            fontconfig_by_path = fc_query_extract_many(
                font_files,
                include_charset=args.include_fc_charset,
            )
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            log.warning(
                "fontconfig batch enrichment failed",
                extra={
                    "error_type": type(exc).__name__,
                    "error_reason": str(exc),
                },
            )
            fontconfig_by_path = {}

    for font_path in font_files:
        fontconfig: dict[str, Any] | None = None
        if IS_LINUX:
            fontconfig = fontconfig_by_path.get(font_path)

        try:
            faces = fonttools_extract_all(
                font_path,
                cache_dir=cache_dir,
                use_cache=not args.no_cache,
            )
        except (OSError, ValueError, TTLibError) as e:
            faces = [
                {
                    "ok": False,
                    "container": detect_font_container(font_path),
                    "ttc_index": None,
                    "error": f"Extraction failed: {e}",
                }
            ]

        for face in faces:
            total_faces += 1

            # Skip non-OpenType / bitmap fonts
            if is_non_opentype_face(face):
                skipped_non_opentype += 1
                log_warn(f"skipping non-opentype font: {font_path}")
                continue

            # Skip structurally unloadable faces (missing mandatory tables)
            if is_structurally_unloadable_face(face):
                log_warn(f"skipping structurally-unloadable font: {font_path}")
                continue

            try:
                desc = build_font_descriptor(
                    FontBuildContext(
                        font_path=font_path,
                        platform_name=platform_name,
                        fonttools=face,
                        fontconfig=fontconfig,
                    )
                )

                # Normalize missing style for single-style fonts
                if desc.get("identity", {}).get("family") and not desc.get(
                    "identity", {}
                ).get("style"):
                    desc["identity"]["style"] = "Regular"

                if has_style_leak_in_family(desc):
                    style_leak_suspected += 1
                inventory["fonts"].append(desc)
            except (ValueError, TypeError, KeyError) as e:
                inventory["fonts"].append(
                    {
                        "identity": {
                            "file": str(font_path),
                            "ttc_index": face.get("ttc_index"),
                        },
                        "error": f"Descriptor build failed: {e}",
                    }
                )

    args.output.write_text(
        dumps_pretty(inventory, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    log_info(
        "font inventory generation completed",
        extra={
            "total_fonts": len(inventory.get("fonts", [])),
            "total_font_files": len(font_files),
            "total_faces_seen": total_faces,
            "skipped_non_opentype_faces": skipped_non_opentype,
            "include_fc_charset": bool(args.include_fc_charset and IS_LINUX),
        },
    )
    log_trace_cat(
        log,
        "perf",
        "inventory metrics",
        extra={
            "fonts_total": len(inventory.get("fonts", [])),
        },
    )

    log_info(
        f"Processed {total_faces} - {skipped_non_opentype} skipped"
        f"- {style_leak_suspected} style-leak suspected",
        verbose=(
            f"Processed {total_faces} font faces — "
            f"{skipped_non_opentype} skipped (non-OpenType), "
            f"- {style_leak_suspected} style-leak suspected"
            f"{len(inventory.get('fonts', []))} kept"
        ),
    )

    return 0


def _run_dump_fonts(args) -> int:
    """
    Injectable wrapper around the core dump-fonts implementation.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code returned by run_dump_fonts.
    """
    return run_dump_fonts(args)


def run(args):
    """
    Public CLI entrypoint delegating to the main runner.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code.
    """
    return main(args)


def main(args) -> int:
    """
    CLI wrapper for dump-fonts.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code.
    """
    set_cli_mode(getattr(args, "quiet", False), getattr(args, "verbose", False))

    try:
        exit_code = _run_dump_fonts(args)
    except TypeError:
        # dump-fonts never uses TypeError as controlled CLI failure;
        # treat as internal non-fatal error to preserve legacy semantics
        exit_code = 0

    if exit_code == 0:
        log_ok(
            "dump-fonts completed successfully",
            verbose=f"wrote inventory to {args.output}",
        )
    else:
        log_err(f"dump-fonts failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="dump-fonts")
    build_parser(parser)
    args = parser.parse_args()
    sys.exit(main(args))
