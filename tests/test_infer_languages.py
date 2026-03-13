"""
Verify language inference from Unicode block coverage.

Responsibilities
----------------
- Ensure languages are correctly inferred from Unicode block statistics.
- Validate inference for representative scripts such as Latin and Cyrillic.

Design principles
----------------
Language inference tests use synthetic coverage maps so that inference
behavior can be validated deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
language inference logic derived from Unicode block coverage.
"""

from fontshow.inventory.infer_languages import infer_languages


def test_infer_languages_latn():
    """
    Verify that Basic Latin coverage yields at least English as a candidate.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Basic Latin": 95,
        }
    }

    result = infer_languages(coverage)
    languages = result.keys()

    assert "en" in languages


def test_infer_languages_cyrillic():
    """
    Verify that Cyrillic coverage yields Russian as a candidate language.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Cyrillic": 128,
        }
    }

    result = infer_languages(coverage)
    languages = result.keys()

    assert "ru" in languages


def test_infer_languages_mixed_scripts():
    """
    Verify that mixed Latin and Greek coverage yields both language families.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Basic Latin": 95,
            "Greek and Coptic": 120,
        }
    }

    result = infer_languages(coverage)
    languages = result.keys()

    assert "en" in languages
    assert "el" in languages


def test_infer_languages_unknown_script():
    """
    Verify that an empty Unicode block map yields no inferred languages.

    Returns
    -------
    None
    """
    coverage = {"unicode_blocks": {}}

    result = infer_languages(coverage)

    assert result == {}


def test_infer_languages_empty_input():
    """
    Verify that completely empty input yields no inferred languages.

    Returns
    -------
    None
    """
    result = infer_languages({})

    assert result == {}
