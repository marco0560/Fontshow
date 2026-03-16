"""
Exercise inventory I/O helper branches.

Responsibilities
----------------
- Cover structural validation and strict schema-1.2 inventory loading.
- Verify inventory loading error conversion and semantic/platform gates.
- Keep tests deterministic by patching platform and semantic validators.
"""

from __future__ import annotations

import json

import pytest

from fontshow.core.types import Severity
from fontshow.inventory import io
from tests.helpers import minimal_inventory_v12


def test_validate_fonts_container_accepts_only_lists():
    """
    Ensure the helper returns the list unchanged and rejects non-lists.

    Returns
    -------
    None
    """
    fonts = [{"family": "Alpha"}]

    assert io._validate_fonts_container({"fonts": fonts}) == fonts
    assert io._validate_fonts_container({"fonts": "nope"}) is None


@pytest.mark.parametrize(
    ("inventory", "expected"),
    [
        ({}, (False, [])),
        ({"fonts": "bad"}, (False, [])),
        ({"fonts": []}, (False, [])),
        ({"fonts": [object()]}, (False, [])),
        ({"fonts": [{"family": "Alpha"}]}, (True, [{"family": "Alpha"}])),
    ],
)
def test_validate_fonts_structure_covers_boundary_shapes(inventory, expected):
    """
    Ensure malformed and valid ``fonts`` containers are classified correctly.

    Parameters
    ----------
    inventory : dict[str, object]
        Candidate inventory payload passed to the helper.
    expected : tuple[bool, list[dict[str, object]]]
        Expected validity flag and normalized font list.

    Returns
    -------
    None
    """
    assert io._validate_fonts_structure(inventory) == expected


def test_load_font_inventory_raises_runtime_error_for_invalid_result(
    monkeypatch, tmp_path
):
    """
    Ensure the public loader preserves its exception-based contract.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the lower-level loader.
    tmp_path : pathlib.Path
        Temporary directory fixture used to build a dummy input path.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        io, "_load_inventory", lambda _path, require_platform=False: (1, [])
    )

    with pytest.raises(RuntimeError, match="Invalid or incompatible inventory"):
        io.load_font_inventory(tmp_path / "inventory.json")


def test_load_inventory_rejects_non_mapping_metadata(tmp_path, monkeypatch):
    """
    Ensure invalid ``metadata`` shapes are rejected early.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture emitted error messages.

    Returns
    -------
    None
    """
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({"metadata": 1}), encoding="utf-8")
    errors: list[str] = []

    monkeypatch.setattr(io, "log_err", errors.append)

    rc, fonts = io._load_inventory(path)

    assert (rc, fonts) == (1, [])
    assert errors == ["Invalid inventory JSON: expected 'metadata' to be an object."]


def test_load_inventory_rejects_missing_run_environment_when_required(
    tmp_path, monkeypatch
):
    """
    Ensure strict platform mode requires ``metadata.run_environment``.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture emitted error messages.

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()
    del data["metadata"]["run_environment"]
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    errors: list[str] = []

    monkeypatch.setattr(io, "log_err", errors.append)

    rc, fonts = io._load_inventory(path, require_platform=True)

    assert (rc, fonts) == (1, [])
    assert errors == [
        "failed to load inventory: Inventory schema validation failed: 'run_environment' is a required property"
    ]


def test_load_inventory_rejects_legacy_schema_version(tmp_path, monkeypatch):
    """
    Ensure legacy schema versions are rejected immediately.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture emitted error messages.

    Returns
    -------
    None
    """
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps({"metadata": {"schema_version": "1.0"}, "fonts": []}),
        encoding="utf-8",
    )
    errors: list[str] = []

    monkeypatch.setattr(io, "log_err", errors.append)

    rc, fonts = io._load_inventory(path, require_platform=False)

    assert (rc, fonts) == (1, [])
    assert errors == ["Unsupported inventory schema_version: '1.0' (required 1.2)"]


def test_load_inventory_rejects_mixed_shape_entry(tmp_path, monkeypatch):
    """
    Ensure entries carrying legacy-only fields are rejected by strict loading.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture emitted error messages.

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()
    data["fonts"][0]["identity"] = {"file": data["fonts"][0]["path"]}
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    errors: list[str] = []

    monkeypatch.setattr(io, "log_err", errors.append)

    rc, fonts = io._load_inventory(path, require_platform=False)

    assert (rc, fonts) == (1, [])
    assert len(errors) == 1
    assert errors[0].startswith(
        "failed to load inventory: Inventory schema validation failed:"
    )


def test_load_inventory_rejects_platform_mismatch(tmp_path, monkeypatch):
    """
    Ensure platform mismatches are logged and converted into rc=1.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace platform enforcement and capture logs.

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    errors: list[str] = []

    monkeypatch.setattr(
        io, "_enforce_platform", lambda _env: (False, ["os", "machine"])
    )
    monkeypatch.setattr(io, "log_err", errors.append)

    rc, fonts = io._load_inventory(path, require_platform=True)

    assert (rc, fonts) == (1, [])
    assert errors == ["Inventory platform mismatch: os, machine"]


def test_load_inventory_reports_semantic_errors(tmp_path, monkeypatch):
    """
    Ensure semantic validation failures surface only warning/error messages.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace validation helpers and capture logs.

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    errors: list[str] = []

    monkeypatch.setattr(io, "_enforce_platform", lambda _env: (True, []))
    monkeypatch.setattr(io, "normalize_loaded_enums", lambda inventory: None)
    monkeypatch.setattr(
        io,
        "enforce_semantic_validation",
        lambda _inventory, strict=True: (
            False,
            [
                {"severity": Severity.INFO, "message": "ignore info"},
                {"severity": Severity.WARN, "message": "warn me"},
                {"severity": Severity.ERROR, "message": "break me"},
            ],
        ),
    )
    monkeypatch.setattr(io, "log_err", errors.append)
    monkeypatch.setattr(io, "log_trace_cat", lambda *_args, **_kwargs: None)

    rc, fonts = io._load_inventory(path, require_platform=True)

    assert (rc, fonts) == (1, [])
    assert errors == ["warn me", "break me"]


def test_load_inventory_returns_fonts_when_platform_check_is_disabled(
    tmp_path, monkeypatch
):
    """
    Ensure non-platform mode skips platform matching for valid schema-1.2 inventories.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the test inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace validation helpers and capture success logs.

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    oks: list[str] = []

    monkeypatch.setattr(io, "normalize_loaded_enums", lambda inventory: None)
    monkeypatch.setattr(
        io, "enforce_semantic_validation", lambda _inventory, strict=True: (True, [])
    )
    monkeypatch.setattr(io, "log_trace_cat", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(io, "log_ok", oks.append)

    rc, fonts = io._load_inventory(path, require_platform=False)

    assert rc == 0
    assert fonts[0]["path"] == data["fonts"][0]["path"]
    assert oks == [f"Inventory loaded: {path} (1 fonts)"]
