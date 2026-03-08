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
    inv = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_missing_run_environment(tmp_path):
    inv = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_platform_mismatch(tmp_path, monkeypatch):
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
