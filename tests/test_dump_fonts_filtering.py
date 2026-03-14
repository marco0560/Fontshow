"""
Verify filtering behavior of the dump-fonts command.

Responsibilities
----------------
- Ensure non-OpenType fonts are excluded from dump-fonts output.
- Verify filtering logic independent of the system font installation.

Design principles
-----------------
Tests mock the font discovery layer so that filtering behavior can be
verified deterministically without relying on actual system fonts.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the filtering rules applied by the dump-fonts CLI command.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from fontshow.cli.dump_fonts import run_dump_fonts


def test_dump_fonts_excludes_non_opentype(tmp_path, monkeypatch):
    """
    Ensure that dump-fonts excludes non-OpenType fonts
    without depending on the system font installation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the emitted inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery and extraction helpers.

    Returns
    -------
    None
    """
    # --- Mock font discovery ---
    fake_fonts = [
        Path("/fake/font-valid.ttf"),
        Path("/fake/font-bitmap.pcf"),
    ]

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: fake_fonts,
    )

    # --- Mock fonttools extraction ---
    def fake_fonttools_extract_all(path, **kwargs):
        """
        Emulate fontTools extraction for one valid OpenType face and one bitmap face.

        Parameters
        ----------
        path : pathlib.Path
            Discovered font path being inspected.
        **kwargs : object
            Ignored extraction options preserved for signature compatibility.

        Returns
        -------
        list[dict]
            Minimal extraction payload matching the expected dump-fonts contract.
        """
        if path.name.endswith(".ttf"):
            return [
                {
                    "ok": True,
                    "ttc_index": None,
                }
            ]

        return [
            {
                "ok": False,
                "error": "Not a TrueType or OpenType font",
                "ttc_index": None,
            }
        ]

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
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
    assert fonts[0]["path"].endswith("font-valid.ttf")


def test_parse_inventory_after_dump(tmp_path, monkeypatch):
    """
    Ensure parse-inventory succeeds after dump-fonts filtering.

    This test must not depend on system font installation or subprocess CLI
    calls (determinism + performance).

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for intermediate inventory files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery and extraction helpers.

    Returns
    -------
    None
    """

    # --- Mock font discovery ---
    fake_fonts = [
        Path("/fake/font-valid.ttf"),
        Path("/fake/font-bitmap.pcf"),
    ]

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: fake_fonts,
    )

    # --- Mock fonttools extraction ---
    def fake_fonttools_extract_all(path, **kwargs):
        """
        Emulate fontTools extraction for one valid OpenType face and one bitmap face.

        Parameters
        ----------
        path : pathlib.Path
            Discovered font path being inspected.
        **kwargs : object
            Ignored extraction options preserved for signature compatibility.

        Returns
        -------
        list[dict]
            Minimal extraction payload matching the expected dump-fonts contract.
        """
        if path.name.endswith(".ttf"):
            return [
                {
                    "ok": True,
                    "ttc_index": None,
                }
            ]

        return [
            {
                "ok": False,
                "error": "Not a TrueType or OpenType font",
                "ttc_index": None,
            }
        ]

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
        fake_fonttools_extract_all,
    )

    # --- Run dump-fonts in-process ---
    inventory = tmp_path / "fonts.json"

    dump_args = SimpleNamespace(
        output=inventory,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        verbose=False,
    )

    ret = run_dump_fonts(dump_args)
    assert ret == 0
    assert inventory.exists()

    # --- Run parse-inventory in-process ---
    from fontshow.cli.parse_inventory import run_parse_font_inventory

    output = tmp_path / "fonts_enriched.json"

    parse_args = SimpleNamespace(
        input=inventory,
        output=output,
        infer_level="medium",
        validate_inventory=False,
        strict_bcp47=False,
        verbose=False,
    )

    ret = run_parse_font_inventory(parse_args)
    assert ret == 0
    assert output.exists()


def test_dump_fonts_fails_instead_of_writing_non_schema_fallback(tmp_path, monkeypatch):
    """
    Ensure dump-fonts aborts when it cannot build a schema-1.2 descriptor.
    """
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: [Path("/fake/font-valid.ttf")],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
        lambda path, **kwargs: [{"ok": True, "ttc_index": None}],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.build_font_descriptor",
        lambda _ctx: (_ for _ in ()).throw(ValueError("broken descriptor")),
    )

    output = tmp_path / "fonts.json"
    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        verbose=False,
    )

    ret = run_dump_fonts(args)

    assert ret == 1
    assert not output.exists()
