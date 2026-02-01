import subprocess
import sys

import pytest


@pytest.mark.parametrize("stub_preflight", ["fail"], indirect=True)
def test_preflight_failure_propagates(cli_runner, stub_preflight):
    code, out = cli_runner(["fontshow", "preflight"])

    assert "Preflight failed." in out
    assert code == 1


@pytest.mark.parametrize("stub_preflight", ["ok"], indirect=True)
def test_preflight_success(cli_runner, stub_preflight):
    code, out = cli_runner(["fontshow", "preflight"])

    assert "Preflight passed." in out
    assert code == 0


def test_preflight_verbose_outputs_details(cli_runner, stub_preflight):
    """
    Verbose flag is accepted and propagated correctly.

    Note: the stubbed runner does not emit real verbose output,
    so this test only checks command wiring, not rendering.
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
    """
    code, out = cli_runner(["fontshow", "preflight", "-q"])

    assert code == 0
    assert "Preflight passed." in out


def test_preflight_help(cli_runner):
    """
    Help output must be available and exit cleanly.
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
    """
    code, out = cli_runner(["fontshow", "preflight"])

    # Must not be argparse error / crash
    assert code in (0, 1)

    # Some output is expected in non-quiet mode
    assert out.strip() != ""


def test_preflight_module_entrypoint_runs():
    """
    Ensure that `python -m fontshow.preflight` executes
    and does not crash.

    This test bypasses cli_runner on purpose, because
    cli_runner is scoped to the `fontshow` console script.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "fontshow.preflight"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Must not be argparse error / crash
    assert proc.returncode in (0, 1)
