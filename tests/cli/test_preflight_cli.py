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
