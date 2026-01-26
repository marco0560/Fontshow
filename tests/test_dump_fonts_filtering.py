import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from fontshow.dump_fonts import run_dump_fonts


def test_dump_fonts_excludes_non_opentype(tmp_path, monkeypatch):
    """
    Ensure that dump-fonts excludes non-OpenType fonts
    without depending on the system font installation.
    """
    # --- Mock font discovery ---
    fake_fonts = [
        Path("/fake/font-valid.ttf"),
        Path("/fake/font-bitmap.pcf"),
    ]

    monkeypatch.setattr(
        "fontshow.dump_fonts.get_installed_font_files",
        lambda: fake_fonts,
    )

    # --- Mock fonttools extraction ---
    def fake_fonttools_extract_all(path, **kwargs):
        if path.name.endswith(".ttf"):
            return [
                {
                    "ok": True,
                    "ttc_index": None,
                }
            ]
        else:
            return [
                {
                    "ok": False,
                    "error": "Not a TrueType or OpenType font",
                    "ttc_index": None,
                }
            ]

    monkeypatch.setattr(
        "fontshow.dump_fonts.fonttools_extract_all",
        fake_fonttools_extract_all,
    )

    # --- Prepare args object ---
    output = tmp_path / "fonts.json"

    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        verbose=False,
    )

    # --- Run ---
    ret = run_dump_fonts(args)

    assert ret == 0
    assert output.exists()

    data = json.loads(output.read_text())
    fonts = data.get("fonts", [])

    # --- Assertions ---
    assert len(fonts) == 1
    assert fonts[0]["identity"]["file"].endswith("font-valid.ttf")


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
