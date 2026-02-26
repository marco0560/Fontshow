import pytest


@pytest.mark.parametrize("stub_create_catalog", ["ok"], indirect=True)
def test_create_catalog_success(cli_runner, stub_create_catalog, tmp_path):
    code, out = cli_runner(["fontshow", "create-catalog", "--inventory", "inv.json"])

    assert code == 0


@pytest.mark.parametrize("stub_create_catalog", ["ok"], indirect=True)
def test_create_catalog_accepts_output_option(
    cli_runner, stub_create_catalog, tmp_path
):
    out_tex = tmp_path / "out.tex"
    code, out = cli_runner(
        ["fontshow", "create-catalog", "--inventory", "inv.json", "-o", str(out_tex)]
    )

    assert code == 0


@pytest.mark.parametrize(
    "stub_create_catalog, expected_code",
    [
        ("fail", 1),  # errore atteso
        ("boom", 2),  # errore interno (eccezione)
    ],
    indirect=["stub_create_catalog"],
)
def test_create_catalog_failure(cli_runner, stub_create_catalog, expected_code):
    code, out = cli_runner(["fontshow", "create-catalog", "--inventory", "inv.json"])
    assert code == expected_code
