"""
Verify validation of complete font inventories.

Responsibilities
----------------
- Ensure minimal valid inventories pass validation.
- Verify structural validation detects invalid inventory roots.

Design principles
----------------
Validation tests rely on minimal synthetic inventories so that
inventory validation behavior can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
validation behavior for complete inventory structures.
"""

from fontshow.cli.parse_inventory import validate_inventory
from tests.helpers import minimal_font_entry_v12, minimal_inventory_v12

# ============================================================
# VALID MINIMAL INVENTORY
# ============================================================


def test_validate_inventory_valid_minimal():
    data = minimal_inventory_v12()

    result = validate_inventory(data)
    assert result == 0


# ============================================================
# INVALID ROOT
# ============================================================


def test_validate_inventory_invalid_root():
    result = validate_inventory([])
    assert result > 0


# ============================================================
# MISSING FONTS
# ============================================================


def test_validate_inventory_missing_fonts():
    data = {"metadata": {"schema_version": "1.2"}}

    result = validate_inventory(data)
    assert result > 0


# ============================================================
# INVALID FONT ENTRY
# ============================================================


def test_validate_inventory_with_invalid_entry():
    data = minimal_inventory_v12()
    data["fonts"] = [
        {
            # structurally invalid: missing required fields
            "path": "/tmp/broken.ttf",
        }
    ]

    result = validate_inventory(data)
    assert result > 0


# ============================================================
# WARNING ONLY (no fatal errors)
# ============================================================


def test_validate_inventory_missing_family_is_fatal():
    entry = minimal_font_entry_v12()
    entry["family"] = None

    data = minimal_inventory_v12()
    data["fonts"] = [entry]

    result = validate_inventory(data)
    assert result > 0


# ============================================================
# MISSING SCHEMA VERSION
# ============================================================


def test_validate_inventory_missing_schema_version_is_fatal():
    data = minimal_inventory_v12()
    del data["metadata"]["schema_version"]

    result = validate_inventory(data)
    assert result > 0


# ============================================================
# QUIET MODE SUPPRESSES OUTPUT
# ============================================================


def test_quiet_suppresses_output(capsys):
    from fontshow.core.cli_utils import set_cli_mode

    set_cli_mode(quiet=True, verbose=False)

    data = minimal_inventory_v12()
    validate_inventory(data)

    captured = capsys.readouterr()
    assert captured.out == ""
