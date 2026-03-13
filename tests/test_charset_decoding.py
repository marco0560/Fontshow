"""
Verify charset decoding behavior when loading font inventories.

Responsibilities
----------------
- Ensure UTF-8 encoded inventory files are correctly decoded.
- Validate that malformed encodings are handled predictably.

Design principles
-----------------
Decoding tests operate on small synthetic inventories so that
encoding behavior can be validated deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the charset decoding logic used when loading inventory files.
"""

import json
from pathlib import Path

import pytest

from fontshow.inventory.io import load_font_inventory


def _write_inventory(tmp_path: Path, content: bytes | str) -> Path:
    """
    Write an inventory payload to the temporary test directory.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture used to isolate the inventory file.
    content : bytes | str
        Inventory payload written either as raw bytes or as UTF-8 text.

    Returns
    -------
    Path
        Path to the materialized inventory file.
    """
    path = tmp_path / "inventory.json"
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def test_utf8_inventory_ok(tmp_path):
    """
    Verify that a UTF-8 encoded inventory loads successfully.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture used by `_write_inventory`.

    Returns
    -------
    None
    """
    data = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [
            {"name": "Café Sans", "coverage": {"languages": ["fr"]}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))
    fonts = load_font_inventory(p)

    assert isinstance(fonts, list)
    assert fonts[0]["name"] == "Café Sans"


def test_non_latin_characters_ok(tmp_path):
    """
    Verify that non-Latin font names survive inventory loading unchanged.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture used by `_write_inventory`.

    Returns
    -------
    None
    """
    data = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [
            {"name": "東京ゴシック", "coverage": {"languages": ["ja"]}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))
    fonts = load_font_inventory(p)

    assert fonts[0]["name"] == "東京ゴシック"


def test_invalid_utf8_bytes_fail(tmp_path):
    """
    Verify that invalid UTF-8 bytes trigger a load failure.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture used by `_write_inventory`.

    Returns
    -------
    None

    Raises
    ------
    None
        The asserted exception is part of the expected test behavior.
    """
    raw = b'{"fonts": ["\xff"]}'
    p = _write_inventory(tmp_path, raw)

    with pytest.raises(Exception):
        load_font_inventory(p)


def test_mixed_invalid_unicode_fails(tmp_path):
    """
    Verify that surrogate-containing JSON text round-trips through loading.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture used by `_write_inventory`.

    Returns
    -------
    None

    Notes
    -----
    This test covers the edge case of a string containing an unpaired
    surrogate escape in JSON content.
    """
    data = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [
            {"name": "Bad\udc00Name", "coverage": {"languages": ["en"]}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))

    fonts = load_font_inventory(p)

    assert fonts[0]["name"] == "Bad\udc00Name"


def test_empty_string_fields_ok(tmp_path):
    """
    Verify that empty string fields are preserved during loading.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture used by `_write_inventory`.

    Returns
    -------
    None
    """
    data = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [
            {"name": "", "coverage": {"languages": []}},
        ],
    }

    p = _write_inventory(tmp_path, json.dumps(data))
    fonts = load_font_inventory(p)

    assert fonts[0]["name"] == ""
