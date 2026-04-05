#!/usr/bin/env python3
"""
Generate the raw ontology-versus-ISO script gap report.

This maintenance script compares the repository's ISO 15924 source file
against the current ontology script table and reports which ISO scripts
are still missing from ``SCRIPT_INFO``. It also reports whether any
implemented ontology scripts lack a curated specimen.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fontshow.ontology.language_tables import SCRIPT_INFO

_DEFAULT_ISO_PATH = Path("src/fontshow/data/iso/iso15924-2024.txt")
_DEFAULT_OUTPUT_PATH = Path("reports/ontology_script_gap_report.json")


def load_iso15924_codes(path: Path) -> dict[str, str]:
    """
    Load ISO 15924 script codes and English names from the source file.

    Parameters
    ----------
    path : pathlib.Path
        Path to the repository copy of the ISO 15924 source file.

    Returns
    -------
    dict[str, str]
        Mapping from upper-case ISO 15924 code to English script name.
    """
    records: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split(";")
        if len(fields) < 3:
            continue
        code = fields[0].strip().upper()
        name = fields[2].strip()
        if len(code) == 4 and code.isalpha():
            records[code] = name
    return records


def build_raw_gap_report(iso_records: dict[str, str]) -> dict[str, Any]:
    """
    Build the raw ontology gap report from ISO and ontology data.

    Parameters
    ----------
    iso_records : dict[str, str]
        Mapping of ISO 15924 codes to English names.

    Returns
    -------
    dict[str, object]
        JSON-serializable raw gap report.
    """
    implemented = {str(code).upper(): info for code, info in SCRIPT_INFO.items()}
    missing_from_script_info = [
        {"code": code, "name": iso_records[code]}
        for code in sorted(set(iso_records) - set(implemented))
    ]
    missing_curated_specimen = [
        {
            "code": code,
            "canonical_name": str(implemented[code].get("canonical_name", "")),
        }
        for code in sorted(implemented)
        if not isinstance(implemented[code].get("specimen"), str)
        or not str(implemented[code].get("specimen", "")).strip()
    ]
    return {
        "iso15924_count": len(iso_records),
        "script_info_count": len(implemented),
        "missing_from_script_info": missing_from_script_info,
        "missing_curated_specimen": missing_curated_specimen,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments for raw ontology gap reporting.

    Parameters
    ----------
    argv : list[str] | None, optional
        Explicit argument vector used by tests.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iso-source",
        type=Path,
        default=_DEFAULT_ISO_PATH,
        help="Path to the ISO 15924 source file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT_PATH,
        help="Output JSON report path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """
    Generate the raw ontology gap report.

    Parameters
    ----------
    argv : list[str] | None, optional
        Explicit argument vector used by tests.

    Returns
    -------
    int
        Process exit code.
    """
    args = parse_args(argv)
    report = build_raw_gap_report(load_iso15924_codes(args.iso_source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
