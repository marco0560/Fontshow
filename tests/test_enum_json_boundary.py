"""
Verify JSON boundary handling for enum serialization.

Responsibilities
----------------
- Ensure enum values are serialized to JSON as strings.
- Verify enum normalization when loading JSON inventories.

Design principles
-----------------
Boundary tests validate the interface between internal enum types and
JSON representations so that serialization and deserialization remain
stable and deterministic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the JSON boundary behavior for enum values in inventory data.
"""

from __future__ import annotations

import json

from fontshow.core.json_boundary import normalize_loaded_enums
from fontshow.core.json_format import dumps_pretty
from fontshow.core.types import Severity


def _build_sample_inventory():
    """
    Build a minimal inventory payload containing enum-backed warnings.

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Inventory structure used by the JSON boundary tests.
    """
    return {
        "metadata": {"schema_version": "1.0"},
        "warnings": [
            {"code": "x", "message": "m", "severity": Severity.WARN},
            {"code": "y", "message": "m", "severity": Severity.ERROR},
        ],
    }


def test_enum_written_as_string():
    """
    Verify that enum severities serialize to JSON strings.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inv = _build_sample_inventory()

    s = dumps_pretty(inv)
    data = json.loads(s)

    warnings = data["warnings"]
    assert isinstance(warnings[0]["severity"], str)
    assert warnings[0]["severity"] == "warning"
    assert warnings[1]["severity"] == "error"


def test_enum_restored_after_load():
    """
    Verify that JSON-loaded severity strings are normalized back to enums.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inv = _build_sample_inventory()
    s = dumps_pretty(inv)

    data = json.loads(s)
    normalize_loaded_enums(data)

    warnings = data["warnings"]
    assert isinstance(warnings[0]["severity"], Severity)
    assert warnings[0]["severity"] is Severity.WARN
    assert warnings[1]["severity"] is Severity.ERROR


def test_no_string_severity_after_normalization():
    """
    Verify that normalization leaves no string severities in warnings.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inv = _build_sample_inventory()
    s = dumps_pretty(inv)

    data = json.loads(s)
    normalize_loaded_enums(data)

    for w in data["warnings"]:
        assert not isinstance(w["severity"], str)


def test_roundtrip_stability():
    """
    Verify that serialize-normalize-serialize preserves JSON semantics.

    This edge case checks round-trip stability across the enum JSON
    boundary rather than object identity.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inv = _build_sample_inventory()

    s1 = dumps_pretty(inv)
    data = json.loads(s1)
    normalize_loaded_enums(data)
    s2 = dumps_pretty(data)

    assert json.loads(s1) == json.loads(s2)
