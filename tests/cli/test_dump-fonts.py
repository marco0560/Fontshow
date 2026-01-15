import pytest


@pytest.mark.parametrize("stub_dump_fonts", ["ok"], indirect=True)
def test_dump_fonts_success(cli_runner, stub_dump_fonts, tmp_path):
    code, out = cli_runner(["fontshow", "dump-fonts", "-o", str(tmp_path / "inv.json")])

    assert code == 0


@pytest.mark.parametrize(
    "stub_dump_fonts, expected_code",
    [
        ("fail", 2),  # errore atteso
        ("boom", 2),  # errore interno
    ],
    indirect=["stub_dump_fonts"],
)
def test_dump_fonts_failure(cli_runner, stub_dump_fonts, expected_code):
    code, out = cli_runner(["fontshow", "dump-fonts", "--output", "out.json"])
    assert code == expected_code
