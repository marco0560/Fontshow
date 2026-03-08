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
    code, out = cli_runner(["fontshow", "dump-fonts", "-o", str(tmp_path / "inv.json")])

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
    code, out = cli_runner(["fontshow", "dump-fonts", "--output", "out.json"])
    assert code == expected_code
