def test_quiet_produces_no_output(cli_runner, stub_preflight_ok):
    code, out = cli_runner(["fontshow", "preflight", "--quiet"])

    assert out == ""
    assert code == 0


def test_default_prints_summary(cli_runner, stub_preflight_ok):
    code, out = cli_runner(["fontshow", "preflight"])

    assert "Preflight passed." in out
    assert code == 0


def test_preflight_failure_propagates(cli_runner, stub_preflight_fail):
    code, out = cli_runner(["fontshow", "preflight"])

    assert "Preflight failed." in out
    assert code == 1
