import pytest


@pytest.mark.parametrize("stub_dump_fonts", ["ok"], indirect=True)
def test_dump_fonts_success(cli_runner, stub_dump_fonts, tmp_path):
    code, out = cli_runner(["fontshow", "dump-fonts", "-o", str(tmp_path / "inv.json")])

    assert code == 0


@pytest.mark.parametrize("stub_dump_fonts", ["fail"], indirect=True)
def test_dump_fonts_failure(cli_runner, stub_dump_fonts, tmp_path):
    code, out = cli_runner(["fontshow", "dump-fonts", "-o", str(tmp_path / "inv.json")])

    assert code == 1
