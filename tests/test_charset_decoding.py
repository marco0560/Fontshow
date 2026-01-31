# tests/test_charset_decoding.py

import json
from pathlib import Path

import pytest

from fontshow.create_catalog import load_font_inventory


def _write_inventory(tmp_path: Path, content: bytes | str) -> Path:
    path = tmp_path / "inventory.json"
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def test_utf8_inventory_ok(tmp_path):
    data = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [
            {"name": "Café Sans", "coverage": {"languages": ["fr"]}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))
    fonts = load_font_inventory(p)

    assert isinstance(fonts, list)
    assert fonts[0]["name"] == "Café Sans"


def test_non_latin_characters_ok(tmp_path):
    data = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [
            {"name": "東京ゴシック", "coverage": {"languages": ["ja"]}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))
    fonts = load_font_inventory(p)

    assert fonts[0]["name"] == "東京ゴシック"


def test_invalid_utf8_bytes_fail(tmp_path):
    raw = b'{"fonts": ["\xff"]}'
    p = _write_inventory(tmp_path, raw)

    with pytest.raises(Exception):
        load_font_inventory(p)


def test_mixed_invalid_unicode_fails(tmp_path):
    data = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [
            {"name": "Bad\udc00Name", "coverage": {"languages": ["en"]}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))

    fonts = load_font_inventory(p)

    assert fonts[0]["name"] == "Bad\udc00Name"


def test_empty_string_fields_ok(tmp_path):
    data = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [
            {"name": "", "coverage": {"languages": []}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))
    fonts = load_font_inventory(p)

    assert fonts[0]["name"] == ""
