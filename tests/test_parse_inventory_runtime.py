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


def test_run_parse_inventory_lists_missing_language_coverage(monkeypatch, tmp_path):
    """
    Ensure the reporting mode lists only fonts with empty coverage.languages.
    """
    input_file = tmp_path / "inventory.json"
    output_file = tmp_path / "out.json"
    infos: list[str] = []

    inventory = {
        "metadata": {
            "schema_version": "1.2",
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
        strict_bcp47=False,
    )

    rc = parse_inventory.run_parse_font_inventory(
        args,
        write_text_fn=lambda path, text: write_calls.append((path, text)),
    )

    assert rc == 0
    assert write_calls == []
    assert infos == [
        "Fonts with missing declared language coverage: 2",
        "Alpha | /fonts/a.ttf",
        "Gamma | /fonts/c.ttf",
    ]
