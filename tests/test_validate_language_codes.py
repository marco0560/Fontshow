"""
Verify validation of language codes in inventories.

Responsibilities
----------------
- Ensure valid language codes do not produce warnings.
- Verify invalid inferred language codes generate validation warnings.

Design principles
----------------
Tests use minimal synthetic inventories so that language validation
behavior can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
semantic validation rules for language codes within inventory data.
"""

from fontshow.inventory.semantic_validation import validate_language_codes


def test_valid_language_codes_no_warnings():
    """
    Verify that valid declared and inferred language codes produce no warnings.

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "coverage": {"languages": ["en", "fr"]},
                "inference": {"languages": ["de"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_invalid_inferred_language_code_emits_warning():
    """
    Verify that an invalid inferred language code emits one warning.

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "inference": {"languages": ["zz"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    w = warnings[0]
    assert w["code"] == "invalid_language_code"
    assert w["language"] == "zz"


def test_invalid_declared_language_code_emits_warning():
    """
    Verify that an invalid declared coverage language emits a warning.

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "coverage": {"languages": ["xx"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    assert warnings[0]["language"] == "xx"


def test_unknown_language_code_is_ignored():
    """
    Verify that the ``unknown`` sentinel is ignored during validation.

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "inference": {"languages": ["unknown"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_duplicate_language_codes_emit_single_warning():
    """
    Verify that duplicate invalid codes across coverage and inference warn once.

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "coverage": {"languages": ["zz"]},
                "inference": {"languages": ["zz"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
