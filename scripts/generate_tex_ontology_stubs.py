#!/usr/bin/env python3
"""
Generate reviewable ontology stubs from the TeX gap report.

This maintenance script consumes the TeX-versus-ontology gap report and
produces a deterministic JSON proposal separating:

- canonical specimen-language candidates,
- alias-only language variants,
- script stubs requiring curation.

Responsibilities
----------------
- Classify missing Polyglossia entries into canonical or alias buckets.
- Preserve missing script entries for later ontology curation.
- Emit a review-oriented JSON proposal without changing source code.

Design principles
-----------------
The script is conservative by default. It avoids inventing specimens,
script mappings, or language metadata beyond what can be inferred from
the gap-report naming shape.

Architectural role
------------------
This script belongs to the developer tooling layer and supports staged
expansion of Fontshow's TeX-facing ontology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

_DEFAULT_GAP_REPORT = Path("reports/tex_ontology_gap_report.json")
_DEFAULT_OUTPUT = Path("reports/tex_ontology_stub_proposal.json")


def load_gap_report(path: Path) -> dict[str, Any]:
    """
    Load a previously generated TeX ontology gap report.

    Parameters
    ----------
    path : pathlib.Path
        Path to the gap report JSON file.

    Returns
    -------
    dict[str, object]
        Parsed JSON payload.
    """
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def is_alias_language(name: str) -> bool:
    """
    Determine whether a Polyglossia module name is alias-like.

    Parameters
    ----------
    name : str
        Polyglossia language/module name.

    Returns
    -------
    bool
        True when the name appears to be a variant or alias rather than
        a canonical specimen-language candidate.
    """
    return any(ch in name for ch in {"-", "_"}) or len(name) <= 3


def canonicalize_alias_target(name: str) -> str:
    """
    Derive a conservative canonical target for an alias-like name.

    Parameters
    ----------
    name : str
        Polyglossia language/module name.

    Returns
    -------
    str
        Canonicalized target token for grouping related variants.
    """
    token = name.replace("_", "-").split("-", 1)[0]
    return token.lower()


def build_stub_proposal(gap_report: dict[str, Any]) -> dict[str, Any]:
    """
    Build a reviewable ontology-stub proposal from a gap report.

    Parameters
    ----------
    gap_report : dict[str, object]
        Parsed JSON payload from ``generate_tex_ontology_gap_report.py``.

    Returns
    -------
    dict[str, object]
        JSON-serializable stub proposal.
    """
    missing = gap_report.get("missing", {})
    missing_scripts = missing.get("fontspec_scripts", [])
    missing_languages = missing.get("polyglossia_languages", [])

    script_stubs = [
        {
            "fontspec_script": item["name"],
            "classification": item["classification"],
            "action": "curate_script_mapping_and_specimen",
        }
        for item in missing_scripts
    ]

    alias_variants: list[dict[str, str]] = []
    canonical_languages: list[dict[str, str]] = []

    for item in missing_languages:
        name = item["name"]
        classification = item["classification"]
        if is_alias_language(name):
            alias_variants.append(
                {
                    "alias": name,
                    "canonical_candidate": canonicalize_alias_target(name),
                    "classification": classification,
                }
            )
        else:
            canonical_languages.append(
                {
                    "language": name,
                    "classification": classification,
                    "action": "curate_sample_and_script_profile",
                }
            )

    alias_variants.sort(key=lambda item: (item["canonical_candidate"], item["alias"]))
    canonical_languages.sort(key=lambda item: item["language"])

    grouped_aliases: dict[str, list[str]] = {}
    for item in alias_variants:
        grouped_aliases.setdefault(item["canonical_candidate"], []).append(
            item["alias"]
        )

    return {
        "summary": {
            "script_stubs": len(script_stubs),
            "canonical_language_candidates": len(canonical_languages),
            "alias_variants": len(alias_variants),
            "alias_groups": len(grouped_aliases),
        },
        "scripts": script_stubs,
        "languages": {
            "canonical_candidates": canonical_languages,
            "alias_variants": alias_variants,
            "alias_groups": grouped_aliases,
        },
    }


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for stub proposal generation.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments for the stub-proposal generator.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gap-report",
        type=Path,
        default=_DEFAULT_GAP_REPORT,
        help="Path to the TeX ontology gap report JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Output JSON proposal path",
    )
    return parser.parse_args()


def main() -> int:
    """
    Execute stub proposal generation from the current gap report.

    Returns
    -------
    int
        Process exit status code. Returns ``0`` on success.
    """
    args = parse_args()
    proposal = build_stub_proposal(load_gap_report(args.gap_report))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(proposal, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {args.output}")
    print(
        "[OK] "
        f"script stubs={proposal['summary']['script_stubs']} "
        f"canonical language candidates={proposal['summary']['canonical_language_candidates']} "
        f"alias variants={proposal['summary']['alias_variants']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
