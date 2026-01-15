import pytest


@pytest.mark.parametrize("stub_parse_inventory", ["ok"], indirect=True)
def test_parse_inventory_success(cli_runner, stub_parse_inventory, tmp_path):
    inp = tmp_path / "in.json"
    outp = tmp_path / "out.json"
    inp.write_text('{"schema_version": "1.0", "fonts": []}')

    code, out = cli_runner(["fontshow", "parse-inventory", str(inp), "-o", str(outp)])

    assert code == 0


@pytest.mark.parametrize(
    "stub_parse_inventory, expected_code",
    [
        ("fail", 2),  # errore atteso
        ("boom", 2),  # errore interno
    ],
    indirect=["stub_parse_inventory"],
)
def test_parse_inventory_failure(cli_runner, stub_parse_inventory, expected_code):
    code, out = cli_runner(["fontshow", "parse-inventory", "--input", "inv.json"])
    assert code == expected_code
