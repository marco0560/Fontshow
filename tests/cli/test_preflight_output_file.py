"""
Verify preflight CLI output file handling.

This module tests the behavior of the preflight CLI when an output file
is requested, ensuring that results are written correctly to the
specified location.

Responsibilities
----------------
- Verify that preflight results can be written to an output file.
- Ensure correct serialization of preflight results.
- Validate expected CLI semantics when an output path is provided.

Design principles
-----------------
Tests operate on in-memory results and temporary filesystem paths so
output-file behavior can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
file-output behavior of the preflight command-line interface.
"""

from argparse import Namespace
from pathlib import Path

from fontshow.core.cli_utils import set_cli_mode
from fontshow.preflight.__main__ import run_preflight_cli
from fontshow.preflight.model import CheckResult, PreflightResult, Severity


def test_preflight_output_writes_file(tmp_path, capsys):
    """
    Verify that the preflight CLI writes the rendered report to the output file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the output report path.
    capsys : pytest.CaptureFixture[str]
        Capture fixture used to inspect CLI stdout.

    Returns
    -------
    None
    """
    set_cli_mode(False, False)

    out_path = tmp_path / "preflight_report.txt"
    args = Namespace(output=out_path, quiet=False, verbose=False)

    def fake_run_preflight():
        """
        Return a deterministic one-warning preflight result for file-output testing.

        Returns
        -------
        PreflightResult
            Minimal preflight result containing a single warning entry.
        """
        return PreflightResult(
            [
                CheckResult(
                    check_id="unit-test",
                    severity=Severity.WARN,
                    message="hello",
                )
            ]
        )

    code = run_preflight_cli(args=args, run_preflight_fn=fake_run_preflight)

    captured = capsys.readouterr().out
    assert code == 0
    assert "Preflight passed." in captured

    text = Path(out_path).read_text(encoding="utf-8")
    assert "[WARN]" in text
    assert "unit-test" in text
    assert "hello" in text
