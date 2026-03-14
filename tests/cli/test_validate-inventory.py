"""
Verify the validate-inventory CLI command.

This module tests the behavior of the `fontshow validate-inventory`
command, ensuring correct top-level CLI wiring and shared flag support.

Responsibilities
----------------
- Validate successful command dispatch via the root CLI.
- Verify that shared quiet/verbose flags are accepted by the parser.
- Verify the default inventory path when no explicit path is provided.

Design principles
-----------------
These tests stub the command implementation so they only exercise CLI
argument registration and dispatch behavior.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the command-line interface for inventory validation.
"""

import argparse
from pathlib import Path

import pytest

from fontshow.cli.validate_inventory import build_parser


@pytest.mark.parametrize("stub_validate_inventory", ["ok"], indirect=True)
def test_validate_inventory_success(cli_runner, stub_validate_inventory, tmp_path):
    """
    Verify that validate-inventory dispatches successfully from the root CLI.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_validate_inventory : object
        Indirect fixture configuring the validate-inventory stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build the input file path.

    Returns
    -------
    None
    """
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}", encoding="utf-8")

    code, out = cli_runner(["fontshow", "validate-inventory", str(inventory)])

    assert code == 0


@pytest.mark.parametrize("stub_validate_inventory", ["ok"], indirect=True)
def test_validate_inventory_accepts_quiet_flag(
    cli_runner, stub_validate_inventory, tmp_path
):
    """
    Verify that validate-inventory accepts the shared ``--quiet`` flag.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_validate_inventory : object
        Indirect fixture configuring the validate-inventory stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build the input file path.

    Returns
    -------
    None
    """
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}", encoding="utf-8")

    code, out = cli_runner(["fontshow", "validate-inventory", "-q", str(inventory)])

    assert code == 0


def test_validate_inventory_defaults_to_font_inventory_json():
    """
    Verify that validate-inventory defaults to ``font_inventory.json``.
    """
    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args([])

    assert args.path == Path("font_inventory.json")
