"""
Verify create-catalog inventory validation failures.

This module tests the validation failures surfaced by the create-catalog
pipeline when the input inventory is structurally or semantically
unusable for rendering.

Responsibilities
----------------
- Ensure invalid inventory data is rejected by create-catalog.
- Detect malformed or inconsistent catalog input.
- Verify correct failure reporting on invalid inventories.

Design principles
-----------------
These tests operate on controlled inventories so create-catalog failure
paths can be verified deterministically without external dependencies.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
create-catalog's inventory validation behavior.
"""

import argparse
import json

from fontshow.cli.create_catalog import build_parser, run_create_catalog


def test_create_catalog_fails_on_invalid_language_metadata(tmp_path):
    """
    Verify that create-catalog fails on invalid language metadata.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used to write the inventory file.

    Returns
    -------
    None
    """
    inv = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [
            {
                "name": "BrokenFont",
                "coverage": {"languages": ["xx"]},
            }
        ],
    }

    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inv), encoding="utf-8")

    # Create real parser (as CLI does)
    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(p),
            "--quiet",
        ]
    )

    rc = run_create_catalog(args)
    assert rc == 1


def test_create_catalog_fails_on_top_level_warning_issue(tmp_path):
    """
    Verify that create-catalog also fails on top-level inventory warnings.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used to write the inventory file.

    Returns
    -------
    None

    Notes
    -----
    The setup injects a top-level warning to confirm that the command
    rejects inventories with non-language warning conditions as well.
    """
    inv = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [
            {
                "name": "SomeFont",
                "coverage": {"languages": ["en"]},
            }
        ],
        # Simulate a semantic issue not related to language
        "warnings": [
            {
                "severity": "warning",
                "code": "semantic_inconsistency",
                "message": "Inconsistent metadata detected",
            }
        ],
    }

    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inv), encoding="utf-8")

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(p),
            "--quiet",
        ]
    )

    rc = run_create_catalog(args)
    assert rc == 1
