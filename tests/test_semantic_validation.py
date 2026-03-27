"""
Verify semantic validation of language codes.

Responsibilities
----------------
- Ensure raw language tags are not validated prematurely.
- Verify that only normalized language lists are checked.

Design principles
----------------
Semantic validation tests isolate language validation logic using
minimal synthetic inventories.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
semantic validation rules for language codes.
"""

from fontshow.inventory.semantic_validation import validate_language_codes


def test_raw_languages_are_not_validated():
    """
    Verify that raw language tags are not validated prematurely.

    The test asserts that ``coverage.languages_raw`` is ignored by
    `validate_language_codes` and therefore does not emit warnings.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "path": "dummy.ttf",
                "coverage": {"languages_raw": ["zh-hk"], "languages": []},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_valid_language_passes():
    """
    Verify that valid normalized ISO language codes produce no warnings.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inventory = {"fonts": [{"path": "dummy.ttf", "coverage": {"languages": ["en"]}}]}

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_invalid_language_triggers_warning():
    """
    Verify that an invalid normalized language code emits a warning.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inventory = {"fonts": [{"path": "dummy.ttf", "coverage": {"languages": ["xx"]}}]}

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "invalid_language_code"
    assert warnings[0]["language"] == "xx"


def test_raw_and_normalized_languages_mixed():
    """
    Verify that raw languages are ignored while normalized languages are validated.

    This edge case mixes a raw language variant with one valid and one
    invalid normalized language to ensure only the normalized invalid
    entry is reported.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    inventory = {
        "fonts": [
            {
                "path": "dummy.ttf",
                "coverage": {"languages_raw": ["zh-hk"], "languages": ["zh", "xx"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "invalid_language_code"
    assert warnings[0]["language"] == "xx"
