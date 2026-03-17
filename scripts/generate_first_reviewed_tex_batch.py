#!/usr/bin/env python3
"""
Generate a first reviewed TeX-ontology expansion batch.

This maintenance script consumes the previously generated ontology-stub
proposal and emits a conservative JSON batch covering only low-risk
cases that are suitable for fast manual review.

The batch currently focuses on:

- obvious Polyglossia alias-to-canonical mappings;
- obvious Polyglossia module names already normalized by the production pipeline;
- obvious Polyglossia non-canonical locale/style modules to suppress from ontology work;
- obvious TeX script aliases to existing ontology script options;
- a minimal set of new script candidates whose ISO mappings are clear.

Responsibilities
----------------
- Select only low-risk reviewed candidates from the stub proposal.
- Keep reviewed output separate from the authoritative ontology source.
- Provide a deterministic artifact for incremental curation work.

Design principles
-----------------
The selection logic is intentionally narrow. The script does not invent
language specimens, fill ontology entries automatically, or broaden
support based on weak heuristics.

Architectural role
------------------
This script belongs to the developer tooling layer and supports staged
manual expansion of Fontshow's TeX-facing ontology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from fontshow.ontology.language_tables import SCRIPT_INFO

_DEFAULT_STUB_PROPOSAL = Path("reports/tex_ontology_stub_proposal.json")
_DEFAULT_OUTPUT = Path("reports/first_reviewed_tex_batch.json")

_REVIEWED_LANGUAGE_ALIASES: dict[str, str] = {
    "am": "amharic",
    "ar": "arabic",
    "bn": "bengali",
    "de": "german",
    "dv": "divehi",
    "el": "greek",
    "en": "english",
    "en-AU": "english",
    "en-CA": "english",
    "en-GB": "english",
    "en-NZ": "english",
    "en-US": "english",
    "es": "spanish",
    "et": "estonian",
    "eu": "basque",
    "fa": "farsi",
    "fi": "finnish",
    "fr": "french",
    "ga": "irish",
    "gd": "gaelic",
    "he": "hebrew",
    "hi": "hindi",
    "hr": "croatian",
    "hy": "armenian",
    "id": "bahasa",
    "is": "icelandic",
    "it": "italian",
    "ja": "japanese",
    "ka": "georgian",
    "km": "khmer",
    "kn": "kannada",
    "ko": "korean",
    "lo": "lao",
    "lt": "lithuanian",
    "lv": "latvian",
    "mk": "macedonian",
    "ml": "malayalam",
    "mr": "marathi",
    "nb": "norwegian",
    "nl": "dutch",
    "nn": "nynorsk",
    "or": "odia",
    "pt": "portuguese",
    "ru": "russian",
    "ta": "tamil",
    "th": "thai",
    "tr": "turkish",
    "zh": "chinese",
}

_REVIEWED_SCRIPT_ALIASES: dict[str, dict[str, str]] = {
    "CJK Ideographic": {
        "target_script_iso": "HANI",
        "target_fontspec_opts": "Script=CJK",
        "reason": "fontspec alias of the existing Han/CJK render path",
    },
    "Hiragana and Katakana": {
        "target_script_iso": "KANA",
        "target_fontspec_opts": "Script=Kana",
        "reason": "fontspec aggregate alias of the existing Kana render path",
    },
}

_REVIEWED_NEW_SCRIPT_CANDIDATES: dict[str, dict[str, str]] = {
    "Buginese": {
        "script_iso": "BUGI",
        "canonical_name": "Buginese",
        "fontspec_opts": "Script=Buginese",
        "specimen_strategy": "script_sample_required",
        "reason": "clear ISO 15924 and fontspec naming alignment",
    },
    "Buhid": {
        "script_iso": "BUHD",
        "canonical_name": "Buhid",
        "fontspec_opts": "Script=Buhid",
        "specimen_strategy": "script_sample_required",
        "reason": "clear ISO 15924 and fontspec naming alignment",
    },
}


def load_stub_proposal(path: Path) -> dict[str, Any]:
    """
    Load a previously generated TeX ontology stub proposal.

    Parameters
    ----------
    path : pathlib.Path
        Path to the stub proposal JSON file.

    Returns
    -------
    dict[str, object]
        Parsed JSON payload.
    """
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def existing_fontspec_targets() -> set[str]:
    """
    Collect existing ontology ``fontspec`` script option values.

    Returns
    -------
    set[str]
        Set of raw ``Script=...`` option strings currently modeled by
        the ontology.
    """
    return {
        info["fontspec_opts"]
        for info in SCRIPT_INFO.values()
        if info["fontspec_opts"].startswith("Script=")
    }


def build_first_reviewed_batch(stub_proposal: dict[str, Any]) -> dict[str, Any]:
    """
    Build the first reviewed TeX expansion batch.

    Parameters
    ----------
    stub_proposal : dict[str, object]
        Parsed JSON payload from ``generate_tex_ontology_stubs.py``.

    Returns
    -------
    dict[str, object]
        JSON-serializable reviewed batch report.
    """
    languages = stub_proposal.get("languages", {})
    alias_variants = languages.get("alias_variants", [])
    pipeline_normalized = languages.get("pipeline_normalized", [])
    non_canonical_modules = languages.get("non_canonical_modules", [])
    alias_names = {item["alias"] for item in alias_variants}
    pipeline_normalized_names = {item["language"] for item in pipeline_normalized}
    non_canonical_module_names = {item["language"] for item in non_canonical_modules}

    reviewed_language_aliases = [
        {
            "alias": alias,
            "canonical_language": canonical_language,
            "reason": "low-risk spelling/region/module alias for specimen purposes",
        }
        for alias, canonical_language in sorted(_REVIEWED_LANGUAGE_ALIASES.items())
        if alias in alias_names
    ]
    reviewed_pipeline_normalized_languages = [
        {
            "language": language,
            "canonical_language": canonical_language,
            "reason": (
                "production language normalization already collapses this module "
                "to the canonical primary tag"
            ),
        }
        for language, canonical_language in sorted(_REVIEWED_LANGUAGE_ALIASES.items())
        if language in pipeline_normalized_names
    ]
    reviewed_non_canonical_modules = sorted(non_canonical_module_names)

    script_items = stub_proposal.get("scripts", [])
    script_names = {item["fontspec_script"] for item in script_items}
    existing_targets = existing_fontspec_targets()

    reviewed_script_aliases = [
        {
            "fontspec_script": script_name,
            **mapping,
        }
        for script_name, mapping in sorted(_REVIEWED_SCRIPT_ALIASES.items())
        if script_name in script_names
        and mapping["target_fontspec_opts"] in existing_targets
    ]

    reviewed_new_scripts = [
        {
            "fontspec_script": script_name,
            **candidate,
        }
        for script_name, candidate in sorted(_REVIEWED_NEW_SCRIPT_CANDIDATES.items())
        if script_name in script_names
    ]

    return {
        "summary": {
            "reviewed_language_aliases": len(reviewed_language_aliases),
            "reviewed_pipeline_normalized_languages": len(
                reviewed_pipeline_normalized_languages
            ),
            "reviewed_non_canonical_modules": len(reviewed_non_canonical_modules),
            "reviewed_script_aliases": len(reviewed_script_aliases),
            "reviewed_new_script_candidates": len(reviewed_new_scripts),
        },
        "languages": {
            "aliases": reviewed_language_aliases,
            "pipeline_normalized": reviewed_pipeline_normalized_languages,
            "non_canonical_modules": reviewed_non_canonical_modules,
        },
        "scripts": {
            "aliases": reviewed_script_aliases,
            "new_candidates": reviewed_new_scripts,
        },
    }


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for reviewed batch generation.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments for the reviewed-batch generator.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stub-proposal",
        type=Path,
        default=_DEFAULT_STUB_PROPOSAL,
        help="Path to the TeX ontology stub proposal JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Output JSON reviewed-batch path",
    )
    return parser.parse_args()


def main() -> int:
    """
    Execute first reviewed-batch generation.

    Returns
    -------
    int
        Process exit status code. Returns ``0`` on success.
    """
    args = parse_args()
    batch = build_first_reviewed_batch(load_stub_proposal(args.stub_proposal))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(batch, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {args.output}")
    print(
        "[OK] "
        f"language aliases={batch['summary']['reviewed_language_aliases']} "
        f"pipeline normalized={batch['summary']['reviewed_pipeline_normalized_languages']} "
        f"non-canonical modules={batch['summary']['reviewed_non_canonical_modules']} "
        f"script aliases={batch['summary']['reviewed_script_aliases']} "
        f"new script candidates={batch['summary']['reviewed_new_script_candidates']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
