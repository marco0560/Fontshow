"""
Verify language normalization utilities.

Responsibilities
----------------
- Ensure language codes are normalized to canonical form.
- Validate handling of case normalization and empty inputs.

Design principles
----------------
Normalization tests rely on small synthetic language lists so that
normalization rules can be validated deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
language normalization behavior used during inventory validation.
"""

from fontshow.inventory.semantic_validation import normalize_languages


def test_empty_input():
    """
    Verify that empty language input normalizes to empty result collections.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages([])
    assert result["normalized"] == []
    assert result["deprecated"] == []
    assert result["dropped"] == []


def test_basic_normalization():
    """
    Verify that already-normalized language tags are preserved.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages(["en", "fr"])
    assert result["normalized"] == ["en", "fr"]
    assert result["deprecated"] == []
    assert result["dropped"] == []


def test_case_normalization():
    """
    Verify that mixed-case language tags are lowercased.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages(["EN", "Fr"])
    assert result["normalized"] == ["en", "fr"]
    assert result["deprecated"] == []
    assert result["dropped"] == []


def test_deprecated_language_mapping():
    """
    Verify that deprecated language tags are remapped and recorded.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages(["mo"])
    assert result["normalized"] == ["ro"]
    assert result["deprecated"] == [{"raw": "mo", "from_": "mo", "to": "ro"}]
    assert result["dropped"] == []


def test_variant_stripping():
    """
    Verify that region and variant suffixes are stripped to base tags.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages(["zh-hk", "pt_BR"])
    assert result["normalized"] == ["zh", "pt"]
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "zh-hk", "reason": "variant_stripped"},
        {"raw": "pt_BR", "reason": "variant_stripped"},
    ]


def test_duplicate_languages():
    """
    Verify that duplicates after normalization are dropped with reasons.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages(["en", "EN", "en"])
    assert result["normalized"] == ["en"]
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "EN", "reason": "duplicate_normalized", "normalized": "en"},
        {"raw": "en", "reason": "duplicate_normalized", "normalized": "en"},
    ]


def test_unknown_language():
    """
    Verify that unknown language codes are dropped as unsupported.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    result = normalize_languages(["xx"])
    assert result["normalized"] == []
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "xx", "reason": "unknown_language"},
    ]


def test_mixed_case():
    """
    Verify that repeated regional variants collapse to one normalized base tag.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    This test covers the edge case where the first value is recorded as a
    stripped variant and later values become duplicate-normalized drops.
    """
    result = normalize_languages(["ar_IN", "ar_IQ", "ar_JO"])
    assert result["normalized"] == ["ar"]
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "ar_IN", "reason": "variant_stripped"},
        {"raw": "ar_IQ", "reason": "duplicate_normalized", "normalized": "ar"},
        {"raw": "ar_JO", "reason": "duplicate_normalized", "normalized": "ar"},
    ]
