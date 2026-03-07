import pytest

from fontshow.core.types import Severity
from fontshow.inventory.schema_validation import (
    _validate_inventory_schema_strict,
    validate_inventory_schema,
)

# ---------------------------------------------------------------------------
# Helper — minimal valid v1.2 inventory (must satisfy schema requirements)
# ---------------------------------------------------------------------------


def _valid_v12_inventory():
    return {
        "metadata": {
            "schema_version": "1.2",
            "input_inventory_tool": "test",
            "input_inventory_tool_version": "0",
            "inference_level": "none",
            "fonttools": {
                "available": True,
                "version": "0",
                "fontconfig_charset_included": False,
            },
            "run_environment": {
                "os": "test",
                "os_release": "test",
                "kernel": "test",
                "machine": "test",
                "python_version": "test",
                "hostname": "test",
                "execution_context": "native",
            },
        },
        "fonts": [],
    }


# ---------------------------------------------------------------------------
# Public validator behaviour
# ---------------------------------------------------------------------------


def test_raw_inventory_without_metadata_emits_deprecation_warning():
    data = {"fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_deprecated"
    assert warnings[0]["severity"] == Severity.WARN


def test_valid_v1_2_inventory_is_ok():
    data = _valid_v12_inventory()

    warnings = validate_inventory_schema(data)

    assert warnings == []


def test_unknown_schema_version_emits_warning():
    data = {"metadata": {"schema_version": "9.9"}, "fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_unknown"
    assert warnings[0]["severity"] == Severity.ERROR


def test_legacy_schema_is_reported_as_unknown():
    # Current validator behavior: legacy versions are not treated as "deprecated",
    # they are treated as "unknown" schema versions.
    data = {"metadata": {"schema_version": "1.0"}, "fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_unknown"
    assert warnings[0]["severity"] == Severity.ERROR


# ---------------------------------------------------------------------------
# Strict validator behaviour
# ---------------------------------------------------------------------------


def test_invalid_inventory_structure_raises():
    data = {
        "metadata": {"schema_version": "1.2"}
        # missing "fonts"
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data)


def test_invalid_schema_raises_validation_error():
    data = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [],
        # missing required metadata fields
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data)
