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
    Raw language tags (coverage.languages_raw) must NOT be validated
    and must NOT produce warnings.
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
    Valid ISO language codes must not produce warnings.
    """
    inventory = {"fonts": [{"path": "dummy.ttf", "coverage": {"languages": ["en"]}}]}

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_invalid_language_triggers_warning():
    """
    Invalid ISO language codes must generate a warning.
    """
    inventory = {"fonts": [{"path": "dummy.ttf", "coverage": {"languages": ["xx"]}}]}

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    assert warnings[0]["code"] == "invalid_language_code"
    assert warnings[0]["language"] == "xx"


def test_raw_and_normalized_languages_mixed():
    """
    Raw languages must be ignored.
    Normalized languages must be validated.
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
