"""
Verify inventory schema validation behavior.

This module tests the validation logic responsible for ensuring that
Fontshow inventory files comply with the declared schema version.

Responsibilities
----------------
- Verify strict schema validation behavior.
- Ensure schema validation reports the correct severity levels.
- Validate correct handling of missing or malformed schema fields.

Design principles
-----------------
Schema validation tests operate on minimal inventory structures so
that schema rule regressions are detected deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the schema validation logic used for inventory data structures.
"""

import pytest

from fontshow.inventory.schema_validation import (
    _validate_inventory_schema_strict,
    validate_inventory_schema,
)


def make_inventory(schema_version="1.3", with_fonts=True):
    """
    Build a minimal inventory payload for schema validation tests.

    Parameters
    ----------
    schema_version : str, optional
        Schema version inserted into the inventory metadata.
    with_fonts : bool, optional
        Whether to include the top-level ``fonts`` container.

    Returns
    -------
    dict
        Minimal inventory payload used by the tests in this module.
    """
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
    """
    Verify that strict schema validation rejects legacy v1.0 inventories.

    Returns
    -------
    None
    """
    data = make_inventory("1.0")
    with pytest.raises(ValueError):
        _validate_inventory_schema_strict(data)


def test_strict_validation_rejects_unknown_version():
    """
    Verify that strict schema validation rejects unknown schema versions.

    Returns
    -------
    None
    """
    data = make_inventory("9.9")

    with pytest.raises(ValueError, match="Unsupported inventory schema"):
        _validate_inventory_schema_strict(data)


def test_strict_validation_missing_schema_file(monkeypatch):
    """
    Verify that a missing bundled schema file is surfaced as a validation error.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the schema resource loader.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        Raised by the fake schema-path reader and converted into a validation error.

    Notes
    -----
    The test replaces the schema resource loader with a fake path-like
    object that raises `FileNotFoundError` when the schema text is read.
    """
    data = make_inventory("1.3")

    class FakeSchemaPath:
        """
        Minimal path-like test double used to emulate a missing schema resource.

        Notes
        -----
        The instance preserves path-joining semantics while failing on reads.
        """

        def __truediv__(self, name):
            """
            Preserve chained path joining while keeping the fake object unchanged.

            Parameters
            ----------
            name : str
                Ignored path component requested by the code under test.

            Returns
            -------
            FakeSchemaPath
                The same fake path object.
            """
            return self

        def read_text(self, *args, **kwargs):
            """
            Emulate schema resource reading failure.

            Parameters
            ----------
            *args : object
                Ignored positional arguments preserved for interface compatibility.
            **kwargs : object
                Ignored keyword arguments preserved for interface compatibility.

            Returns
            -------
            None

            Raises
            ------
            FileNotFoundError
                Always raised to simulate a missing bundled schema file.
            """
            raise FileNotFoundError

    monkeypatch.setattr(
        "fontshow.inventory.schema_validation.files",
        lambda *_: FakeSchemaPath(),
    )

    with pytest.raises(ValueError, match="Schema resource not found"):
        _validate_inventory_schema_strict(data)


def test_strict_validation_schema_error():
    """
    Verify that strict validation rejects inventories missing required schema fields.

    Returns
    -------
    None
    """
    # Missing required metadata fields AND fonts
    data = {
        "metadata": {
            "schema_version": "1.3",
        }
    }

    with pytest.raises(ValueError, match="Inventory schema validation failed"):
        _validate_inventory_schema_strict(data)


# ----------------------------------------------------------------------
# Public API tests
# ----------------------------------------------------------------------


def _valid_metadata_block():
    """
    Build a complete metadata block for public schema validation tests.

    Returns
    -------
    dict
        Schema-valid metadata mapping.
    """
    return {
        "schema_version": "1.3",
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
        "validation": {
            "lualatex": {
                "attempted": False,
                "engine": None,
                "engine_version": None,
                "luaotfload_version": None,
                "fontspec_version": None,
                "polyglossia_version": None,
                "runtime_fingerprint": None,
                "render_policy_version": "test-policy",
            }
        },
    }


def test_public_validation_ok_returns_no_warnings():
    """
    Verify that public schema validation returns no warnings for valid input.

    Returns
    -------
    None
    """
    data = {
        "metadata": _valid_metadata_block(),
        "fonts": [],
    }

    warnings = validate_inventory_schema(data)

    assert warnings == []


def test_public_validation_returns_warning_on_invalid_schema():
    """
    Verify that public schema validation converts invalid schema into warnings.

    Returns
    -------
    None
    """
    data = {
        "metadata": _valid_metadata_block(),
        # missing fonts
    }

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "invalid_schema"
    assert "schema" in warnings[0]["message"]


def test_public_validation_handles_unknown_schema_version():
    """
    Verify that public schema validation reports unknown schema versions.

    Returns
    -------
    None
    """
    data = make_inventory("9.9")

    warnings = validate_inventory_schema(data)

    assert len(warnings) == 1
    assert warnings[0]["schema_version"] == "9.9"
