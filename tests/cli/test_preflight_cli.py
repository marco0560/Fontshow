"""
Verify the preflight CLI command.

This module tests the behavior of the `fontshow preflight` command,
ensuring that the CLI correctly invokes the preflight validation
pipeline.

Responsibilities
----------------
- Verify that the preflight CLI command executes successfully.
- Ensure correct propagation of exit codes.
- Validate expected CLI output semantics.

Design principles
-----------------
Preflight CLI tests invoke the command through subprocess execution so
the complete CLI behavior—including exit codes and output streams—is
verified in an isolated environment.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and validates
the command-line entry point for the preflight validation pipeline.
"""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("stub_preflight", ["fail"], indirect=True)
def test_preflight_failure_propagates(cli_runner, stub_preflight):
    """
    Verify that a failing stubbed preflight run propagates exit code and message.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_preflight : object
        Indirect fixture configuring the preflight stub to fail.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight"])

    assert "Preflight failed." in out
    assert code == 1


@pytest.mark.parametrize("stub_preflight", ["ok"], indirect=True)
def test_preflight_success(cli_runner, stub_preflight):
    """
    Verify that a successful stubbed preflight run reports success cleanly.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_preflight : object
        Indirect fixture configuring the preflight stub to succeed.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight"])

    assert "Preflight passed." in out
    assert code == 0


def test_preflight_verbose_outputs_details(cli_runner, stub_preflight):
    """
    Verbose flag is accepted and propagated correctly.

    Note: the stubbed runner does not emit real verbose output,
    so this test only checks command wiring, not rendering.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_preflight : object
        Fixture providing the stubbed successful preflight implementation.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight", "-v"])

    assert code == 0
    assert "Preflight passed." in out


def test_preflight_quiet_outputs_nothing(cli_runner, stub_preflight):
    """
    NOTE:
    This test uses a stubbed preflight runner.

    The stub always prints "Preflight passed." regardless of -q,
    because it does not implement the real CLI rendering logic.

    The purpose of this test is NOT to verify output suppression,
    but to ensure that:
      - the command executes correctly
      - the exit code is propagated
      - the quiet flag does not break execution

    Full quiet-mode behavior is tested only in integration tests
    using the real preflight runner.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.
    stub_preflight : object
        Fixture providing the stubbed successful preflight implementation.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight", "-q"])

    assert code == 0
    assert "Preflight passed." in out


def test_preflight_help(cli_runner):
    """
    Help output must be available and exit cleanly.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight", "-h"])

    assert code == 0
    assert "usage:" in out.lower()


def test_preflight_real_runner_does_not_crash(cli_runner):
    """
    Regression test for the preflight CLI renderer.

    This test uses the REAL preflight runner (no stubbing)
    and ensures that the CLI does not crash due to
    invalid unpacking assumptions.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight"])

    # Must not be argparse error / crash
    assert code in (0, 1)

    # Some output is expected in non-quiet mode
    assert out.strip() != ""


def test_preflight_real_runner_quiet_suppresses_stdout(cli_runner):
    """
    Verify that quiet mode suppresses stdout for the real preflight runner.

    Parameters
    ----------
    cli_runner : object
        Fixture used to execute the console entry point.

    Returns
    -------
    None
    """
    code, out = cli_runner(["fontshow", "preflight", "-q"])

    assert code in (0, 1)
    assert out.strip() == ""


def test_preflight_module_entrypoint_runs():
    """
    Ensure that `python -m fontshow.preflight` executes
    and does not crash.

    This test bypasses cli_runner on purpose, because
    cli_runner is scoped to the `fontshow` console script.

    Returns
    -------
    None
    """
    proc = subprocess.run(
        [sys.executable, "-m", "fontshow.preflight"],
        capture_output=True,
        text=True,
    )

    # Must not be argparse error / crash
    assert proc.returncode in (0, 1)
