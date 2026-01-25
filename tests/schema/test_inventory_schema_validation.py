import pytest

from fontshow.schema_validation import (
    _validate_inventory_schema_strict,
    validate_inventory_schema,
)


def make_inventory(schema_version="1.0", with_fonts=True):
    data = {
        "metadata": {
            "schema_version": schema_version,
        },
        "fonts": [],
    }

    if not with_fonts:
        data.pop("fonts")

    return data


# ----------------------------------------------------------------------
# Strict validation tests
# ----------------------------------------------------------------------


def test_strict_validation_ok_v1():
    data = make_inventory("1.0")
    _validate_inventory_schema_strict(data, schema_version="1.0")


def test_strict_validation_rejects_unknown_version():
    data = make_inventory("9.9")

    with pytest.raises(ValueError, match="Unsupported inventory schema"):
        _validate_inventory_schema_strict(data, schema_version="9.9")


def test_strict_validation_missing_schema_file(monkeypatch):
    data = make_inventory("1.0")

    def fake_exists(self):
        return False

    monkeypatch.setattr(
        "pathlib.Path.exists",
        fake_exists,
    )

    with pytest.raises(ValueError, match="Schema file not found"):
        _validate_inventory_schema_strict(data, schema_version="1.0")


def test_strict_validation_schema_error():
    # Missing "fonts"
    data = {
        "metadata": {
            "schema_version": "1.0",
        }
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data, schema_version="1.0")


# ----------------------------------------------------------------------
# Public API tests (backward compatibility)
# ----------------------------------------------------------------------


def test_public_validation_ok_returns_no_warnings():
    data = make_inventory("1.0")
    warnings = validate_inventory_schema(data)

    assert warnings == []


def test_public_validation_returns_warning_on_invalid_schema():
    data = {
        "metadata": {
            "schema_version": "1.0",
        }
        # missing fonts
    }

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "invalid_schema"
    assert "schema" in warnings[0]["message"]


def test_public_validation_handles_unknown_schema_version():
    data = make_inventory("9.9")

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["schema_version"] == "9.9"
