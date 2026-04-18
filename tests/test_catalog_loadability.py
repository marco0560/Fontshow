"""
Exercise catalog loadability filtering helpers.

Responsibilities
----------------
- Verify candidate selection only targets real supported font files.
- Ensure catalog filtering consumes persisted LuaLaTeX loadability only.
- Ensure trusted persisted failures are reported deterministically.
"""

from __future__ import annotations

import pytest

from fontshow.catalog import loadability


def _metadata(fingerprint: str = "fp-1") -> dict[str, object]:
    """
    Build current LuaLaTeX validation metadata for catalog tests.

    Parameters
    ----------
    fingerprint : str, optional
        Runtime fingerprint exposed to the catalog loadability gate.

    Returns
    -------
    dict[str, object]
        Minimal metadata block accepted by persisted loadability checks.
    """
    return {
        "attempted": True,
        "runtime_fingerprint": fingerprint,
    }


def _persisted(loadable: bool, *, fingerprint: str = "fp-1") -> dict[str, object]:
    """
    Build a persisted per-font LuaLaTeX loadability block.

    Parameters
    ----------
    loadable : bool
        Persisted loadability result.
    fingerprint : str, optional
        Runtime fingerprint stored with the persisted result.

    Returns
    -------
    dict[str, object]
        Schema-shaped ``loadability.lualatex`` payload.
    """
    return {
        "attempted": True,
        "loadable": loadable,
        "reason": None if loadable else "subset-empty",
        "runtime_fingerprint": fingerprint,
        "probe_input": "U+0041",
        "render_variants": [],
    }


def _font(path, family: str, *, loadable: bool | None = True) -> dict[str, object]:
    """
    Build a catalog font entry for loadability filtering tests.

    Parameters
    ----------
    path : pathlib.Path
        Font path to store in the entry.
    family : str
        Font family label.
    loadable : bool | None, optional
        Persisted loadability result. If None, omit persisted state.

    Returns
    -------
    dict[str, object]
        Catalog font entry.
    """
    font: dict[str, object] = {
        "path": str(path),
        "family": family,
        "full_name": f"{family} Regular",
        "unique_font_id": f"{family.lower()}-1",
    }
    if loadable is not None:
        font["loadability"] = {"lualatex": _persisted(loadable)}
    return font


def test_is_validation_candidate_requires_existing_supported_font_file(tmp_path):
    """
    Ensure validation only targets existing supported font files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage test font files.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")

    assert loadability._is_validation_candidate({"path": str(font_path)}) is True
    assert (
        loadability._is_validation_candidate({"path": str(tmp_path / "Missing.ttf")})
        is False
    )
    assert (
        loadability._is_validation_candidate({"path": str(tmp_path / "Alpha.txt")})
        is False
    )
    assert loadability._is_validation_candidate({"family": "ETbb", "path": ""}) is False


def test_filter_loadable_catalog_fonts_rejects_missing_persisted_state(
    monkeypatch, tmp_path
):
    """
    Ensure catalog filtering rejects loadability-incomplete inventories.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace current validation metadata.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the test font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")
    monkeypatch.setattr(loadability, "_current_lualatex_validation_metadata", _metadata)

    with pytest.raises(ValueError, match="not loadability-ready"):
        loadability.filter_loadable_catalog_fonts(
            [_font(font_path, "Alpha", loadable=None)]
        )


def test_filter_loadable_catalog_fonts_uses_trusted_persisted_pass(
    monkeypatch, tmp_path
):
    """
    Ensure trusted persisted loadability keeps loadable fonts.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace current validation metadata.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the test font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")
    monkeypatch.setattr(loadability, "_current_lualatex_validation_metadata", _metadata)

    fonts = [_font(font_path, "Alpha", loadable=True)]

    assert loadability.filter_loadable_catalog_fonts(fonts) == fonts


def test_filter_loadable_catalog_fonts_uses_inventory_validation_metadata(
    monkeypatch, tmp_path
):
    """
    Ensure catalog filtering trusts inventory-level attempted state.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace current runtime metadata.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the test font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")
    monkeypatch.setattr(
        loadability,
        "_current_lualatex_validation_metadata",
        lambda: {"attempted": False, "runtime_fingerprint": "fp-1"},
    )

    fonts = [_font(font_path, "Alpha", loadable=True)]

    result = loadability.filter_loadable_catalog_fonts_with_report(
        fonts,
        validation_metadata=_metadata("fp-1"),
    )

    assert result.kept == fonts
    assert result.excluded == []


def test_filter_loadable_catalog_fonts_uses_trusted_persisted_failure(
    monkeypatch, tmp_path
):
    """
    Ensure trusted persisted failures are skipped without runtime probing.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace current validation metadata and logging.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the test font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Broken.ttf"
    font_path.write_bytes(b"")
    warnings: list[str] = []

    monkeypatch.setattr(loadability, "_current_lualatex_validation_metadata", _metadata)
    monkeypatch.setattr(loadability, "log_warn", warnings.append)

    fonts = [_font(font_path, "Broken", loadable=False)]

    assert loadability.filter_loadable_catalog_fonts(fonts) == []
    assert warnings == [
        f"Font skipped: Broken Regular | path={font_path} | id=broken-1",
        "Reason: LuaLaTeX load failure",
        "Detail: subset-empty",
    ]


def test_filter_loadable_catalog_fonts_rejects_stale_persisted_state(
    monkeypatch, tmp_path
):
    """
    Ensure stale persisted loadability is a hard catalog input error.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace current validation metadata.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the test font file.

    Returns
    -------
    None
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")
    monkeypatch.setattr(
        loadability,
        "_current_lualatex_validation_metadata",
        lambda: _metadata("fp-new"),
    )
    font = _font(font_path, "Alpha", loadable=True)
    font["loadability"] = {"lualatex": _persisted(True, fingerprint="fp-old")}

    with pytest.raises(ValueError, match="runtime_fingerprint mismatch"):
        loadability.filter_loadable_catalog_fonts([font])


def test_filter_loadable_catalog_fonts_skips_only_persisted_failed_candidates(
    monkeypatch, tmp_path
):
    """
    Ensure unloadable fonts are removed while non-candidates are preserved.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace current validation metadata and logging.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the test font files.

    Returns
    -------
    None
    """
    good_path = tmp_path / "Alpha.ttf"
    bad_path = tmp_path / "Broken.ttf"
    good_path.write_bytes(b"")
    bad_path.write_bytes(b"")
    warnings: list[str] = []

    monkeypatch.setattr(loadability, "_current_lualatex_validation_metadata", _metadata)
    monkeypatch.setattr(loadability, "log_warn", warnings.append)

    fonts = [
        _font(good_path, "Alpha", loadable=True),
        _font(bad_path, "Broken", loadable=False),
        {
            "path": str(tmp_path / "missing.ttf"),
            "family": "Missing",
            "unique_font_id": "missing-1",
        },
    ]

    kept = loadability.filter_loadable_catalog_fonts(fonts)

    assert kept == [fonts[0], fonts[2]]
    assert warnings == [
        f"Font skipped: Broken Regular | path={bad_path} | id=broken-1",
        "Reason: LuaLaTeX load failure",
        "Detail: subset-empty",
    ]
