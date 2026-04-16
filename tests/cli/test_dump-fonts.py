"""
Verify the dump-fonts CLI command.

This module tests the behavior of the `fontshow dump-fonts` command,
ensuring correct exit codes and expected CLI interactions.

Responsibilities
----------------
- Verify successful inventory generation through the CLI.
- Validate error handling for failing dump operations.
- Confirm command-line interface semantics.

Design principles
-----------------
Tests use stubbed implementations of the dump operation so CLI
behavior can be validated without depending on actual system font
installations.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the CLI entry point responsible for font inventory generation.
"""

import pytest


@pytest.mark.parametrize("stub_dump_fonts", ["ok"], indirect=True)
def test_dump_fonts_success(cli_runner, stub_dump_fonts, tmp_path):
    """
    Verify that the dump-fonts CLI succeeds with the success stub.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_dump_fonts : object
        Indirect fixture configuring the dump-fonts stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build the output file path.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "dump-fonts", "-o", str(tmp_path / "inv.json")])

    assert code == 0


@pytest.mark.parametrize("stub_dump_fonts", ["ok"], indirect=True)
def test_dump_fonts_accepts_no_loadability_flag(cli_runner, stub_dump_fonts, tmp_path):
    """
    Verify that dump-fonts accepts the ``--no-loadability`` flag.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_dump_fonts : object
        Indirect fixture configuring the dump-fonts stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build the output file path.

    Returns
    -------
    None
    """
    code, out = cli_runner(
        [
            "fontshow",
            "dump-fonts",
            "--no-loadability",
            "-o",
            str(tmp_path / "inv.json"),
        ]
    )

    assert code == 0


@pytest.mark.parametrize("stub_dump_fonts", ["ok"], indirect=True)
def test_dump_fonts_accepts_paths(cli_runner, stub_dump_fonts, tmp_path):
    """
    Verify that dump-fonts accepts one or more controlled discovery paths.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_dump_fonts : object
        Indirect fixture configuring the dump-fonts stub to succeed.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build the discovery roots.

    Returns
    -------
    None
    """
    root_a = tmp_path / "fonts-a"
    root_b = tmp_path / "fonts-b"
    root_a.mkdir()
    root_b.mkdir()

    code, out = cli_runner(
        [
            "fontshow",
            "dump-fonts",
            "--paths",
            str(root_a),
            str(root_b),
            "-o",
            str(tmp_path / "inv.json"),
        ]
    )

    assert code == 0


@pytest.mark.parametrize(
    "stub_dump_fonts, expected_code",
    [
        ("fail", 2),  # errore atteso
        ("boom", 2),  # errore interno
    ],
    indirect=["stub_dump_fonts"],
)
def test_dump_fonts_failure(cli_runner, stub_dump_fonts, expected_code):
    """
    Verify that dump-fonts propagates stubbed failure exit codes.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_dump_fonts : object
        Indirect fixture configuring the dump-fonts stub to fail or crash.
    expected_code : int
        Parameterized exit code expected from the stubbed behavior.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "dump-fonts", "--output", "out.json"])
    assert code == expected_code
