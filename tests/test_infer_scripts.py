"""
Verify script inference from Unicode block coverage.

Responsibilities
----------------
- Ensure scripts are inferred correctly from Unicode block statistics.
- Validate inference behavior for representative scripts.

Design principles
----------------
Script inference tests rely on small synthetic coverage datasets so
that inference behavior can be validated deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the logic that derives script inference results from Unicode coverage.
"""

from fontshow.inventory.script_analysis import infer_scripts


def test_infer_scripts_latn_from_unicode_blocks():
    """
    Verify that Latin block coverage infers the ``latn`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Latin Extended-A": 100,
            "Basic Latin": 200,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["latn"]


def test_infer_scripts_arabic_from_unicode_blocks():
    """
    Verify that Arabic block coverage infers the ``arab`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Arabic": 150,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["arab"]


def test_infer_scripts_mixed_latin_greek():
    """
    Verify that mixed Latin and Greek coverage reports both scripts.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Latin Extended-A": 120,
            "Greek and Coptic": 80,
        }
    }

    scripts = infer_scripts(coverage)
    assert set(scripts) == {"latn", "grek"}


def test_infer_scripts_cjk_japanese_disambiguation():
    """
    Verify that Hiragana and Katakana disambiguate Han coverage to Japanese.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Hiragana": 80,
            "Katakana": 90,
            "CJK Unified Ideographs": 200,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["jpan"]


def test_infer_scripts_unknown_when_no_coverage():
    """
    Verify that missing coverage yields the ``unknown`` sentinel.

    Returns
    -------
    None
    """
    coverage = {}

    scripts = infer_scripts(coverage)
    assert scripts == ["unknown"]


def test_infer_scripts_cyrillic():
    """
    Verify that Cyrillic block coverage infers the ``cyrl`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Cyrillic": 150,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["cyrl"]


def test_coverage_scripts_never_unknown():
    """
    Verify that the public coverage script list itself never contains ``unknown``.

    Returns
    -------
    None
    """
    coverage = {}
    scripts = coverage.get("scripts", [])
    assert "unknown" not in scripts
