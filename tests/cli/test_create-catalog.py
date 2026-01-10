import pytest


@pytest.mark.parametrize("stub_create_catalog", ["ok"], indirect=True)
def test_create_catalog_success(cli_runner, stub_create_catalog, tmp_path):
    code, out = cli_runner(["fontshow", "create-catalog", "--inventory", "inv.json"])

    assert code == 0


@pytest.mark.parametrize("stub_create_catalog", ["fail"], indirect=True)
def test_create_catalog_failure(cli_runner, stub_create_catalog):
    code, out = cli_runner(["fontshow", "create-catalog", "--inventory", "inv.json"])

    assert code == 1
