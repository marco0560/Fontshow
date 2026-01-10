import pytest


@pytest.mark.parametrize("stub_parse_inventory", ["ok"], indirect=True)
def test_parse_inventory_success(cli_runner, stub_parse_inventory, tmp_path):
    inp = tmp_path / "in.json"
    outp = tmp_path / "out.json"
    inp.write_text('{"schema_version": "1.0", "fonts": []}')

    code, out = cli_runner(["fontshow", "parse-inventory", str(inp), "-o", str(outp)])

    assert code == 0


@pytest.mark.parametrize("stub_parse_inventory", ["fail"], indirect=True)
def test_parse_inventory_failure(cli_runner, stub_parse_inventory, tmp_path):
    inp = tmp_path / "in.json"
    inp.write_text("{}")

    code, out = cli_runner(["fontshow", "parse-inventory", str(inp)])

    assert code == 1
