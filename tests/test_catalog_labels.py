"""
Exercise catalog label edge cases.

Responsibilities
----------------
- Verify malformed script metadata does not leak stringified sentinels.
- Ensure charset-coverage parsing falls back deterministically.
"""

from fontshow.catalog.labels import primary_script


def test_primary_script_ignores_non_string_inference_entries():
    """
    Ensure malformed inferred scripts do not become string labels.

    Returns
    -------
    None
    """
    assert primary_script({"inference": {"scripts": [None]}}) is None
    assert primary_script({"coverage": {"scripts": [0]}}) is None


def test_primary_script_falls_back_when_charset_scores_are_not_comparable():
    """
    Ensure malformed charset coverage values do not raise.

    Returns
    -------
    None
    """
    font = {
        "coverage": {"script_coverage_from_charset": {"LATN": object()}},
        "inference": {"scripts": ["latn"]},
    }

    assert primary_script(font) == "latn"
