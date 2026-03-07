import pytest

from fontshow.inventory.schema_validation import (
    _validate_inventory_schema_strict,
    validate_inventory_schema,
)


def make_inventory(schema_version="1.2", with_fonts=True):
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


def test_strict_validation_rejects_v1():
    data = make_inventory("1.0")
    with pytest.raises(ValueError):
        _validate_inventory_schema_strict(data)


def test_strict_validation_rejects_unknown_version():
    data = make_inventory("9.9")

    with pytest.raises(ValueError, match="Unsupported inventory schema"):
        _validate_inventory_schema_strict(data)


def test_strict_validation_missing_schema_file(monkeypatch):
    data = make_inventory("1.2")

    class FakeSchemaPath:
        def __truediv__(self, name):
            return self

        def read_text(self, *args, **kwargs):
            raise FileNotFoundError

    monkeypatch.setattr(
        "fontshow.inventory.schema_validation.files",
        lambda *_: FakeSchemaPath(),
    )

    with pytest.raises(ValueError, match="Schema resource not found"):
        _validate_inventory_schema_strict(data)


def test_strict_validation_schema_error():
    # Missing required metadata fields AND fonts
    data = {
        "metadata": {
            "schema_version": "1.2",
        }
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data)


# ----------------------------------------------------------------------
# Public API tests
# ----------------------------------------------------------------------


def _valid_metadata_block():
    return {
        "schema_version": "1.2",
        "input_inventory_tool": "test",
        "input_inventory_tool_version": "0",
        "inference_level": "none",
        "fonttools": {
            "available": True,
            "fontconfig_charset_included": True,
            "version": "0",
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
    }


def test_public_validation_ok_returns_no_warnings():
    data = {
        "metadata": _valid_metadata_block(),
        "fonts": [],
    }

    warnings = validate_inventory_schema(data)

    assert warnings == []


def test_public_validation_returns_warning_on_invalid_schema():
    data = {
        "metadata": _valid_metadata_block(),
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
