import json
import subprocess


def test_dump_fonts_excludes_non_opentype(tmp_path):
    """
    Ensure that dump-fonts does not emit bitmap / non-OpenType fonts.
    """

    output = tmp_path / "fonts.json"

    result = subprocess.run(
        [
            "fontshow",
            "dump-fonts",
            "-o",
            str(output),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output.exists()

    data = json.loads(output.read_text())
    fonts = data.get("fonts", [])

    # No font entry should have UNKNOWN container
    for font in fonts:
        fmt = font.get("format", {})
        assert fmt.get("container") != "UNKNOWN"

        src = font.get("source", {}).get("fonttools", {})
        assert src.get("ok") is not False


def test_parse_inventory_after_dump(tmp_path):
    """
    Ensure parse-inventory succeeds after dump-fonts filtering.
    """

    inventory = tmp_path / "fonts.json"

    dump = subprocess.run(
        [
            "fontshow",
            "dump-fonts",
            "-o",
            str(inventory),
        ],
        capture_output=True,
        text=True,
    )

    assert dump.returncode == 0
    assert inventory.exists()

    parse = subprocess.run(
        [
            "fontshow",
            "parse-inventory",
            str(inventory),
        ],
        capture_output=True,
        text=True,
    )

    assert parse.returncode == 0
