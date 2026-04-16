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
from fontshow.core.cli_utils import set_cli_mode


def test_dump_fonts_excludes_non_opentype(tmp_path, monkeypatch):
    """
    Ensure that dump-fonts excludes non-OpenType fonts without depending on the system font installation.

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

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the output inventory path.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery, extraction, and descriptor building.

    Returns
    -------
    None
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


def test_dump_fonts_paths_mode_does_not_use_system_discovery(tmp_path, monkeypatch):
    """
    Ensure explicit path mode disables system discovery fallback.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for input roots and output.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery helpers.

    Returns
    -------
    None
    """
    root = tmp_path / "fonts"
    root.mkdir()

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_font_files_from_paths",
        lambda _paths: [],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: (_ for _ in ()).throw(AssertionError("system discovery called")),
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_last_discovery_stats",
        lambda: {"skipped_legacy_extension": 0},
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fc_query_extract_many",
        lambda *_args, **_kwargs: {},
    )

    output = tmp_path / "fonts.json"
    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        no_loadability=True,
        paths=[root],
        verbose=False,
    )

    ret = run_dump_fonts(args)

    assert ret == 0
    assert json.loads(output.read_text())["fonts"] == []


def test_dump_fonts_paths_mode_fails_invalid_root(tmp_path, monkeypatch):
    """
    Ensure invalid controlled discovery roots abort without writing output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for input roots and output.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace system discovery.

    Returns
    -------
    None
    """
    missing = tmp_path / "missing"

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: (_ for _ in ()).throw(AssertionError("system discovery called")),
    )

    output = tmp_path / "fonts.json"
    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        no_loadability=True,
        paths=[missing],
        verbose=False,
    )

    ret = run_dump_fonts(args)

    assert ret == 1
    assert not output.exists()


def test_dump_fonts_verbose_reports_style_leak_details(tmp_path, monkeypatch):
    """
    Ensure style-leak details are attached only via the verbose log variant.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the output inventory path.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery, extraction, and logging helpers.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: [Path("/fake/arial-black.ttf")],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_last_discovery_stats",
        lambda: {"skipped_legacy_extension": 0},
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fc_query_extract_many",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
        lambda path, **kwargs: [{"ok": True, "ttc_index": None}],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.build_font_descriptor",
        lambda _ctx: {
            "path": "/fake/arial-black.ttf",
            "family": "Arial Black",
            "subfamily": "Regular",
            "typographic_subfamily": "Regular",
            "full_name": "Arial Black Regular",
            "postscript_name": "ArialBlack-Regular",
            "version_string": "1.0",
            "unique_font_id": "arial-black-regular-1.0",
            "units_per_em": 1000,
            "ascent": 800,
            "descent": -200,
            "weight_class": 400,
            "width_class": 5,
            "italic_angle": 0.0,
            "is_fixed_pitch": False,
            "glyph_count": 1,
            "coverage": {},
            "inference": {},
            "charset": {},
            "sample_text": {"source": "font", "text": "A"},
            "specimen_text": "A",
            "specimen_strategy": "cmap",
            "specimen_glyph_count": 1,
        },
    )

    infos: list[tuple[str, str | None]] = []

    def fake_log_info(message, verbose=None, **kwargs):
        infos.append((message, verbose))

    monkeypatch.setattr("fontshow.cli.dump_fonts.log_info", fake_log_info)
    set_cli_mode(False, True)

    output = tmp_path / "fonts.json"
    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        verbose=True,
    )

    ret = run_dump_fonts(args)

    assert ret == 0
    detail = next(
        verbose
        for message, verbose in infos
        if message == "1 entries flagged for possible style leak"
    )
    assert detail is not None
    assert "Possible style-leak entries:" in detail
    assert (
        "/fake/arial-black.ttf | Arial Black | Regular | "
        "weight_class=400 | width_class=5 | italic_angle=0.0"
    ) in detail
