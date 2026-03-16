"""
Verify the parse-inventory CLI command.

This module tests the behavior of the `fontshow parse-inventory`
command, ensuring that inventory parsing works correctly when invoked
through the command-line interface.

Responsibilities
----------------
- Validate successful parsing of inventory files through the CLI.
- Verify correct handling of command-line options.
- Ensure deterministic output behavior for parsed inventories.

Design principles
-----------------
Tests use temporary files and subprocess invocation so the CLI
behavior is validated in conditions similar to real user execution.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the command-line interface responsible for parsing font inventories.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _valid_inventory_from_cli(tmp_path, *_ignored):
    """
    Build a schema-valid inventory payload using runtime platform metadata.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the metadata probe file.
    *_ignored : object
        Ignored positional arguments retained for caller compatibility.

    Returns
    -------
    dict
        Minimal inventory payload suitable for CLI parse-inventory tests.
    """
    probe = tmp_path / "probe_env.json"

    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; "
                "from fontshow.inventory.platform_metadata import collect_platform_metadata; "
                f"open(r'{probe}', 'w').write(json.dumps(collect_platform_metadata()))"
            ),
        ],
        check=True,
    )

    env = json.loads(probe.read_text())

    return {
        "metadata": {
            "schema_version": "1.2",
            "input_inventory_tool": "fontshow",
            "input_inventory_tool_version": "test",
            "inference_level": "basic",
            "fonttools": {
                "available": False,
                "fontconfig_charset_included": False,
                "version": "unknown",
            },
            "run_environment": env,
        },
        "fonts": [],
    }


@pytest.mark.parametrize("stub_parse_inventory", ["ok"], indirect=True)
def test_parse_inventory_success(cli_runner, stub_parse_inventory, tmp_path):
    """
    Verify that the parse-inventory CLI succeeds with the success stub.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_parse_inventory : object
        Indirect fixture configuring the parse-inventory stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used for input and output files.

    Returns
    -------
    None
    """
    inp = tmp_path / "in.json"
    outp = tmp_path / "out.json"

    inp.write_text(json.dumps(_valid_inventory_from_cli(tmp_path, 0)))

    code, out = cli_runner(["fontshow", "parse-inventory", str(inp), "-o", str(outp)])

    assert code == 0


@pytest.mark.parametrize(
    "stub_parse_inventory, expected_code",
    [
        ("fail", 2),
        ("boom", 2),
    ],
    indirect=["stub_parse_inventory"],
)
def test_parse_inventory_failure(cli_runner, stub_parse_inventory, expected_code):
    """
    Verify that parse-inventory propagates stubbed failure exit codes.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_parse_inventory : object
        Indirect fixture configuring the parse-inventory stub to fail or crash.
    expected_code : int
        Parameterized exit code expected from the stubbed behavior.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "parse-inventory", "--input", "inv.json"])
    assert code == expected_code


def test_parse_inventory_accepts_strict_bcp47_flag(cli_runner, tmp_path):
    """
    Verify that parse-inventory accepts the ``--strict-bcp47`` flag.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    tmp_path : pathlib.Path
        Temporary directory fixture used for input and output files.

    Returns
    -------
    None
    """
    input_file = tmp_path / "in.json"
    output_file = tmp_path / "out.json"

    input_file.write_text(json.dumps(_valid_inventory_from_cli(tmp_path, 0)))

    code, out = cli_runner(
        [
            "fontshow",
            "parse-inventory",
            str(input_file),
            "-o",
            str(output_file),
            "--strict-bcp47",
        ]
    )

    assert code == 0


def test_parse_inventory_defaults_to_raw_inventory_without_validate_flag():
    """
    Verify that parse-inventory defaults to ``font_inventory.json``.

    Returns
    -------
    None
    """
    from fontshow.cli.parse_inventory import build_parser

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args([])

    resolved = (
        Path("font_inventory_enriched.json")
        if args.validate_inventory
        else Path("font_inventory.json")
    )
    assert resolved == Path("font_inventory.json")


def test_parse_inventory_validate_only_defaults_to_enriched_inventory():
    """
    Verify that parse-inventory validate-only mode defaults to the enriched inventory.

    Returns
    -------
    None
    """
    from fontshow.cli.parse_inventory import build_parser

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(["-I"])

    resolved = (
        Path("font_inventory_enriched.json")
        if args.validate_inventory and args.input is None
        else args.input
    )
    assert resolved == Path("font_inventory_enriched.json")


def test_parse_inventory_accepts_missing_language_coverage_listing_flag():
    """
    Verify that parse-inventory accepts the reporting flag.

    Returns
    -------
    None
    """
    from fontshow.cli.parse_inventory import build_parser

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(["--list-missing-language-coverage"])

    assert args.list_missing_language_coverage is True
