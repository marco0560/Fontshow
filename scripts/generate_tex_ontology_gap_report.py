#!/usr/bin/env python3
"""
Generate a TeX-versus-ontology gap report.

This maintenance script compares the local TeX support surface against
Fontshow's current ontology and emits a deterministic JSON report of
missing scripts and languages that should be reviewed.

Responsibilities
----------------
- Load the local TeX audit report.
- Compare local ``fontspec`` and Polyglossia support to ontology data.
- Classify missing items into review buckets.

Design principles
-----------------
Gap analysis is deterministic and conservative. It reports differences
without attempting to auto-modify ontology files or invent linguistic
metadata such as specimens.

Architectural role
------------------
This script belongs to the developer tooling layer and supports staged
expansion of the Fontshow ontology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from fontshow.inventory.semantic_validation import normalize_languages
from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO

_DEFAULT_AUDIT_PATH = Path("reports/local_tex_surface.json")
_DEFAULT_OUTPUT_PATH = Path("reports/tex_ontology_gap_report.json")
_NON_CANONICAL_LANGUAGE_MODULES: frozenset[str] = frozenset(
    {
        "american",
        "australian",
        "austrian",
        "bahasai",
        "bahasam",
        "brazil",
        "british",
        "canadian",
        "canadien",
    }
)


def load_audit_report(path: Path) -> dict[str, Any]:
    """
    Load a previously generated local TeX audit report.

    Parameters
    ----------
    path : pathlib.Path
        Path to the JSON audit report.

    Returns
    -------
    dict[str, object]
        Parsed audit payload.
    """
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def build_ontology_snapshot() -> dict[str, list[str]]:
    """
    Build a normalized view of current ontology TeX-facing entries.

    Returns
    -------
    dict[str, list[str]]
        Snapshot containing the TeX script names and Polyglossia
        languages currently modeled by the ontology.
    """
    ontology_scripts = sorted(
        {
            info["fontspec_opts"][len("Script=") :].strip("{}")
            for info in SCRIPT_INFO.values()
            if info["fontspec_opts"].startswith("Script=")
        }
    )
    ontology_languages = sorted(
        {
            info["polyglossia_language"]
            for info in SCRIPT_INFO.values()
            if info["polyglossia_language"]
        }
    )
    ontology_language_codes = sorted(LANGUAGE_INFO.keys())
    return {
        "fontspec_scripts": ontology_scripts,
        "polyglossia_languages": ontology_languages,
        "language_codes": ontology_language_codes,
    }


def classify_missing_script(script_name: str) -> str:
    """
    Classify a missing fontspec script for later ontology work.

    Parameters
    ----------
    script_name : str
        Local ``fontspec`` script name absent from the ontology.

    Returns
    -------
    str
        Conservative review bucket label.
    """
    script_name_lower = script_name.lower()
    if any(
        token in script_name_lower
        for token in {"default", "math", "musical", "braille"}
    ):
        return "should_not_be_language"
    if any(
        token in script_name_lower
        for token in {
            "cjk",
            "kana",
            "hiragana",
            "katakana",
            "hangul",
            "latin",
            "greek",
            "cyrillic",
            "arabic",
        }
    ):
        return "needs_alias_mapping"
    return "needs_specimen"


def classify_missing_language(language_name: str) -> str:
    """
    Classify a missing Polyglossia language for later ontology work.

    Parameters
    ----------
    language_name : str
        Polyglossia module name absent from the ontology.

    Returns
    -------
    str
        Conservative review bucket label.
    """
    if language_name in _NON_CANONICAL_LANGUAGE_MODULES:
        return "non_canonical_module"
    normalized = normalize_languages([language_name])
    if normalized["normalized"]:
        return "normalized_by_pipeline"
    if any(ch in language_name for ch in {"-", "_"}):
        return "needs_alias_mapping"
    if len(language_name) <= 3:
        return "needs_alias_mapping"
    return "needs_specimen"


def build_gap_report(audit: dict[str, Any]) -> dict[str, Any]:
    """
    Compare the local TeX surface to the current ontology.

    Parameters
    ----------
    audit : dict[str, object]
        Parsed local TeX audit report.

    Returns
    -------
    dict[str, object]
        JSON-serializable comparison report.
    """
    ontology = build_ontology_snapshot()

    local_scripts = sorted(set(audit.get("fontspec_scripts", [])))
    local_languages = sorted(set(audit.get("polyglossia_languages", [])))
    ontology_scripts = ontology["fontspec_scripts"]
    ontology_languages = ontology["polyglossia_languages"]

    missing_scripts = sorted(set(local_scripts) - set(ontology_scripts))
    missing_languages = sorted(set(local_languages) - set(ontology_languages))

    return {
        "local_counts": {
            "fontspec_scripts": len(local_scripts),
            "polyglossia_languages": len(local_languages),
        },
        "ontology_counts": {
            "fontspec_scripts": len(ontology_scripts),
            "polyglossia_languages": len(ontology_languages),
            "language_codes": len(ontology["language_codes"]),
        },
        "covered": {
            "fontspec_scripts": ontology_scripts,
            "polyglossia_languages": ontology_languages,
        },
        "missing": {
            "fontspec_scripts": [
                {
                    "name": script_name,
                    "classification": classify_missing_script(script_name),
                }
                for script_name in missing_scripts
            ],
            "polyglossia_languages": [
                {
                    "name": language_name,
                    "classification": classify_missing_language(language_name),
                }
                for language_name in missing_languages
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for gap report generation.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments for the gap-report generator.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audit-report",
        type=Path,
        default=_DEFAULT_AUDIT_PATH,
        help="Path to the JSON output from audit_local_tex_surface.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT_PATH,
        help="Output JSON report path",
    )
    return parser.parse_args()


def main() -> int:
    """
    Execute TeX-versus-ontology gap analysis.

    Returns
    -------
    int
        Process exit status code. Returns ``0`` on success.
    """
    args = parse_args()
    audit = load_audit_report(args.audit_report)
    report = build_gap_report(audit)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {args.output}")
    print(
        "[OK] "
        f"missing fontspec scripts={len(report['missing']['fontspec_scripts'])} "
        f"missing polyglossia languages={len(report['missing']['polyglossia_languages'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
