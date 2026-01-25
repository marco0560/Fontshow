import pytest

from fontshow.schema_validation import (
    _validate_inventory_schema_strict,
    validate_inventory_schema,
)


def test_raw_inventory_without_metadata_emits_deprecation_warning():
    data = {"fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_deprecated"


def test_enriched_inventory_schema_1_1_is_valid():
    data = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [{"coverage": {"unicode_blocks": {"Basic Latin": 95}}}],
    }

    warnings = validate_inventory_schema(data)

    assert warnings == []


def test_unknown_schema_version_emits_warning():
    data = {"metadata": {"schema_version": "9.9"}, "fonts": []}

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_unknown"


def test_invalid_inventory_structure_raises():
    data = {
        "metadata": {"schema_version": "1.1"}
        # missing "fonts"
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data, schema_version="1.1")


def test_legacy_schema_emits_deprecation_warning():
    data = {
        "fonts": [],
    }

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "schema_version_deprecated"
    assert warnings[0]["severity"] == "warning"


def test_invalid_schema_raises_validation_error():
    data = {
        "metadata": {"schema_version": "1.1"}
        # missing "fonts"
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data, schema_version="1.1")
