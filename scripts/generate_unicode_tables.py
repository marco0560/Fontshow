#!/usr/bin/env python3
"""
Fontshow — generate_unicode_tables.py
====================================

Deterministically generate Python tables from vendored Unicode Character
Database (UCD) files.

Inputs (vendored, pinned by version):
- fontshow/data/unicode/Blocks-<VERSION>.txt
- fontshow/data/unicode/Scripts-<VERSION>.txt

Outputs (generated, committed in a later step):
- fontshow/unicode_tables.py

Notes
-----
- This script is intentionally standalone (stdlib only).
- It does not modify any runtime behavior unless the generated module is later
  imported by production code.
- Script keys produced are *Unicode Script property values* (e.g. "Latin",
  "Hebrew") normalized to lowercase (e.g. "latin", "hebrew") for now.
  In a later step we will map/normalize to ISO-15924 codes where needed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

# ISO15924 lines are semicolon-separated; parsing is done via split()
_ISO15924_LINE_RE = re.compile(r"^([A-Za-z]{4});")

# ------------------------------------------------------------------
# Unicode Script property → ISO15924 naming normalization
# (authoritative mismatches between UCD Scripts.txt and ISO registry)
# ------------------------------------------------------------------
_UNICODE_SCRIPT_ALIASES: dict[str, str] = {
    "Han": "Hani",
    "Hangul": "Hang",
    "Devanagari": "Deva",
    "Ethiopic": "Ethi",
}

# ------------------------------------------------------------------
# Unicode scripts that are NOT writing systems
# (derived ontology, exported to generated tables)
# ------------------------------------------------------------------

_NON_WRITING_UNICODE_SCRIPTS: frozenset[str] = frozenset(
    {
        "Common",
        "Inherited",
        "Unknown",
        "Symbols",
    }
)

_BLOCKS_LINE_RE = re.compile(
    r"^\s*([0-9A-Fa-f]{4,6})\.\.([0-9A-Fa-f]{4,6})\s*;\s*(.+?)\s*$"
)
_SCRIPTS_LINE_RE = re.compile(
    r"^\s*([0-9A-Fa-f]{4,6})(?:\.\.([0-9A-Fa-f]{4,6}))?\s*;\s*([A-Za-z_]+)\s*$"
)


def _parse_ucd_blocks(blocks_path: Path) -> dict[str, tuple[int, int]]:
    """
    Parse UCD Blocks.txt.

    Returns:
        Mapping block name -> (start, end) inclusive.
    """
    out: dict[str, tuple[int, int]] = {}
    for raw in blocks_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _BLOCKS_LINE_RE.match(line)
        if not m:
            msg = f"Unrecognized Blocks.txt line: {raw!r}"
            raise ValueError(msg)
        start_hex, end_hex, name = m.groups()
        start = int(start_hex, 16)
        end = int(end_hex, 16)
        if start > end:
            msg = f"Invalid range in Blocks.txt line: {raw!r}"
            raise ValueError(msg)
        out[name] = (start, end)
    return out


def _parse_ucd_scripts(scripts_path: Path) -> list[tuple[int, int, str]]:
    """
    Parse UCD Scripts.txt.

    Returns:
        List of (start, end, script_property) inclusive.
    """
    out: list[tuple[int, int, str]] = []
    for raw in scripts_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Strip trailing comments, if any.
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = _SCRIPTS_LINE_RE.match(line)
        if not m:
            msg = f"Unrecognized Scripts.txt line: {raw!r}"
            raise ValueError(msg)
        start_hex, end_hex_opt, script = m.groups()
        start = int(start_hex, 16)
        end = int(end_hex_opt, 16) if end_hex_opt else start
        if start > end:
            msg = f"Invalid range in Scripts.txt line: {raw!r}"
            raise ValueError(msg)
        out.append((start, end, script))
    return out


def _parse_iso15924_registry(path: Path) -> dict[str, str]:
    """
    Parse iso15924.txt registry.

    Returns:
        Mapping Unicode Script name -> ISO15924 lowercase code.

    Example:
        "Latin" -> "latn"
        "Hebrew" -> "hebr"
    """
    mapping: dict[str, str] = {}

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if not _ISO15924_LINE_RE.match(line):
            continue

        parts = [p.strip() for p in line.split(";")]

        # ISO15924 format:
        # 0: code
        # 1: numeric
        # 2: English name (long description)
        # 3: French name
        # 4: Unicode Script property name  ← WE NEED THIS
        if len(parts) < 5:
            continue

        code = parts[0]
        unicode_script_name = parts[4]

        mapping[unicode_script_name] = code.lower()
    return mapping


def _merge_contiguous_ranges(
    ranges: Iterable[tuple[int, int]],
) -> list[tuple[int, int]]:
    """
    Merge overlapping or contiguous inclusive ranges.
    Input must be (start, end) inclusive.
    """
    sorted_ranges = sorted(ranges, key=lambda r: (r[0], r[1]))
    if not sorted_ranges:
        return []

    merged: list[tuple[int, int]] = [sorted_ranges[0]]
    for start, end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _aggregate_scripts_to_ranges(
    script_spans: list[tuple[int, int, str]],
    iso_map: dict[str, str],
) -> dict[str, list[tuple[int, int]]]:
    """
    Convert per-span script assignments into merged contiguous ranges per script key.

    Keys are normalized to lowercase for now.
    """
    buckets: dict[str, list[tuple[int, int]]] = {}
    non_writing_scripts: set[str] = set()

    for start, end, script in script_spans:
        iso_code = iso_map.get(script)

        if script in _NON_WRITING_UNICODE_SCRIPTS and iso_code is not None:
            non_writing_scripts.add(iso_code)

        if iso_code is None:
            alias = _UNICODE_SCRIPT_ALIASES.get(script)
            if alias is not None:
                iso_code = alias.lower()

        if iso_code is None:
            # Skip scripts not registered in ISO15924
            continue

        buckets.setdefault(iso_code, []).append((start, end))

    out: dict[str, list[tuple[int, int]]] = {}
    for key, ranges in buckets.items():
        out[key] = _merge_contiguous_ranges(ranges)

    # Deterministic order: by key
    script_ranges_sorted = dict(sorted(out.items(), key=lambda kv: kv[0]))

    return script_ranges_sorted, frozenset(sorted(non_writing_scripts))


def _format_py_dict_block_ranges(block_ranges: dict[str, tuple[int, int]]) -> str:
    lines: list[str] = []
    lines.append("UNICODE_BLOCK_RANGES: dict[str, tuple[int, int]] = {")
    for name in sorted(block_ranges.keys()):
        start, end = block_ranges[name]
        lines.append(f"    {name!r}: (0x{start:04X}, 0x{end:04X}),")
    lines.append("}")
    return "\n".join(lines)


def _format_py_dict_script_ranges(
    script_ranges: dict[str, list[tuple[int, int]]],
) -> str:
    lines: list[str] = []
    lines.append("UNICODE_SCRIPT_RANGES: dict[str, list[tuple[int, int]]] = {")
    for script in sorted(script_ranges.keys()):
        lines.append(f"    {script!r}: [")
        for start, end in script_ranges[script]:
            lines.append(f"        (0x{start:04X}, 0x{end:04X}),")
        lines.append("    ],")
    lines.append("}")
    return "\n".join(lines)


def _format_block_ranges_section(
    block_ranges: dict[str, tuple[int, int]],
) -> str:
    header = """# ------------------------------------------------------------------
# Unicode block ranges (authoritative ontology)
#
# NOTE:
# This table may not be directly consumed by runtime code.
# It represents the frozen Unicode ontology used to derive
# other structures (e.g. UNICODE_BLOCK_SIZES) and is kept
# intentionally for determinism, auditability, and future
# inference/diagnostic features.
# ------------------------------------------------------------------"""
    return header + "\n" + _format_py_dict_block_ranges(block_ranges)


def _format_py_dict_block_sizes(
    block_ranges: dict[str, tuple[int, int]],
) -> str:
    lines: list[str] = []
    lines.append("UNICODE_BLOCK_SIZES: dict[str, int] = {")
    for name in sorted(block_ranges.keys()):
        start, end = block_ranges[name]
        size = end - start + 1
        lines.append(f"    {name!r}: {size},")
    lines.append("}")
    return "\n".join(lines)


def _generate_module_text(
    *,
    unicode_version: str,
    sources: tuple[Path, Path, Path],
    block_ranges: dict[str, tuple[int, int]],
    script_ranges: dict[str, list[tuple[int, int]]],
    non_writing_scripts: frozenset[str],
) -> str:
    blocks_path, scripts_path, iso_path = sources
    now = _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"""# AUTO-GENERATED FILE — DO NOT EDIT
# Generated by: scripts/generate_unicode_tables.py
# Generated at: {now}
# Unicode version: {unicode_version}
# Sources:
#   - {blocks_path.as_posix()}
#   - {scripts_path.as_posix()}
#   - {iso_path.as_posix()}
#
# This module provides Unicode-derived tables for Fontshow.
"""
    parts = [
        header.rstrip(),
        "",
        "from __future__ import annotations",
        "",
        _format_block_ranges_section(block_ranges),
        "",
        _format_py_dict_block_sizes(block_ranges),
        "",
        _format_py_dict_script_ranges(script_ranges),
        "",
        "NON_WRITING_SCRIPTS: frozenset[str] = frozenset({",
        *[f"    {code!r}," for code in sorted(non_writing_scripts)],
        "})",
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Fontshow Unicode tables from vendored UCD files."
    )
    parser.add_argument(
        "--unicode-version",
        default="17.0.0",
        help="Unicode version string used for provenance comments (default: 17.0.0).",
    )
    parser.add_argument(
        "--ucd-dir",
        default="fontshow/data/unicode",
        help="Directory containing vendored UCD files (default: fontshow/data/unicode).",
    )
    parser.add_argument(
        "--blocks-file",
        default=None,
        help="Override Blocks file name (default: Blocks-<version>.txt).",
    )
    parser.add_argument(
        "--scripts-file",
        default=None,
        help="Override Scripts file name (default: Scripts-<version>.txt).",
    )
    parser.add_argument(
        "--out",
        default="fontshow/unicode_tables.py",
        help="Output module path (default: fontshow/unicode_tables.py).",
    )
    parser.add_argument(
        "--iso-file",
        default="fontshow/data/iso/iso15924-2024.txt",
        help="ISO15924 registry snapshot.",
    )

    args = parser.parse_args()

    ucd_dir = Path(args.ucd_dir)
    blocks_name = args.blocks_file or f"Blocks-{args.unicode_version}.txt"
    scripts_name = args.scripts_file or f"Scripts-{args.unicode_version}.txt"

    blocks_path = ucd_dir / blocks_name
    scripts_path = ucd_dir / scripts_name

    if not blocks_path.exists():
        msg = f"Missing Blocks file: {blocks_path}"
        raise SystemExit(msg)
    if not scripts_path.exists():
        msg = f"Missing Scripts file: {scripts_path}"
        raise SystemExit(msg)

    iso_path = Path(args.iso_file)

    if not iso_path.exists():
        msg = f"Missing ISO15924 registry: {iso_path}"
        raise SystemExit(msg)

    iso_map = _parse_iso15924_registry(iso_path)

    block_ranges = _parse_ucd_blocks(blocks_path)
    script_spans = _parse_ucd_scripts(scripts_path)
    script_ranges, non_writing_scripts = _aggregate_scripts_to_ranges(
        script_spans, iso_map
    )

    out_path = Path(args.out)
    module_text = _generate_module_text(
        unicode_version=args.unicode_version,
        sources=(blocks_path, scripts_path, iso_path),
        block_ranges=block_ranges,
        script_ranges=script_ranges,
        non_writing_scripts=non_writing_scripts,
    )

    out_path.write_text(module_text, encoding="utf-8")
    print(f"Wrote {out_path} ({len(module_text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
