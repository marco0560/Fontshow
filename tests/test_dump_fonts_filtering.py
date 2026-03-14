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

import pytest

from fontshow.cli.dump_fonts import run_dump_fonts
from fontshow.platform.font_discovery import (
    _has_legacy_font_extension,
    get_installed_font_files_linux,
    get_installed_font_files_windows,
)


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


def test_linux_discovery_skips_legacy_extensions(tmp_path, monkeypatch):
    """
    Ensure Linux font discovery excludes legacy formats before extraction.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to create deterministic fake files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the Fontconfig command execution.

    Returns
    -------
    None
    """
    modern = tmp_path / "Modern-Regular.ttf"
    legacy_bitmap = tmp_path / "LegacyBitmap.PCF.GZ"
    legacy_type1 = tmp_path / "LegacyType1.PFB"

    modern.write_bytes(b"")
    legacy_bitmap.write_bytes(b"")
    legacy_type1.write_bytes(b"")

    stdout = "\n".join([str(modern), str(legacy_bitmap), str(legacy_type1)])

    monkeypatch.setattr(
        "fontshow.platform.font_discovery.run_command",
        lambda _cmd: SimpleNamespace(returncode=0, stdout=stdout),
    )

    discovered = get_installed_font_files_linux()

    assert discovered == [modern.resolve()]


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("legacy.pfb", True),
        ("legacy.PFA", True),
        ("legacy.T1", True),
        ("legacy.pcf", True),
        ("legacy.PCF.GZ", True),
        ("legacy.bdf", True),
        ("modern.ttf", False),
        ("modern.otf", False),
        ("modern.ttc", False),
        ("modern.otc", False),
    ],
)
def test_legacy_extension_policy(filename, expected):
    """
    Verify the legacy-extension matcher covers all blocked formats only.

    Parameters
    ----------
    filename : str
        Parameterized candidate filename under test.
    expected : bool
        Expected classifier result for the candidate filename.

    Returns
    -------
    None
    """
    assert _has_legacy_font_extension(Path(filename)) is expected


def test_linux_discovery_keeps_supported_modern_formats(tmp_path, monkeypatch):
    """
    Ensure Linux discovery preserves all supported modern container formats.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to create deterministic fake files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the Fontconfig command execution.

    Returns
    -------
    None
    """
    modern_paths = [
        tmp_path / "Family-Regular.ttf",
        tmp_path / "Family-Italic.OTF",
        tmp_path / "Collection.ttc",
        tmp_path / "Collection.OTC",
    ]
    legacy = tmp_path / "Bitmap.bdf"

    for path in [*modern_paths, legacy]:
        path.write_bytes(b"")

    stdout = "\n".join(str(path) for path in [*modern_paths, legacy])

    monkeypatch.setattr(
        "fontshow.platform.font_discovery.run_command",
        lambda _cmd: SimpleNamespace(returncode=0, stdout=stdout),
    )

    discovered = get_installed_font_files_linux()

    assert discovered == sorted(path.resolve() for path in modern_paths)


def test_windows_discovery_skips_legacy_extensions(tmp_path, monkeypatch):
    """
    Ensure Windows directory scanning excludes legacy extensions.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to create deterministic fake files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the known Windows font directories.

    Returns
    -------
    None
    """
    modern_paths = [
        tmp_path / "SegoeUI.ttf",
        tmp_path / "Cambria.OTF",
        tmp_path / "Noto.ttc",
        tmp_path / "Noto.otc",
        tmp_path / "Webfont.woff2",
    ]
    ignored_paths = [
        tmp_path / "Legacy.pfb",
        tmp_path / "Bitmap.PCF.GZ",
    ]

    for path in [*modern_paths, *ignored_paths]:
        path.write_bytes(b"")

    monkeypatch.setattr(
        "fontshow.platform.font_discovery._windows_font_dirs",
        lambda: [tmp_path],
    )

    discovered = get_installed_font_files_windows()

    assert discovered == sorted(path.resolve() for path in modern_paths)


def test_dump_fonts_reports_skip_counters_without_repeated_unloadable_warnings(
    tmp_path, monkeypatch
):
    """
    Ensure dump-fonts reports skip counters and deduplicates unloadable warnings.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the emitted inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery, extraction, and logging helpers.

    Returns
    -------
    None
    """
    font_path = tmp_path / "BrokenCollection.ttc"
    font_path.write_bytes(b"")

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: [font_path],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_last_discovery_stats",
        lambda: {"skipped_legacy_extension": 3},
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fc_query_extract_many",
        lambda *_args, **_kwargs: {},
    )

    def fake_fonttools_extract_all(path, **kwargs):
        """
        Emulate two unloadable faces from the same discovered font file.

        Parameters
        ----------
        path : pathlib.Path
            Discovered font path being inspected.
        **kwargs : object
            Ignored extraction options preserved for signature compatibility.

        Returns
        -------
        list[dict]
            Minimal extraction payload with repeated unloadable faces.
        """
        return [
            {
                "ok": True,
                "container": "TTC",
                "ttc_index": 0,
                "tables": ["name"],
            },
            {
                "ok": True,
                "container": "TTC",
                "ttc_index": 1,
                "tables": ["name"],
            },
        ]

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
        fake_fonttools_extract_all,
    )

    warnings: list[str] = []
    infos: list[tuple[str, dict | None]] = []

    def fake_log_warn(message, **kwargs):
        warnings.append(message)

    def fake_log_info(message, **kwargs):
        infos.append((message, kwargs.get("extra")))

    monkeypatch.setattr("fontshow.cli.dump_fonts.log_warn", fake_log_warn)
    monkeypatch.setattr("fontshow.cli.dump_fonts.log_info", fake_log_info)

    output = tmp_path / "fonts.json"
    args = SimpleNamespace(
        output=output,
        cache_dir=tmp_path,
        include_fc_charset=False,
        no_cache=True,
        verbose=False,
    )

    ret = run_dump_fonts(args)

    assert ret == 0
    assert warnings == [f"skipping structurally-unloadable font: {font_path}"]

    summary = next(extra for message, extra in infos if message == "dump-fonts summary")
    assert summary == {
        "total_faces_seen": 2,
        "total_font_files": 1,
        "total_fonts": 0,
        "skipped_legacy_extension": 3,
        "skipped_structurally_unloadable": 2,
        "skipped_non_opentype_faces": 0,
        "style_leak_suspected": 0,
    }
