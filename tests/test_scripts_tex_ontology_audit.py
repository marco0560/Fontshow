"""
Exercise local TeX audit and gap-report maintenance scripts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_script_module(script_name: str):
    """
    Load a maintenance script as an importable test module.

    Parameters
    ----------
    script_name : str
        Filename of the script located under ``scripts/``.

    Returns
    -------
    module
        Imported Python module object for the requested script.
    """
    path = _SCRIPTS_DIR / script_name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit_local_tex_surface = _load_script_module("audit_local_tex_surface.py")
generate_tex_ontology_gap_report = _load_script_module(
    "generate_tex_ontology_gap_report.py"
)
generate_tex_ontology_stubs = _load_script_module("generate_tex_ontology_stubs.py")
generate_first_reviewed_tex_batch = _load_script_module(
    "generate_first_reviewed_tex_batch.py"
)


def test_extract_fontspec_scripts_normalizes_tilde_and_deduplicates():
    """
    Ensure fontspec script extraction returns stable normalized names.

    Returns
    -------
    None
    """
    text = r"""
    \newfontscript{Arabic}{arab}
    \newfontscript{Dives~Akuru}{diak}
    \newfontscript{Arabic}{arab}
    """
    assert audit_local_tex_surface.extract_fontspec_scripts(text) == [
        "Arabic",
        "Dives Akuru",
    ]


def test_extract_polyglossia_languages_discovers_modules(tmp_path):
    """
    Ensure language module discovery only includes gloss-*.ldf files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage mock Polyglossia files.

    Returns
    -------
    None
    """
    (tmp_path / "gloss-english.ldf").write_text("", encoding="utf-8")
    (tmp_path / "gloss-ar.ldf").write_text("", encoding="utf-8")
    (tmp_path / "README.txt").write_text("", encoding="utf-8")

    assert audit_local_tex_surface.extract_polyglossia_languages(tmp_path) == [
        "ar",
        "english",
    ]


def test_build_gap_report_marks_missing_items_with_review_buckets():
    """
    Ensure gap analysis emits classified missing script/language entries.

    Returns
    -------
    None
    """
    report = generate_tex_ontology_gap_report.build_gap_report(
        {
            "fontspec_scripts": ["Arabic", "Buginese", "Math"],
            "polyglossia_languages": ["arabic", "buginese", "en-US"],
        }
    )

    missing_scripts = {
        item["name"]: item["classification"]
        for item in report["missing"]["fontspec_scripts"]
    }
    missing_languages = {
        item["name"]: item["classification"]
        for item in report["missing"]["polyglossia_languages"]
    }

    assert "Arabic" not in missing_scripts
    assert "Buginese" not in missing_scripts
    assert missing_scripts["Math"] == "should_not_be_language"
    assert "arabic" not in missing_languages
    assert missing_languages["buginese"] == "needs_specimen"
    assert missing_languages["en-US"] == "needs_alias_mapping"


def test_build_stub_proposal_splits_canonical_languages_from_aliases():
    """
    Ensure stub proposal separates alias variants from canonical candidates.

    Returns
    -------
    None
    """
    proposal = generate_tex_ontology_stubs.build_stub_proposal(
        {
            "missing": {
                "fontspec_scripts": [
                    {"name": "Buginese", "classification": "needs_specimen"},
                ],
                "polyglossia_languages": [
                    {"name": "english", "classification": "needs_specimen"},
                    {"name": "en-US", "classification": "needs_alias_mapping"},
                    {"name": "ckb-Arab", "classification": "needs_alias_mapping"},
                ],
            }
        }
    )

    assert proposal["summary"]["script_stubs"] == 1
    assert proposal["summary"]["canonical_language_candidates"] == 1
    assert proposal["summary"]["alias_variants"] == 2
    assert proposal["languages"]["canonical_candidates"] == [
        {
            "action": "curate_sample_and_script_profile",
            "classification": "needs_specimen",
            "language": "english",
        }
    ]
    assert proposal["languages"]["alias_groups"]["ckb"] == ["ckb-Arab"]
    assert proposal["languages"]["alias_groups"]["en"] == ["en-US"]


def test_build_first_reviewed_batch_selects_only_low_risk_items():
    """
    Ensure the reviewed batch emits only configured low-risk candidates.

    Returns
    -------
    None
    """
    batch = generate_first_reviewed_tex_batch.build_first_reviewed_batch(
        {
            "languages": {
                "alias_variants": [
                    {
                        "alias": "en-US",
                        "canonical_candidate": "en",
                        "classification": "needs_alias_mapping",
                    },
                    {
                        "alias": "ja",
                        "canonical_candidate": "ja",
                        "classification": "needs_alias_mapping",
                    },
                    {
                        "alias": "zz",
                        "canonical_candidate": "zz",
                        "classification": "needs_alias_mapping",
                    },
                ]
            },
            "scripts": [
                {"fontspec_script": "Buginese", "classification": "needs_specimen"},
                {
                    "fontspec_script": "Hiragana and Katakana",
                    "classification": "needs_alias_mapping",
                },
                {
                    "fontspec_script": "Unknown Script",
                    "classification": "needs_specimen",
                },
            ],
        }
    )

    assert batch["summary"] == {
        "reviewed_language_aliases": 2,
        "reviewed_script_aliases": 1,
        "reviewed_new_script_candidates": 1,
    }
    assert batch["languages"]["aliases"] == [
        {
            "alias": "en-US",
            "canonical_language": "english",
            "reason": "low-risk spelling/region/module alias for specimen purposes",
        },
        {
            "alias": "ja",
            "canonical_language": "japanese",
            "reason": "low-risk spelling/region/module alias for specimen purposes",
        },
    ]
    assert batch["scripts"]["aliases"][0]["fontspec_script"] == "Hiragana and Katakana"
    assert batch["scripts"]["new_candidates"][0]["script_iso"] == "BUGI"
