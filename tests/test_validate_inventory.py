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
    """
    Verify that a minimal valid inventory passes validation.

    Important setup assumption: `minimal_inventory_v12()` returns a
    structurally valid current-schema inventory.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()

    result = validate_inventory(data)
    assert result == 0


# ============================================================
# INVALID ROOT
# ============================================================


def test_validate_inventory_invalid_root():
    """
    Verify that a non-mapping inventory root is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = validate_inventory([])
    assert result > 0


# ============================================================
# MISSING FONTS
# ============================================================


def test_validate_inventory_missing_fonts():
    """
    Verify that inventories missing the ``fonts`` container fail.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = {"metadata": {"schema_version": "1.5"}}

    result = validate_inventory(data)
    assert result > 0


# ============================================================
# INVALID FONT ENTRY
# ============================================================


def test_validate_inventory_with_invalid_entry():
    """
    Verify that a structurally invalid font entry makes validation fail.

    This test exercises the edge case where the inventory root is valid
    but an individual font descriptor is incomplete.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
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
    """
    Verify that a font entry with a missing required family field is fatal.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    entry = minimal_font_entry_v12()
    entry["family"] = None

    data = minimal_inventory_v12()
    data["fonts"] = [entry]

    result = validate_inventory(data)
    assert result > 0


def test_validate_inventory_allows_empty_internal_sample_when_specimen_is_valid():
    """
    Verify that enriched inventories may keep an empty internal sample text.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    entry = minimal_font_entry_v12()
    entry["typography"]["sample_text"]["text"] = ""

    data = minimal_inventory_v12()
    data["fonts"] = [entry]

    result = validate_inventory(data)
    assert result == 0


# ============================================================
# MISSING SCHEMA VERSION
# ============================================================


def test_validate_inventory_missing_schema_version_is_fatal():
    """
    Verify that removing ``metadata.schema_version`` makes validation fail.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = minimal_inventory_v12()
    del data["metadata"]["schema_version"]

    result = validate_inventory(data)
    assert result > 0


# ============================================================
# QUIET MODE SUPPRESSES OUTPUT
# ============================================================


def test_quiet_suppresses_output(capsys):
    """
    Verify that quiet CLI mode suppresses validator stdout output.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Pytest capture fixture used to inspect emitted output.

    Returns
    -------
    None
    """
    from fontshow.core.cli_utils import set_cli_mode

    set_cli_mode(quiet=True, verbose=False)

    data = minimal_inventory_v12()
    validate_inventory(data)

    captured = capsys.readouterr()
    assert captured.out == ""


def test_validate_inventory_summarizes_observations_without_per_font_warning_spam(
    capsys,
):
    """
    Verify that validation emits grouped summaries instead of per-font warning lines.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Pytest capture fixture used to inspect emitted output.

    Returns
    -------
    None
    """
    from fontshow.core.cli_utils import set_cli_mode

    set_cli_mode(quiet=False, verbose=False)

    entry = minimal_font_entry_v12()
    entry["typography"]["sample_text"]["text"] = ""
    entry["typography"]["specimen_strategy"] = "cmap"
    entry["inference"]["languages"] = ["en"]
    entry["warnings"] = [
        {
            "code": "missing_weight_class",
            "message": "OS/2 weight_class missing",
            "severity": "info",
        }
    ]

    data = minimal_inventory_v12()
    data["fonts"] = [entry]

    result = validate_inventory(data)

    captured = capsys.readouterr()
    assert result == 0
    assert "Validation observations" in captured.out
    assert "missing_internal_sample_text=1" in captured.out
    assert "missing_declared_languages=1" in captured.out
    assert "specimen_from_cmap=1" in captured.out
    assert "Validation warning summary" in captured.out
    assert "missing_weight_class=1" in captured.out
    assert "Warning [" not in captured.err
