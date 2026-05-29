"""
Exercise parse-inventory runtime-only branches.

Responsibilities
----------------
- Verify reporting-only modes exit without writing output.
- Ensure missing-language coverage listing is deterministic.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from fontshow.cli import parse_inventory


def test_run_parse_inventory_lists_missing_language_coverage_summary_only(
    monkeypatch, tmp_path
):
    """
    Ensure the reporting mode lists only fonts with empty coverage.languages.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace metadata, validation, and logging helpers.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage input and output files.

    Returns
    -------
    None
    """
    input_file = tmp_path / "inventory.json"
    output_file = tmp_path / "out.json"
    infos: list[str] = []

    inventory = {
        "metadata": {
            "schema_version": "1.5",
            "run_environment": {"os": "x", "machine": "y", "execution_context": "z"},
        },
        "fonts": [
            {
                "family": "Alpha",
                "path": "/fonts/a.ttf",
                "coverage": {"languages": []},
            },
            {
                "family": "Beta",
                "path": "/fonts/b.ttf",
                "coverage": {"languages": ["en"]},
            },
            {
                "family": "Gamma",
                "path": "/fonts/c.ttf",
                "coverage": {},
            },
        ],
    }
    input_file.write_text(json.dumps(inventory), encoding="utf-8")

    monkeypatch.setattr(
        parse_inventory,
        "collect_platform_metadata",
        lambda: inventory["metadata"]["run_environment"],
    )
    monkeypatch.setattr(
        parse_inventory, "_validate_inventory_schema_strict", lambda data: None
    )
    monkeypatch.setattr(
        parse_inventory, "_validate_fonts_container", lambda data: data["fonts"]
    )
    monkeypatch.setattr(parse_inventory, "log_info", infos.append)

    write_calls: list[tuple[object, object]] = []

    args = SimpleNamespace(
        input=input_file,
        output=output_file,
        infer_level="medium",
        validate_inventory=False,
        list_missing_language_coverage=True,
        show_all_missing_language_coverage=False,
        strict_bcp47=False,
        verbose=False,
    )

    rc = parse_inventory.run_parse_font_inventory(
        args,
        write_text_fn=lambda path, text: write_calls.append((path, text)),
    )

    assert rc == 0
    assert write_calls == []
    assert infos == ["Fonts with missing declared language coverage: 2"]


def test_run_parse_inventory_lists_all_missing_language_coverage_when_requested(
    monkeypatch, tmp_path
):
    """
    Ensure report mode expands to one line per font when explicitly requested.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace metadata, validation, and logging helpers.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage input and output files.

    Returns
    -------
    None
    """
    input_file = tmp_path / "inventory.json"
    output_file = tmp_path / "out.json"
    infos: list[str] = []

    inventory = {
        "metadata": {
            "schema_version": "1.5",
            "run_environment": {"os": "x", "machine": "y", "execution_context": "z"},
        },
        "fonts": [
            {
                "family": "Alpha",
                "path": "/fonts/a.ttf",
                "coverage": {"languages": []},
            },
            {
                "family": "Beta",
                "path": "/fonts/b.ttf",
                "coverage": {"languages": ["en"]},
            },
            {
                "family": "Gamma",
                "path": "/fonts/c.ttf",
                "coverage": {},
            },
        ],
    }
    input_file.write_text(json.dumps(inventory), encoding="utf-8")

    monkeypatch.setattr(
        parse_inventory,
        "collect_platform_metadata",
        lambda: inventory["metadata"]["run_environment"],
    )
    monkeypatch.setattr(
        parse_inventory, "_validate_inventory_schema_strict", lambda data: None
    )
    monkeypatch.setattr(
        parse_inventory, "_validate_fonts_container", lambda data: data["fonts"]
    )
    monkeypatch.setattr(parse_inventory, "log_info", infos.append)

    args = SimpleNamespace(
        input=input_file,
        output=output_file,
        infer_level="medium",
        validate_inventory=False,
        list_missing_language_coverage=True,
        show_all_missing_language_coverage=True,
        strict_bcp47=False,
        verbose=False,
    )

    rc = parse_inventory.run_parse_font_inventory(args)

    assert rc == 0
    assert infos == [
        "Fonts with missing declared language coverage: 2",
        "Alpha | /fonts/a.ttf",
        "Gamma | /fonts/c.ttf",
    ]


def test_run_parse_inventory_rejects_non_object_inventory(tmp_path, monkeypatch):
    """
    Ensure parse-inventory rejects non-object JSON input as a user error.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the input file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture user-facing error messages.

    Returns
    -------
    None
    """
    input_file = tmp_path / "inventory.json"
    output_file = tmp_path / "out.json"
    errors: list[str] = []

    input_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(parse_inventory, "log_err", errors.append)

    args = SimpleNamespace(
        input=input_file,
        output=output_file,
        infer_level="medium",
        validate_inventory=False,
        list_missing_language_coverage=False,
        show_all_missing_language_coverage=False,
        strict_bcp47=False,
        verbose=False,
    )

    rc = parse_inventory.run_parse_font_inventory(args)

    assert rc == 1
    assert errors == ["invalid inventory: expected top-level object"]


def test_run_parse_inventory_rejects_missing_metadata_without_crashing(
    tmp_path, monkeypatch
):
    """
    Ensure missing metadata is converted into a deterministic user error.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the input file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture user-facing error messages.

    Returns
    -------
    None
    """
    input_file = tmp_path / "inventory.json"
    output_file = tmp_path / "out.json"
    errors: list[str] = []

    input_file.write_text(json.dumps({"fonts": []}), encoding="utf-8")
    monkeypatch.setattr(parse_inventory, "log_err", errors.append)

    args = SimpleNamespace(
        input=input_file,
        output=output_file,
        infer_level="medium",
        validate_inventory=False,
        list_missing_language_coverage=False,
        show_all_missing_language_coverage=False,
        strict_bcp47=False,
        verbose=False,
    )

    rc = parse_inventory.run_parse_font_inventory(args)

    assert rc == 1
    assert errors
    assert errors[0].startswith("schema validation failed:")


def test_run_parse_inventory_rejects_malformed_json(tmp_path, monkeypatch):
    """
    Ensure malformed JSON is reported as a deterministic user error.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the input file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture user-facing error messages.

    Returns
    -------
    None
    """
    input_file = tmp_path / "inventory.json"
    output_file = tmp_path / "out.json"
    errors: list[str] = []

    input_file.write_text("{", encoding="utf-8")
    monkeypatch.setattr(parse_inventory, "log_err", errors.append)

    args = SimpleNamespace(
        input=input_file,
        output=output_file,
        infer_level="medium",
        validate_inventory=False,
        list_missing_language_coverage=False,
        show_all_missing_language_coverage=False,
        strict_bcp47=False,
        verbose=False,
    )

    rc = parse_inventory.run_parse_font_inventory(args)

    assert rc == 1
    assert errors
    assert errors[0].startswith("invalid JSON:")
