"""
Exercise inventory I/O helper branches.

Responsibilities
----------------
- Cover structural validation and path normalization helpers.
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
    """
    fonts = [{"family": "Alpha"}]

    assert io._validate_fonts_container({"fonts": fonts}) == fonts
    assert io._validate_fonts_container({"fonts": "nope"}) is None


def test_normalize_inventory_paths_sets_identity_file_only_when_missing():
    """
    Ensure path normalization is idempotent and ignores malformed identities.
    """
    inventory = {
        "fonts": [
            {"path": "/tmp/alpha.ttf", "identity": {}},
            {"path": "/tmp/beta.ttf", "identity": {"file": "/existing.ttf"}},
            {"path": "/tmp/gamma.ttf", "identity": None},
            {"identity": {}},
        ]
    }

    io._normalize_inventory_paths(inventory)

    assert inventory["fonts"][0]["identity"]["file"] == "/tmp/alpha.ttf"
    assert inventory["fonts"][1]["identity"]["file"] == "/existing.ttf"
    assert inventory["fonts"][3]["identity"] == {}


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
    """
    assert io._validate_fonts_structure(inventory) == expected


def test_load_font_inventory_raises_runtime_error_for_invalid_result(
    monkeypatch, tmp_path
):
    """
    Ensure the public loader preserves its exception-based contract.
    """
    monkeypatch.setattr(
        io, "_load_inventory", lambda _path, require_platform=False: (1, [])
    )

    with pytest.raises(RuntimeError, match="Invalid or incompatible inventory"):
        io.load_font_inventory(tmp_path / "inventory.json")


def test_load_inventory_rejects_non_mapping_metadata(tmp_path, monkeypatch):
    """
    Ensure invalid ``metadata`` shapes are rejected early.
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
        "Inventory missing required metadata.run_environment (schema v1.2)"
    ]


def test_load_inventory_rejects_platform_mismatch(tmp_path, monkeypatch):
    """
    Ensure platform mismatches are logged and converted into rc=1.
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
    Ensure non-platform mode skips run-environment enforcement and normalizes paths.
    """
    data = minimal_inventory_v12()
    data["fonts"][0]["identity"] = {}
    del data["metadata"]["run_environment"]
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
    assert fonts[0]["identity"]["file"] == fonts[0]["path"]
    assert oks == [f"Inventory loaded: {path} (1 fonts)"]
