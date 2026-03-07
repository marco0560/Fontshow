from argparse import Namespace
from pathlib import Path

from fontshow.core.cli_utils import set_cli_mode
from fontshow.preflight.__main__ import _run_preflight_cli
from fontshow.preflight.model import CheckResult, PreflightResult, Severity


def test_preflight_output_writes_file(tmp_path, capsys):
    set_cli_mode(False, False)

    out_path = tmp_path / "preflight_report.txt"
    args = Namespace(output=out_path, quiet=False, verbose=False)

    def fake_run_preflight():
        return PreflightResult(
            [
                CheckResult(
                    check_id="unit-test",
                    severity=Severity.WARN,
                    message="hello",
                )
            ]
        )

    code = _run_preflight_cli(args=args, run_preflight_fn=fake_run_preflight)

    captured = capsys.readouterr().out
    assert code == 0
    assert "Preflight passed." in captured

    text = Path(out_path).read_text(encoding="utf-8")
    assert "[WARN]" in text
    assert "unit-test" in text
    assert "hello" in text
