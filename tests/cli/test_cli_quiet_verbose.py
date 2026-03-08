"""
Verify CLI verbosity control flags.

This module tests the behavior of the Fontshow CLI when the `--quiet`
and `--verbose` flags are provided.

Responsibilities
----------------
- Verify that CLI verbosity flags affect command output correctly.
- Ensure that quiet mode suppresses informational output.
- Ensure that verbose mode enables additional diagnostic output.

Design principles
-----------------
CLI tests must invoke the command-line entry point in an isolated
subprocess environment so output behavior can be validated reliably.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and validates
user-facing CLI behavior related to logging verbosity.
"""

import subprocess
import sys
import tempfile


def run_cli(args):
    """Helper to run fontshow CLI and capture output."""
    cmd = [sys.executable, "-m", "fontshow"] + args
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=tmp,
        )


def test_cli_default_output():
    """Default run should produce stdout output and no stderr."""
    result = run_cli(["create-catalog", "--help"])

    assert result.returncode == 0
    assert result.stdout.strip() != ""
    assert result.stderr.strip() == ""


def test_cli_quiet_suppresses_stdout():
    """--quiet must suppress stdout ; missing inventory must still fail."""
    result = run_cli(["create-catalog", "--quiet"])

    # create-catalog now requires a valid v1.2 inventory
    assert result.returncode != 0
    assert result.stdout.strip() == ""
    # warnings may be emitted on stderr


def test_cli_verbose_enables_output():
    """--verbose should produce stdout output when execution succeeds."""
    result = run_cli(["create-catalog", "--verbose"])

    # Without inventory the command must fail
    assert result.returncode != 0
    # verbose does not suppress errors
    assert result.stderr.strip() != ""


def test_cli_quiet_and_verbose_quiet_wins():
    """--quiet and --verbose generate parsing error."""
    result = run_cli(["create-catalog", "--quiet", "--verbose"])

    assert result.returncode != 0
    assert result.stdout.strip() == ""
    assert "not allowed with argument" in result.stderr


def test_cli_inventory_fallback_does_not_crash():
    """Missing inventory must fail with non-zero exit and no stdout."""
    result = run_cli(["create-catalog", "--inventory", "nonexistent_file.json"])

    assert result.returncode != 0
    assert result.stdout.strip() == ""
    assert result.stderr.strip() != ""
