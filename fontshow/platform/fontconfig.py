"""
Fontshow – platform.fontconfig
==============================

Fontconfig integration utilities used by the dump-fonts pipeline.

This module isolates all interaction with the external ``fc-query`` tool
provided by Fontconfig. Its responsibilities include executing the
command-line tool, decoding its structured output, and extracting
character set coverage and basic metadata for font files.

Separating this logic from the pipeline layer ensures that platform
integration code remains confined to the ``platform`` package, while
higher-level modules operate on normalized data structures.

Responsibilities
----------------
• Invoke the ``fc-query`` executable
• Batch font file paths to avoid command-line limits
• Parse fc-query output blocks
• Decode fontconfig charset bitmap information
• Extract core metadata fields reported by fontconfig

Design principles
-----------------
• No dependency on pipeline entrypoints
• No dependency on catalog or LaTeX layers
• Deterministic parsing of fc-query output
• Pure platform integration: no inventory object construction

Typical workflow
----------------
The dump-fonts pipeline calls this module to obtain preliminary font
metadata and character set coverage using fontconfig. The resulting
data is later enriched with FontTools-based extraction and inventory
analysis.

External dependency
-------------------
Fontconfig must be available on the host system and the ``fc-query``
executable must be discoverable in ``PATH``.
"""

from pathlib import Path
from typing import Any

from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.inventory.utils import run_command


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
