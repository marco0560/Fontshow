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

from fontshow.cli import parse_inventory as parse_inventory_module
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


def test_parse_inventory_reconciles_primary_script_with_internal_specimen(
    monkeypatch,
):
    """
    Ensure specimen text can correct an incoherent explicit primary script.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace parse-stage helpers with deterministic
        stubs.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        parse_inventory_module,
        "_apply_schema_validation",
        lambda _data: None,
    )
    monkeypatch.setattr(parse_inventory_module, "_process_charset", lambda *_args: None)
    monkeypatch.setattr(
        parse_inventory_module,
        "_process_language_metadata",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        parse_inventory_module,
        "collect_latex_validation_metadata",
        dict,
    )
    monkeypatch.setattr(
        parse_inventory_module,
        "probe_and_persist_lualatex_render_variants",
        lambda _fonts, *, validation_metadata: None,
    )

    def _fake_infer(font, coverage, *, level, font_path):
        _ = level, font_path
        coverage["scripts"] = ["LATN", "ARAB"]
        coverage["primary_script"] = "LATN"
        font["inference"] = {
            "level": "aggressive",
            "scripts": ["LATN", "ARAB"],
            "primary_script": "LATN",
            "languages": ["en", "ar"],
            "declared_scripts": [],
            "declared_languages": [],
            "unicode_blocks": {"Basic Latin": 95},
        }

    monkeypatch.setattr(
        parse_inventory_module,
        "_infer_and_attach_metadata",
        _fake_infer,
    )

    def _fake_specimen(font, coverage, font_path):
        _ = coverage, font_path
        typography = font.setdefault("typography", {})
        typography["specimen_text"] = (
            "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ ٱلشَّمْسِ إِذْ بَزَغَتْ"
        )
        typography["specimen_strategy"] = "internal"
        typography["specimen_glyph_count"] = 24
        typography["specimen_rejection_reason"] = None

    monkeypatch.setattr(
        parse_inventory_module,
        "_specimen_generate_for_font",
        _fake_specimen,
    )

    data = {
        "metadata": {"validation": {}},
        "fonts": [
            {
                "path": "/tmp/Amiri-Regular.ttf",
                "family": "Amiri",
                "coverage": {"unicode_blocks": {"Basic Latin": 95}},
            }
        ],
    }

    result = parse_inventory(data, level="aggressive")
    font = result["fonts"][0]

    assert font["coverage"]["primary_script"] == "ARAB"
    assert font["coverage"]["scripts"][0] == "ARAB"
    assert font["inference"]["primary_script"] == "ARAB"
    assert font["inference"]["scripts"][0] == "ARAB"
    assert font["typography"]["primary_script"] == "ARAB"


def test_parse_inventory_reconciles_mixed_cmap_specimen_away_from_latn(
    monkeypatch,
):
    """
    Ensure mixed Han-plus-Latin cmap specimens do not stay spuriously Latin.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace parse-stage helpers with deterministic
        stubs.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        parse_inventory_module,
        "_apply_schema_validation",
        lambda _data: None,
    )
    monkeypatch.setattr(parse_inventory_module, "_process_charset", lambda *_args: None)
    monkeypatch.setattr(
        parse_inventory_module,
        "_process_language_metadata",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        parse_inventory_module,
        "collect_latex_validation_metadata",
        dict,
    )
    monkeypatch.setattr(
        parse_inventory_module,
        "probe_and_persist_lualatex_render_variants",
        lambda _fonts, *, validation_metadata: None,
    )

    def _fake_infer(font, coverage, *, level, font_path):
        _ = level, font_path
        coverage["scripts"] = ["LATN", "HANI", "BOPO"]
        coverage["primary_script"] = "LATN"
        font["inference"] = {
            "level": "aggressive",
            "scripts": ["LATN", "HANI", "BOPO"],
            "primary_script": "LATN",
            "languages": ["zh"],
            "declared_scripts": [],
            "declared_languages": [],
            "unicode_blocks": {
                "Basic Latin": 25,
                "CJK Unified Ideographs": 25,
            },
        }

    monkeypatch.setattr(
        parse_inventory_module,
        "_infer_and_attach_metadata",
        _fake_infer,
    )

    def _fake_specimen(font, coverage, font_path):
        _ = coverage, font_path
        typography = font.setdefault("typography", {})
        typography["specimen_text"] = "天地玄黃 宇宙洪荒"
        typography["specimen_strategy"] = "cmap"
        typography["specimen_glyph_count"] = 8
        typography["specimen_rejection_reason"] = "fallback_to_cmap"

    monkeypatch.setattr(
        parse_inventory_module,
        "_specimen_generate_for_font",
        _fake_specimen,
    )

    data = {
        "metadata": {"validation": {}},
        "fonts": [
            {
                "path": "/tmp/ARPLKaitiM.ttf",
                "family": "AR PL KaitiM",
                "coverage": {"unicode_blocks": {"Basic Latin": 25}},
            }
        ],
    }

    result = parse_inventory(data, level="aggressive")
    font = result["fonts"][0]

    assert font["coverage"]["primary_script"] == "HANI"
    assert font["coverage"]["scripts"][0] == "HANI"
    assert font["inference"]["primary_script"] == "HANI"
    assert font["inference"]["scripts"][0] == "HANI"
    assert font["typography"]["primary_script"] == "HANI"
