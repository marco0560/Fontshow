"""
Verify threshold behavior in language inference.

Responsibilities
----------------
- Ensure symbolic or minimal block coverage does not trigger inference.
- Validate language inference once coverage thresholds are exceeded.

Design principles
----------------
Threshold tests verify that inference heuristics remain stable and
do not produce false positives for small symbolic coverage.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
threshold rules applied by the language inference algorithm.
"""

from fontshow.inventory.infer_languages import infer_languages


def test_greek_not_inferred_from_symbolic_coverage():
    """
    Verify that symbolic Greek coverage does not trigger Greek inference.

    The setup mixes strong Basic Latin coverage with only two Greek code
    points so the test exercises the low-coverage threshold guard
    against false positives.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Greek and Coptic": 2,  # presenza simbolica
            "Basic Latin": 95,
        }
    }

    languages = infer_languages(coverage)
    codes = set(languages.keys())

    assert "el" not in codes


def test_greek_inferred_with_sufficient_block_coverage():
    """
    Verify that substantial Greek block coverage enables Greek inference.

    This edge case checks the threshold crossover where Greek coverage
    becomes high enough to infer ``el`` confidently.

    Returns
    -------
    None
    """
    # Greek and Coptic size ≈ 135
    # 72 / 135 ≈ 0.53 > 0.40
    coverage = {
        "unicode_blocks": {
            "Greek and Coptic": 72,
        }
    }

    languages = infer_languages(coverage)
    codes = set(languages.keys())

    assert "el" in codes


def test_latin_languages_not_regressed():
    """
    Verify that stronger threshold rules do not regress Latin inference.

    The setup provides broad Latin block coverage and asserts that the
    core Western language candidates remain inferred.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Basic Latin": 95,  # 95 / 128 ≈ 0.74
            "Latin-1 Supplement": 96,  # 96 / 128 = 0.75
            "Latin Extended-A": 110,  # supporto opzionale
        }
    }

    languages = infer_languages(coverage)
    codes = set(languages.keys())

    assert "en" in codes
    assert "fr" in codes
    assert "de" in codes
