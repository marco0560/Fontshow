"""
Verify repository artifact hygiene.

This module tests that generated artifacts produced by the Fontshow
pipeline follow repository conventions and remain consistent with the
expected project structure.

Responsibilities
----------------
- Verify that generated files conform to expected naming conventions.
- Ensure that artifact locations follow repository layout rules.
- Detect accidental creation of unexpected output files.

Design principles
-----------------
Artifact hygiene tests operate only on generated test fixtures and
temporary directories so repository integrity rules can be validated
without altering the working tree.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the structural integrity of artifacts produced by the Fontshow
generation pipeline.
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


def test_only_tex_artifact_created(tmp_path):
    """
    Verify that create-catalog leaves only the expected JSON and TEX artifacts.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used both for the input
        inventory and for the generated catalog artifact.

    Returns
    -------
    None

    Notes
    -----
    The test changes the current working directory to the temporary
    directory so generated files are isolated and easy to enumerate.
    It asserts the edge case that no unexpected side artifacts are
    created alongside the expected ``.tex`` output.
    """
    inventory = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": collect_platform_metadata(),
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
        assert rc == 0
    finally:
        os.chdir(old_cwd)

    files = list(tmp_path.iterdir())

    # Expect exactly:
    # - inventory file
    # - generated .tex file
    assert len(files) == 2

    tex_files = [p for p in files if p.suffix == ".tex"]
    assert len(tex_files) == 1

    # Ensure no unexpected artifacts
    for p in files:
        assert p.suffix in {".json", ".tex"}
