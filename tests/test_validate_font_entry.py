"""
Verify validation of font inventory entries.

Responsibilities
----------------
- Ensure minimal valid entries pass validation.
- Verify structural errors are detected for malformed entries.

Design principles
----------------
Validation tests construct minimal inventory entries so that schema
and structural validation rules can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
validation logic for individual font inventory entries.
"""

from fontshow.inventory.entry_validation import validate_font_entry
from tests.helpers import minimal_font_entry_v12

# ============================================================
# VALID MINIMAL ENTRY
# ============================================================


def test_validate_font_entry_valid_minimal():
    entry = minimal_font_entry_v12()

    errors = validate_font_entry(entry, index=0)
    assert errors == []


# ============================================================
# NOT A DICT
# ============================================================


def test_validate_font_entry_not_a_dict():
    entry = "not a dict"

    errors = validate_font_entry(entry, index=0)
    assert errors  # must contain at least one error


# ============================================================
# MISSING REQUIRED FIELDS → FATAL
# ============================================================


def test_validate_font_entry_missing_required_fields():
    entry = {
        "path": "/tmp/font.ttf"
        # missing required structural fields like family/subfamily/etc.
    }

    errors = validate_font_entry(entry, index=0)
    assert errors  # fatal structural error expected


# ============================================================
# BASE_NAMES PRESENT → IDENTITY NOT REQUIRED
# (validator logic)
# ============================================================


def test_validate_font_entry_missing_family_is_fatal():
    entry = minimal_font_entry_v12()
    entry.pop("family", None)

    errors = validate_font_entry(entry, index=0)
    assert errors
    assert "Missing or invalid 'family'" in errors


# ============================================================
# IDENTITY PRESENT → BASE_NAMES NOT REQUIRED
# ============================================================


def test_validate_font_entry_identity_allows_missing_base_names():
    entry = minimal_font_entry_v12()
    entry.pop("base_names", None)

    errors = validate_font_entry(entry, index=0)
    assert errors == []


# ============================================================
# IDENTITY WRONG TYPE
# ============================================================


def test_validate_font_entry_extra_unknown_field_is_ignored():
    entry = minimal_font_entry_v12()
    entry["identity"] = "not a dict"  # unknown field under schema 1.2

    errors = validate_font_entry(entry, index=0)
    assert errors == []
