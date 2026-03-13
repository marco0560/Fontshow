"""
Verify strict semantic validation.

This module tests the semantic validation rules applied to catalog
and inventory data structures produced by the Fontshow pipeline.

Responsibilities
----------------
- Ensure semantic validation rules are enforced.
- Detect malformed or inconsistent catalog entries.
- Verify correct error reporting when semantic violations occur.

Design principles
-----------------
Semantic validation tests operate on controlled inputs so logical
consistency of catalog structures can be verified deterministically
without depending on external resources.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
semantic correctness of internal Fontshow data representations.
"""

import argparse
import json

from fontshow.cli.create_catalog import build_parser, run_create_catalog


def test_semantic_validaion_fails(tmp_path):
    """
    Verify that strict semantic validation fails on invalid language metadata.

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


def test_semantic_validation_fails_on_non_language_issue(tmp_path):
    """
    Verify that strict semantic validation also fails on non-language warnings.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used to write the inventory file.

    Returns
    -------
    None

    Notes
    -----
    The setup injects a top-level semantic warning to confirm that
    strict mode is not limited to language-related issues.
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
