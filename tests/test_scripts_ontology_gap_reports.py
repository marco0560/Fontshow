"""
Exercise ontology gap report helper scripts.

Responsibilities
----------------
- Verify the raw ISO-versus-ontology gap report remains deterministic.
- Verify the encountered inventory-versus-ontology gap report narrows
  the scope to scripts actually seen in enriched inventories.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_RAW_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_ontology_script_gap_report.py"
)
_RAW_SPEC = importlib.util.spec_from_file_location(
    "generate_ontology_script_gap_report", _RAW_SCRIPT_PATH
)
assert _RAW_SPEC is not None and _RAW_SPEC.loader is not None
raw_gap_report = importlib.util.module_from_spec(_RAW_SPEC)
sys.modules[_RAW_SPEC.name] = raw_gap_report
_RAW_SPEC.loader.exec_module(raw_gap_report)

_ENCOUNTERED_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_inventory_encountered_ontology_gap_report.py"
)
_ENCOUNTERED_SPEC = importlib.util.spec_from_file_location(
    "generate_inventory_encountered_ontology_gap_report",
    _ENCOUNTERED_SCRIPT_PATH,
)
assert _ENCOUNTERED_SPEC is not None and _ENCOUNTERED_SPEC.loader is not None
encountered_gap_report = importlib.util.module_from_spec(_ENCOUNTERED_SPEC)
sys.modules[_ENCOUNTERED_SPEC.name] = encountered_gap_report
_ENCOUNTERED_SPEC.loader.exec_module(encountered_gap_report)


def test_build_raw_gap_report_lists_missing_iso_scripts() -> None:
    """
    Ensure the raw gap report captures missing ISO 15924 ontology entries.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    report = raw_gap_report.build_raw_gap_report(
        {
            "LATN": "Latin",
            "ARAB": "Arabic",
            "ZZZZ": "Synthetic Test Script",
        }
    )

    assert report["missing_from_script_info"] == [
        {"code": "ZZZZ", "name": "Synthetic Test Script"}
    ]
    assert report["missing_curated_specimen"] == []


def test_build_encountered_gap_report_narrows_to_seen_inventory_scripts() -> None:
    """
    Ensure the encountered gap report ignores unencountered ontology gaps.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    report = encountered_gap_report.build_encountered_gap_report(
        {
            "fonts": [
                {
                    "coverage": {"scripts": ["latn", "zzzz"], "primary_script": "LATN"},
                    "inference": {
                        "scripts": ["latn", "zzzz"],
                        "primary_script": "ZZZZ",
                    },
                    "typography": {"primary_script": "ZZZZ"},
                },
                {
                    "coverage": {"scripts": ["brai"], "primary_script": "BRAI"},
                    "inference": {"scripts": ["brai"], "primary_script": "BRAI"},
                    "typography": {"primary_script": "BRAI"},
                },
            ]
        }
    )

    assert report["seen_missing_from_script_info"] == ["ZZZZ"]
    assert report["seen_missing_curated_specimen"] == []


def test_raw_gap_report_main_writes_json(tmp_path: Path) -> None:
    """
    Ensure the raw gap report script writes a deterministic JSON artifact.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory used to stage input and output files.

    Returns
    -------
    None
    """
    iso_path = tmp_path / "iso15924.txt"
    iso_path.write_text(
        "# comment\nLatn;215;Latin;;;;\nZzzz;999;Synthetic Test Script;;;;\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "raw-gap.json"

    rc = raw_gap_report.main(
        ["--iso-source", str(iso_path), "--output", str(output_path)]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert rc == 0
    assert payload["missing_from_script_info"] == [
        {"code": "ZZZZ", "name": "Synthetic Test Script"}
    ]


def test_encountered_gap_report_main_writes_json(tmp_path: Path) -> None:
    """
    Ensure the encountered gap report script writes a deterministic JSON artifact.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory used to stage input and output files.

    Returns
    -------
    None
    """
    inventory_path = tmp_path / "font_inventory_enriched.json"
    inventory_path.write_text(
        json.dumps(
            {
                "fonts": [
                    {
                        "coverage": {
                            "scripts": ["latn", "zzzz"],
                            "primary_script": "LATN",
                        },
                        "inference": {
                            "scripts": ["latn", "zzzz"],
                            "primary_script": "ZZZZ",
                        },
                        "typography": {"primary_script": "ZZZZ"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "encountered-gap.json"

    rc = encountered_gap_report.main(
        ["--inventory", str(inventory_path), "--output", str(output_path)]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert rc == 0
    assert payload["seen_missing_from_script_info"] == ["ZZZZ"]
    assert payload["seen_missing_curated_specimen"] == []
