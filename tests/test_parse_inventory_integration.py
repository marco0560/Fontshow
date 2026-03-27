"""
Verify integration behavior of inventory parsing.

Responsibilities
----------------
- Ensure the parse_inventory CLI logic produces valid inference results.
- Validate integration between parsing, inference, and output structure.

Design principles
----------------
Integration tests use minimal inventory structures so that parsing and
inference behavior can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
integration behavior of the inventory parsing pipeline.
"""

from fontshow.cli.parse_inventory import parse_inventory


def test_parse_inventory_basic_latin_only():
    """
    Verify that Basic Latin coverage alone does not infer languages.

    The test exercises the integration path from inventory parsing to
    language inference and asserts that the resulting inference payload
    remains empty for minimal Latin-only coverage.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = {
        "fonts": [
            {
                "coverage": {
                    "unicode_blocks": {
                        "Basic Latin": 95,
                    }
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert inference["languages"] == []


def test_parse_inventory_latin_extended():
    """
    Verify that richer Latin coverage yields expected inferred languages.

    The setup adds both Basic Latin and Latin-1 Supplement coverage and
    asserts that common Western language candidates appear in the
    parsed inference payload.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = {
        "fonts": [
            {
                "coverage": {
                    "unicode_blocks": {
                        "Basic Latin": 95,
                        "Latin-1 Supplement": 96,
                    }
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert "en" in inference["languages"]
    assert "fr" in inference["languages"]
    assert "de" in inference["languages"]


def test_declared_languages_do_not_affect_inference():
    """
    Verify that declared coverage languages are preserved but not reused for inference.

    This edge case checks that parsing keeps ``declared_languages`` in
    the output while inferred languages remain driven only by Unicode
    coverage heuristics.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = {
        "fonts": [
            {
                "coverage": {
                    "languages": ["fr", "de"],
                    "unicode_blocks": {
                        "Basic Latin": 95,
                    },
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    # declared preserved
    assert inference["declared_languages"] == ["fr", "de"]

    # inferred remains strict
    assert inference["languages"] == []


def test_parse_inventory_cyrillic():
    """
    Verify that Cyrillic coverage propagates to Russian language inference.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = {
        "fonts": [
            {
                "coverage": {
                    "unicode_blocks": {
                        "Cyrillic": 128,
                    }
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert "ru" in inference["languages"]


def test_parse_inventory_no_coverage():
    """
    Verify that missing coverage data yields an empty inference result.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data: dict[str, object] = {"fonts": [{"coverage": {}}]}

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert inference["languages"] == []


def test_missing_declared_languages_uses_inference_without_warning():
    """
    Verify that missing declared languages is handled via inference without warning noise.

    The enriched inventory should remain usable even when declared
    languages are absent from the raw metadata.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data: dict[str, object] = {
        "fonts": [{"coverage": {"unicode_blocks": {"Basic Latin": 95}}}]
    }

    result = parse_inventory(data, level="medium")
    assert result["fonts"][0]["inference"]["languages"] == []
    assert result["fonts"][0].get("warnings", []) == []
