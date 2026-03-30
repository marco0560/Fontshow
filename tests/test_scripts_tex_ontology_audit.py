"""Exercise local TeX audit and gap-report maintenance scripts."""

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
generate_tex_alignment_plan = _load_script_module("generate_tex_alignment_plan.py")


def test_extract_fontspec_scripts_normalizes_tilde_and_deduplicates():
    """
    Ensure fontspec script extraction returns stable normalized names.

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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
    assert missing_languages["en-US"] == "normalized_by_pipeline"
    assert generate_tex_ontology_gap_report.classify_missing_language("american") == (
        "non_canonical_module"
    )


def test_build_stub_proposal_splits_canonical_languages_from_aliases():
    """
    Ensure stub proposal separates alias variants from canonical candidates.

    Parameters
    ----------
    None

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
                    {"name": "en-US", "classification": "normalized_by_pipeline"},
                    {"name": "ckb-Arab", "classification": "needs_alias_mapping"},
                    {"name": "american", "classification": "non_canonical_module"},
                ],
            }
        }
    )

    assert proposal["summary"]["script_stubs"] == 1
    assert proposal["summary"]["canonical_language_candidates"] == 1
    assert proposal["summary"]["alias_variants"] == 1
    assert proposal["summary"]["pipeline_normalized_languages"] == 1
    assert proposal["summary"]["non_canonical_modules"] == 1
    assert proposal["languages"]["canonical_candidates"] == [
        {
            "action": "curate_sample_and_script_profile",
            "classification": "needs_specimen",
            "language": "english",
        }
    ]
    assert proposal["languages"]["alias_groups"]["ckb"] == ["ckb-Arab"]
    assert proposal["languages"]["pipeline_normalized"] == [
        {
            "language": "en-US",
            "normalized_candidate": "en",
            "classification": "normalized_by_pipeline",
        }
    ]
    assert proposal["languages"]["non_canonical_modules"] == [
        {
            "language": "american",
            "classification": "non_canonical_module",
        }
    ]


def test_build_first_reviewed_batch_selects_only_low_risk_items():
    """
    Ensure the reviewed batch emits only configured low-risk candidates.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    batch = generate_first_reviewed_tex_batch.build_first_reviewed_batch(
        {
            "languages": {
                "alias_variants": [
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
                ],
                "pipeline_normalized": [
                    {
                        "language": "en-US",
                        "normalized_candidate": "en",
                        "classification": "normalized_by_pipeline",
                    }
                ],
                "non_canonical_modules": [
                    {
                        "language": "american",
                        "classification": "non_canonical_module",
                    }
                ],
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
        "reviewed_language_aliases": 1,
        "reviewed_pipeline_normalized_languages": 1,
        "reviewed_non_canonical_modules": 1,
        "reviewed_script_aliases": 1,
        "reviewed_new_script_candidates": 1,
    }
    assert batch["languages"]["aliases"] == [
        {
            "alias": "ja",
            "canonical_language": "japanese",
            "reason": "low-risk spelling/region/module alias for specimen purposes",
        },
    ]
    assert batch["languages"]["pipeline_normalized"] == [
        {
            "language": "en-US",
            "canonical_language": "english",
            "reason": (
                "production language normalization already collapses this module "
                "to the canonical primary tag"
            ),
        }
    ]
    assert batch["languages"]["non_canonical_modules"] == ["american"]
    assert batch["scripts"]["aliases"][0]["fontspec_script"] == "Hiragana and Katakana"
    assert batch["scripts"]["new_candidates"][0]["script_iso"] == "BUGI"


def test_build_alignment_plan_separates_alias_work_from_batch_work():
    """
    Ensure the staged alignment plan preserves the alias policy and batches.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    plan = generate_tex_alignment_plan.build_alignment_plan(
        {
            "local_counts": {
                "fontspec_scripts": 6,
                "polyglossia_languages": 8,
            },
            "ontology_counts": {
                "fontspec_scripts": 3,
                "polyglossia_languages": 2,
                "language_codes": 7,
            },
            "covered": {
                "fontspec_scripts": ["Arabic", "CJK", "Kana"],
                "polyglossia_languages": ["arabic", "japanese"],
            },
            "missing": {
                "fontspec_scripts": [
                    {
                        "name": "CJK Ideographic",
                        "classification": "needs_alias_mapping",
                    },
                    {
                        "name": "Math",
                        "classification": "should_not_be_language",
                    },
                    {"name": "Avestan", "classification": "needs_specimen"},
                    {"name": "Bassa Vah", "classification": "needs_specimen"},
                ],
                "polyglossia_languages": [
                    {"name": "en-US", "classification": "needs_alias_mapping"},
                    {"name": "english", "classification": "needs_specimen"},
                    {"name": "afrikaans", "classification": "needs_specimen"},
                ],
            },
        },
        {
            "scripts": [
                {
                    "fontspec_script": "Avestan",
                    "classification": "needs_specimen",
                    "action": "curate_script_mapping_and_specimen",
                },
                {
                    "fontspec_script": "Bassa Vah",
                    "classification": "needs_specimen",
                    "action": "curate_script_mapping_and_specimen",
                },
            ],
            "languages": {
                "canonical_candidates": [
                    {
                        "language": "afrikaans",
                        "classification": "needs_specimen",
                        "action": "curate_sample_and_script_profile",
                    },
                    {
                        "language": "english",
                        "classification": "needs_specimen",
                        "action": "curate_sample_and_script_profile",
                    },
                ],
                "alias_variants": [
                    {
                        "alias": "ckb-Arab",
                        "canonical_candidate": "ckb",
                        "classification": "needs_alias_mapping",
                    }
                ],
                "alias_groups": {"ckb": ["ckb-Arab"]},
                "pipeline_normalized": [
                    {
                        "language": "en-US",
                        "normalized_candidate": "en",
                        "classification": "normalized_by_pipeline",
                    }
                ],
                "non_canonical_modules": [
                    {
                        "language": "american",
                        "classification": "non_canonical_module",
                    }
                ],
            },
            "summary": {
                "script_stubs": 2,
                "canonical_language_candidates": 2,
                "alias_variants": 1,
                "alias_groups": 1,
                "pipeline_normalized_languages": 1,
                "non_canonical_modules": 1,
            },
        },
        {
            "summary": {
                "reviewed_language_aliases": 1,
                "reviewed_pipeline_normalized_languages": 0,
                "reviewed_non_canonical_modules": 1,
                "reviewed_script_aliases": 1,
                "reviewed_new_script_candidates": 0,
            },
            "languages": {
                "aliases": [
                    {
                        "alias": "en-US",
                        "canonical_language": "english",
                        "reason": "low-risk spelling/region/module alias for specimen purposes",
                    }
                ],
                "pipeline_normalized": [],
                "non_canonical_modules": ["american"],
            },
            "scripts": {
                "aliases": [
                    {
                        "fontspec_script": "CJK Ideographic",
                        "target_script_iso": "HANI",
                        "target_fontspec_opts": "Script=CJK",
                        "reason": "fontspec alias of the existing Han/CJK render path",
                    }
                ],
                "new_candidates": [],
            },
        },
        batch_size=1,
    )

    assert plan["policy"]["alias_handling"] == (
        "support_only_aliases_stay_outside_production_ontology"
    )
    assert plan["distance"]["missing"] == {
        "fontspec_scripts": 4,
        "polyglossia_languages": 3,
    }
    assert plan["buckets"]["support_alias_work"] == {
        "script_alias_candidates": 1,
        "language_alias_variants": 1,
        "pipeline_normalized_languages": 1,
        "non_canonical_modules": 1,
        "reviewed_language_aliases": 1,
        "reviewed_pipeline_normalized_languages": 0,
        "reviewed_non_canonical_modules": 1,
        "reviewed_script_aliases": 1,
    }
    assert plan["buckets"]["production_ontology_work"] == {
        "script_stubs": 2,
        "canonical_language_candidates": 2,
    }
    assert plan["buckets"]["non_ontology_local_tex_entries"] == {
        "fontspec_scripts": ["Math"]
    }
    assert plan["production_batches"]["scripts"] == [
        {
            "batch": 1,
            "kind": "scripts",
            "items": [
                {
                    "fontspec_script": "Avestan",
                    "classification": "needs_specimen",
                    "action": "curate_script_mapping_and_specimen",
                }
            ],
        },
        {
            "batch": 2,
            "kind": "scripts",
            "items": [
                {
                    "fontspec_script": "Bassa Vah",
                    "classification": "needs_specimen",
                    "action": "curate_script_mapping_and_specimen",
                }
            ],
        },
    ]
    assert plan["production_batches"]["languages"] == [
        {
            "batch": 1,
            "kind": "languages",
            "items": [
                {
                    "language": "afrikaans",
                    "classification": "needs_specimen",
                    "action": "curate_sample_and_script_profile",
                }
            ],
        },
        {
            "batch": 2,
            "kind": "languages",
            "items": [
                {
                    "language": "english",
                    "classification": "needs_specimen",
                    "action": "curate_sample_and_script_profile",
                }
            ],
        },
    ]
