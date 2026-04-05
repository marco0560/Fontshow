#!/usr/bin/env python3
"""
Generate the encountered inventory-versus-ontology script gap report.

This maintenance script reads a schema v1.4 enriched inventory and
reports the narrower ontology gap: scripts actually seen in the
inventory that are either absent from ``SCRIPT_INFO`` or present but
lacking a curated specimen.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fontshow.ontology.language_tables import SCRIPT_INFO

_DEFAULT_INVENTORY_PATH = Path("font_inventory_enriched.json")
_DEFAULT_OUTPUT_PATH = Path("reports/inventory_encountered_ontology_gap_report.json")


def load_enriched_inventory(path: Path) -> dict[str, Any]:
    """
    Load the enriched inventory JSON payload.

    Parameters
    ----------
    path : pathlib.Path
        Path to the schema v1.4 enriched inventory file.

    Returns
    -------
    dict[str, object]
        Parsed inventory payload.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def collect_seen_scripts(data: dict[str, Any]) -> set[str]:
    """
    Collect all explicit script identifiers seen in the enriched inventory.

    Parameters
    ----------
    data : dict[str, object]
        Parsed enriched inventory payload.

    Returns
    -------
    set[str]
        Upper-case script identifiers encountered in coverage,
        inference, or typography primary-script fields.
    """
    seen: set[str] = set()
    for font in data.get("fonts", []):
        if not isinstance(font, dict):
            continue
        for bucket_name in ("coverage", "inference", "typography"):
            bucket = font.get(bucket_name)
            if not isinstance(bucket, dict):
                continue
            scripts = bucket.get("scripts")
            if isinstance(scripts, list):
                for script in scripts:
                    if isinstance(script, str) and script.strip():
                        seen.add(script.strip().upper())
            primary = bucket.get("primary_script")
            if isinstance(primary, str) and primary.strip():
                seen.add(primary.strip().upper())
    return seen


def build_encountered_gap_report(data: dict[str, Any]) -> dict[str, Any]:
    """
    Build the encountered inventory-versus-ontology gap report.

    Parameters
    ----------
    data : dict[str, object]
        Parsed enriched inventory payload.

    Returns
    -------
    dict[str, object]
        JSON-serializable encountered-gap report.
    """
    seen = collect_seen_scripts(data)
    implemented = {str(code).upper(): info for code, info in SCRIPT_INFO.items()}
    seen_missing_from_script_info = sorted(seen - set(implemented))
    seen_missing_curated_specimen = sorted(
        code
        for code in seen & set(implemented)
        if not isinstance(implemented[code].get("specimen"), str)
        or not str(implemented[code].get("specimen", "")).strip()
    )
    return {
        "seen_script_count": len(seen),
        "seen_scripts": sorted(seen),
        "seen_missing_from_script_info": seen_missing_from_script_info,
        "seen_missing_curated_specimen": seen_missing_curated_specimen,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments for encountered-gap reporting.

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
        "--inventory",
        type=Path,
        default=_DEFAULT_INVENTORY_PATH,
        help="Path to the schema v1.4 enriched inventory JSON file",
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
    Generate the encountered inventory gap report.

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
    report = build_encountered_gap_report(load_enriched_inventory(args.inventory))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
