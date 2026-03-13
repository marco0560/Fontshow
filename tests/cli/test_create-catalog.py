"""
Verify the create-catalog CLI command.

This module tests the behavior of the `fontshow create-catalog`
command, ensuring correct exit codes and option handling.

Responsibilities
----------------
- Validate successful catalog generation via the CLI.
- Verify support for output-related CLI options.
- Ensure command invocation follows expected semantics.

Design principles
-----------------
CLI command tests rely on stubbed implementations and temporary
directories so behavior can be verified without invoking the full
Fontshow pipeline.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the command-line interface for catalog generation.
"""

import pytest


@pytest.mark.parametrize("stub_create_catalog", ["ok"], indirect=True)
def test_create_catalog_success(cli_runner, stub_create_catalog, tmp_path):
    """
    Verify that the create-catalog CLI succeeds with the success stub.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_create_catalog : object
        Indirect fixture configuring the create-catalog stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture present in the test signature.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "create-catalog", "--inventory", "inv.json"])

    assert code == 0


@pytest.mark.parametrize("stub_create_catalog", ["ok"], indirect=True)
def test_create_catalog_accepts_output_option(
    cli_runner, stub_create_catalog, tmp_path
):
    """
    Verify that create-catalog accepts an explicit output path option.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_create_catalog : object
        Indirect fixture configuring the create-catalog stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build the output file path.

    Returns
    -------
    None
    """
    out_tex = tmp_path / "out.tex"
    code, out = cli_runner(
        ["fontshow", "create-catalog", "--inventory", "inv.json", "-o", str(out_tex)]
    )

    assert code == 0


@pytest.mark.parametrize(
    "stub_create_catalog, expected_code",
    [
        ("fail", 1),  # errore atteso
        ("boom", 2),  # errore interno (eccezione)
    ],
    indirect=["stub_create_catalog"],
)
def test_create_catalog_failure(cli_runner, stub_create_catalog, expected_code):
    """
    Verify that create-catalog propagates stubbed failure exit codes.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_create_catalog : object
        Indirect fixture configuring the create-catalog stub to fail or crash.
    expected_code : int
        Parameterized exit code expected from the stubbed behavior.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "create-catalog", "--inventory", "inv.json"])
    assert code == expected_code
