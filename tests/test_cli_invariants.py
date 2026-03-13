"""
Verify CLI invariants.

This module tests structural invariants of the Fontshow command-line
interface to ensure that CLI commands maintain stable semantics across
versions.

Responsibilities
----------------
- Verify that CLI commands expose the expected parser interface.
- Ensure that CLI command wiring remains stable.
- Validate invariants required by downstream tooling and tests.

Design principles
-----------------
Invariant tests verify CLI structure rather than execution behavior so
regressions in command definitions can be detected early and
deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and ensures
the structural stability of the Fontshow command-line interface.
"""

import argparse
import json

from fontshow.cli.create_catalog import build_parser, run_create_catalog


def _run(tmp_path, inventory):
    """
    Execute ``create-catalog`` against a temporary inventory file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used to materialize the input
        inventory JSON file.
    inventory : dict
        Inventory payload written to disk and passed to the CLI parser.

    Returns
    -------
    int
        Exit code returned by `run_create_catalog`.
    """
    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inventory), encoding="utf-8")

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(p),
            "--quiet",
        ]
    )

    return run_create_catalog(args)


def test_cli_invalid_schema(tmp_path):
    """
    Verify that create-catalog rejects inventories with an unsupported schema.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used by `_run`.

    Returns
    -------
    None
    """
    inv = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_missing_run_environment(tmp_path):
    """
    Verify that schema v1.2 inventories missing ``run_environment`` fail.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used by `_run`.

    Returns
    -------
    None
    """
    inv = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_platform_mismatch(tmp_path, monkeypatch):
    """
    Verify that create-catalog rejects inventories from a mismatched platform.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used by `_run`.
    monkeypatch : pytest.MonkeyPatch
        Present as a pytest fixture in this test signature.

    Returns
    -------
    None
    """
    inv = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": {
                "os": "fake-os",
                "machine": "fake-cpu",
                "execution_context": {"type": "fake"},
            },
        },
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_missing_fonts(tmp_path):
    """
    Verify that inventories missing the ``fonts`` container fail fast.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used by `_run`.

    Returns
    -------
    None
    """
    inv = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": {
                "os": "x",
                "machine": "y",
                "execution_context": {"type": "z"},
            },
        }
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_malformed_font_descriptor(tmp_path):
    """
    Verify that non-dictionary font entries are rejected by the CLI path.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory fixture used by `_run`.

    Returns
    -------
    None
    """
    inv = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": {
                "os": "x",
                "machine": "y",
                "execution_context": {"type": "z"},
            },
        },
        "fonts": ["not-a-dict"],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1
