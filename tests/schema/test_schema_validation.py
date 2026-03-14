"""
Verify general schema validation rules.

This module tests the primary validation routines responsible for
checking inventory data against the defined schema.

Responsibilities
----------------
- Validate schema compliance for minimal valid inventories.
- Ensure schema violations produce the expected severity levels.
- Verify behavior of strict and non-strict validation modes.

Design principles
-----------------
Validation tests rely on minimal inventories to isolate schema rule
behavior and detect regressions deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
core schema validation logic for inventory structures.
"""

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
    """
    Build a minimal schema-valid v1.2 inventory payload.

    Returns
    -------
    dict
        Inventory structure suitable for schema validation tests.
    """
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


def test_raw_inventory_without_metadata_emits_error():
    """
    Verify that inventories without metadata are rejected.

    Returns
    -------
    None
    """
    data = {"fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_missing"
    assert warnings[0]["severity"] == Severity.ERROR


def test_valid_v1_2_inventory_is_ok():
    """
    Verify that a minimal valid v1.2 inventory produces no warnings.

    Returns
    -------
    None
    """
    data = _valid_v12_inventory()

    warnings = validate_inventory_schema(data)

    assert warnings == []


def test_unknown_schema_version_emits_warning():
    """
    Verify that an unknown schema version produces an error-severity warning.

    Returns
    -------
    None
    """
    data = {"metadata": {"schema_version": "9.9"}, "fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_unknown"
    assert warnings[0]["severity"] == Severity.ERROR


def test_legacy_schema_is_reported_as_unknown():
    """
    Verify the current behavior for legacy schema versions treated as unknown.

    Returns
    -------
    None
    """
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
    """
    Verify that strict validation raises on inventories missing required structure.

    Returns
    -------
    None
    """
    data = {
        "metadata": {"schema_version": "1.2"}
        # missing "fonts"
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data)


def test_invalid_schema_raises_validation_error():
    """
    Verify that strict validation raises on inventories missing metadata details.

    Returns
    -------
    None
    """
    data = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [],
        # missing required metadata fields
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data)
