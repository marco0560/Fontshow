#!/usr/bin/env python3
"""
Generate Unicode-derived Python tables.

This maintenance script reads vendored Unicode Character Database inputs
and deterministically produces Python source text for derived tables used
by Fontshow's Unicode and script-processing infrastructure.

Responsibilities
----------------
- Parse vendored Unicode block and script registry inputs.
- Normalize and aggregate Unicode script metadata into deterministic
  Python table representations.
- Generate source text for committed Unicode support tables.

Design principles
-----------------
Unicode table generation must be reproducible, standalone, and based only
on vendored authoritative inputs. The script avoids runtime side effects
and isolates table-generation logic from the production pipeline so that
derived data can be regenerated deterministically when upstream Unicode
data changes.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a
code-generation utility for the Unicode constants and ontology
infrastructure used by Fontshow.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class UnicodeTablesData:
    """
    Container for Unicode-derived data used to generate ontology tables.

    This structure aggregates the normalized information extracted from
    Unicode source files before it is rendered into the generated Python
    module.

    Attributes
    ----------
    block_ranges : dict[str, tuple[int, int]]
        Mapping of Unicode block names to their inclusive codepoint ranges
        ``(start, end)``.

    script_ranges : dict[str, list[tuple[int, int]]]
        Mapping of script identifiers to lists of inclusive Unicode ranges
        describing where characters of that script occur.

    non_writing_scripts : frozenset[str]
        Set of script identifiers representing scripts that are considered
        non-writing (for example symbols or control-related scripts).
    """

    block_ranges: dict[str, tuple[int, int]]
    script_ranges: dict[str, list[tuple[int, int]]]
    non_writing_scripts: frozenset[str]


@dataclass(frozen=True)
class GeneratorOptions:
    """
    Options controlling the structure of the generated Unicode tables.

    Attributes
    ----------
    script_keys : {"tag", "iso"}
        Determines the type used as keys for script-related tables.

        - ``"tag"`` produces tables keyed by plain script tags (``str``).
        - ``"iso"`` produces tables keyed by :class:`ScriptISO` objects.
    """

    script_keys: Literal["tag", "iso"]


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
    Parse the Unicode Character Database ``Blocks.txt`` file.

    Parameters
    ----------
    blocks_path : pathlib.Path
        Path to the ``Blocks.txt`` file.

    Returns
    -------
    dict[str, tuple[int, int]]
        Mapping from block name to inclusive Unicode codepoint range
        ``(start, end)``.

    Raises
    ------
    ValueError
        Raised if a line in the file does not match the expected format
        or if a parsed range is invalid.
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
    Parse the Unicode Character Database ``Scripts.txt`` file.

    Parameters
    ----------
    scripts_path : pathlib.Path
        Path to the ``Scripts.txt`` file.

    Returns
    -------
    list[tuple[int, int, str]]
        List of tuples ``(start, end, script_property)`` describing
        inclusive Unicode codepoint ranges and their associated script.

    Raises
    ------
    ValueError
        Raised if a line does not match the expected format or if an
        invalid range is encountered.
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
    Parse the ISO 15924 registry snapshot.

    Parameters
    ----------
    path : pathlib.Path
        Path to the ISO15924 registry file.

    Returns
    -------
    dict[str, str]
        Mapping from Unicode script property name to ISO15924 code
        (lowercase).

    Examples
    --------
    ``"Latin" -> "latn"``
    ``"Hebrew" -> "hebr"``
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

    Parameters
    ----------
    ranges : Iterable[tuple[int, int]]
        Iterable of inclusive codepoint ranges ``(start, end)``.

    Returns
    -------
    list[tuple[int, int]]
        List of merged inclusive ranges with overlaps and adjacent
        intervals collapsed.

    Notes
    -----
    The input ranges are first sorted by start and end positions to
    ensure deterministic merging.
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
) -> tuple[dict[str, list[tuple[int, int]]], frozenset[str]]:
    """
    Aggregate script spans into merged contiguous ranges per ISO script code.

    Parameters
    ----------
    script_spans : list[tuple[int, int, str]]
        List of tuples ``(start, end, script_property)`` describing
        inclusive Unicode codepoint ranges associated with script
        properties from ``Scripts.txt``.
    iso_map : dict[str, str]
        Mapping from Unicode script property names to ISO15924 script
        codes (lowercase).

    Returns
    -------
    tuple[dict[str, list[tuple[int, int]]], frozenset[str]]
        Two values:

        - Mapping from ISO15924 script code to merged contiguous
          codepoint ranges.
        - Frozen set of ISO15924 codes representing non-writing scripts.

    Notes
    -----
    Scripts not present in the ISO15924 registry are ignored.
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
    """
    Format Unicode block ranges as a Python dictionary literal.

    Parameters
    ----------
    block_ranges : dict[str, tuple[int, int]]
        Mapping of Unicode block names to inclusive codepoint ranges
        represented as ``(start, end)``.

    Returns
    -------
    str
        A string containing Python source code that defines the
        ``UNICODE_BLOCK_RANGES`` dictionary with deterministically
        ordered entries.
    """
    lines: list[str] = []
    lines.append("UNICODE_BLOCK_RANGES: dict[str, tuple[int, int]] = {")
    for name in sorted(block_ranges.keys()):
        start, end = block_ranges[name]
        lines.append(f"    {name!r}: (0x{start:04X}, 0x{end:04X}),")
    lines.append("}")
    return "\n".join(lines)


def _format_py_dict_script_ranges(
    script_ranges: dict[str, list[tuple[int, int]]],
    *,
    script_keys: Literal["tag", "iso"],
) -> str:
    """
    Format Unicode script ranges as a Python dictionary literal.

    Parameters
    ----------
    script_ranges : dict[str, list[tuple[int, int]]]
        Mapping of script identifiers to lists of inclusive Unicode
        codepoint ranges ``(start, end)``.
    script_keys : {"tag", "iso"}
        Determines the type used as keys in the generated dictionary.

        - ``"tag"`` produces keys as plain script tags (``str``).
        - ``"iso"`` produces keys as :class:`ScriptISO` objects.

    Returns
    -------
    str
        A string containing Python source code defining the
        ``UNICODE_SCRIPT_RANGES`` dictionary.
    """
    lines: list[str] = []

    if script_keys == "iso":
        lines.append(
            "UNICODE_SCRIPT_RANGES: dict[ScriptISO, list[tuple[int, int]]] = {"
        )
    else:
        lines.append("UNICODE_SCRIPT_RANGES: dict[str, list[tuple[int, int]]] = {")

    for script in sorted(script_ranges.keys()):
        key = f'ScriptISO("{script.upper()}")' if script_keys == "iso" else repr(script)
        lines.append(f"    {key}: [")
        for start, end in script_ranges[script]:
            lines.append(f"        (0x{start:04X}, 0x{end:04X}),")
        lines.append("    ],")
    lines.append("}")
    return "\n".join(lines)


def _format_block_ranges_section(
    block_ranges: dict[str, tuple[int, int]],
) -> str:
    """
    Generate the formatted section describing Unicode block ranges.

    This function wraps the block range dictionary with a descriptive
    comment header explaining the role of the table within the generated
    module.

    Parameters
    ----------
    block_ranges : dict[str, tuple[int, int]]
        Mapping of Unicode block names to inclusive codepoint ranges.

    Returns
    -------
    str
        A formatted text block containing the explanatory header followed
        by the Python dictionary definition for ``UNICODE_BLOCK_RANGES``.
    """
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
    """
    Generate a dictionary mapping Unicode blocks to their sizes.

    The size of each block is computed as ``end - start + 1`` using the
    inclusive codepoint ranges provided in ``block_ranges``.

    Parameters
    ----------
    block_ranges : dict[str, tuple[int, int]]
        Mapping of Unicode block names to inclusive codepoint ranges.

    Returns
    -------
    str
        A string containing Python source code that defines the
        ``UNICODE_BLOCK_SIZES`` dictionary.
    """
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
    data: UnicodeTablesData,
    options: GeneratorOptions,
) -> str:
    """
    Generate the complete Python module containing Unicode-derived tables.

    The produced text corresponds to the auto-generated module used by
    Fontshow to provide deterministic Unicode block and script metadata.

    Parameters
    ----------
    unicode_version : str
        Unicode version used to derive the tables.
    sources : tuple[pathlib.Path, pathlib.Path, pathlib.Path]
        Paths to the Unicode data source files used to build the tables
        (blocks file, scripts file, and ISO mapping file).
    data : UnicodeTablesData
        Parsed Unicode data required to build the module tables.
    options : GeneratorOptions
        Generation options controlling details such as the type used for
        script keys.

    Returns
    -------
    str
        The complete Python source code of the generated module.
    """
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
    parts: list[str] = [
        header.rstrip(),
        "",
        "from __future__ import annotations",
        "",
    ]

    if options.script_keys == "iso":
        parts.extend(
            [
                "from fontshow.core.types import ScriptISO",
                "",
            ]
        )

    parts.extend(
        [
            _format_block_ranges_section(data.block_ranges),
            "",
            _format_py_dict_block_sizes(data.block_ranges),
            "",
            _format_py_dict_script_ranges(
                data.script_ranges, script_keys=options.script_keys
            ),
            "",
        ]
    )

    if options.script_keys == "iso":
        parts.append("NON_WRITING_SCRIPTS: frozenset[ScriptISO] = frozenset({")
        parts.extend(
            [
                f'    ScriptISO("{code.upper()}"),'
                for code in sorted(data.non_writing_scripts)
            ]
        )
    else:
        parts.append("NON_WRITING_SCRIPTS: frozenset[str] = frozenset({")
        parts.extend([f"    {code!r}," for code in sorted(data.non_writing_scripts)])

    parts.extend(
        [
            "})",
            "",
        ]
    )
    return "\n".join(parts)


def main() -> int:
    """
    Generate the Fontshow Unicode tables module from vendored Unicode data files.

    This command-line entry point reads Unicode Character Database (UCD)
    source files and the ISO15924 registry snapshot, derives normalized
    block and script range tables, and writes the generated module
    ``src/fontshow/ontology/unicode_tables.py``.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Exit status code. Returns ``0`` when the generation completes
        successfully.

    Raises
    ------
    SystemExit
        Raised if required input files are missing or if argument parsing
        fails.
    """
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
        default="src/fontshow/data/unicode",
        help="Directory containing vendored UCD files (default: src/fontshow/data/unicode).",
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
        default="src/fontshow/ontology/unicode_tables.py",
        help="Output module path (default: src/fontshow/ontology/unicode_tables.py).",
    )
    parser.add_argument(
        "--script-keys",
        choices=("tag", "iso"),
        default="tag",
        help=(
            "Key UNICODE_SCRIPT_RANGES by 'tag' (strings like 'latn') or by "
            "'iso' (ScriptISO objects like ScriptISO(\"LATN\")). Default: tag."
        ),
    )
    parser.add_argument(
        "--iso-file",
        default="src/fontshow/data/iso/iso15924-2024.txt",
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
    options = GeneratorOptions(script_keys=args.script_keys)

    data = UnicodeTablesData(
        block_ranges=block_ranges,
        script_ranges=script_ranges,
        non_writing_scripts=non_writing_scripts,
    )

    module_text = _generate_module_text(
        unicode_version=args.unicode_version,
        sources=(blocks_path, scripts_path, iso_path),
        data=data,
        options=options,
    )

    out_path.write_text(module_text, encoding="utf-8")
    print(f"Wrote {out_path} ({len(module_text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
