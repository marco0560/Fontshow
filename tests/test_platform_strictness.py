"""
Verify platform strictness behavior.

This module tests that Fontshow enforces the expected platform
constraints when executing CLI commands.

Responsibilities
----------------
- Verify that supported environments are accepted.
- Ensure unsupported environments are rejected deterministically.
- Validate the strict platform checks performed before pipeline
  execution.

Design principles
-----------------
Platform validation must fail early and deterministically whenever
required system capabilities or assumptions are not satisfied.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and validates
the environment strictness guarantees enforced by the Fontshow CLI.
"""

import argparse
import json
import os
from pathlib import Path

from fontshow.cli.create_catalog import (
    build_parser,
    run_create_catalog,
)
from fontshow.inventory.platform_metadata import collect_platform_metadata


def test_cli_rejects_platform_mismatch(tmp_path):
    """
    Verify that create-catalog rejects inventories from a mismatched platform.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used to store the inventory file.

    Returns
    -------
    None

    Notes
    -----
    The test clones the current runtime metadata and changes only the
    machine identifier so the mismatch is controlled and deterministic.
    """
    runtime = collect_platform_metadata()

    # Force mismatch in a controlled way
    bad_env = dict(runtime)
    bad_env["machine"] = "mismatch-cpu"

    inventory = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": bad_env,
        },
        "fonts": [
            {"name": "Alpha", "coverage": {"languages": ["en"]}},
        ],
    }

    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps(inventory), encoding="utf-8")

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(inv),
            "--quiet",
        ]
    )

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        rc = run_create_catalog(args)
    finally:
        os.chdir(old_cwd)

    assert rc == 1
