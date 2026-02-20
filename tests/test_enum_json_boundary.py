from __future__ import annotations

import json

from fontshow.json_boundary import normalize_loaded_enums
from fontshow.json_format import dumps_pretty
from fontshow.types import Severity


def _build_sample_inventory():
    return {
        "metadata": {"schema_version": "1.0"},
        "warnings": [
            {"code": "x", "message": "m", "severity": Severity.WARN},
            {"code": "y", "message": "m", "severity": Severity.ERROR},
        ],
    }


def test_enum_written_as_string():
    inv = _build_sample_inventory()

    s = dumps_pretty(inv)
    data = json.loads(s)

    warnings = data["warnings"]
    assert isinstance(warnings[0]["severity"], str)
    assert warnings[0]["severity"] == "warning"
    assert warnings[1]["severity"] == "error"


def test_enum_restored_after_load():
    inv = _build_sample_inventory()
    s = dumps_pretty(inv)

    data = json.loads(s)
    normalize_loaded_enums(data)

    warnings = data["warnings"]
    assert isinstance(warnings[0]["severity"], Severity)
    assert warnings[0]["severity"] is Severity.WARN
    assert warnings[1]["severity"] is Severity.ERROR


def test_no_string_severity_after_normalization():
    inv = _build_sample_inventory()
    s = dumps_pretty(inv)

    data = json.loads(s)
    normalize_loaded_enums(data)

    for w in data["warnings"]:
        assert not isinstance(w["severity"], str)


def test_roundtrip_stability():
    inv = _build_sample_inventory()

    s1 = dumps_pretty(inv)
    data = json.loads(s1)
    normalize_loaded_enums(data)
    s2 = dumps_pretty(data)

    assert json.loads(s1) == json.loads(s2)
