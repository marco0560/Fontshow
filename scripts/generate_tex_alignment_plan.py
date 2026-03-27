#!/usr/bin/env python3
"""
Generate a staged TeX-versus-ontology alignment plan.

This maintenance script consumes the previously generated TeX audit
reports and emits a deterministic JSON plan describing:

- current production coverage,
- alias-only support work that should stay outside production ontology,
- true ontology curation work split into fixed-size batches.

Responsibilities
----------------
- Summarize the current distance between local TeX support and ontology.
- Separate support-script alias work from production ontology work.
- Produce deterministic batches for staged ontology expansion.

Design principles
-----------------
The planner is conservative and bookkeeping-oriented. It does not infer
specimens, invent ontology rows, or modify source files directly.

Architectural role
------------------
This script belongs to the developer tooling layer and supports the
manual LaTeX/ontology alignment workflow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

_DEFAULT_GAP_REPORT = Path("reports/tex_ontology_gap_report.json")
_DEFAULT_STUB_PROPOSAL = Path("reports/tex_ontology_stub_proposal.json")
_DEFAULT_REVIEWED_BATCH = Path("reports/first_reviewed_tex_batch.json")
_DEFAULT_OUTPUT = Path("reports/tex_alignment_plan.json")


def load_json_report(path: Path) -> dict[str, Any]:
    """
    Load a JSON maintenance report from disk.

    Parameters
    ----------
    path : pathlib.Path
        Path to the JSON report.

    Returns
    -------
    dict[str, object]
        Parsed JSON payload.
    """
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    """
    Split a list of items into deterministic fixed-size chunks.

    Parameters
    ----------
    items : list[dict[str, object]]
        Ordered item list to partition.
    size : int
        Maximum size of each chunk.

    Returns
    -------
    list[list[dict[str, object]]]
        Partitioned item chunks preserving input order.

    Raises
    ------
    ValueError
        Raised when ``size`` is smaller than ``1``.
    """
    if size < 1:
        msg = "batch size must be at least 1"
        raise ValueError(msg)
    return [items[index : index + size] for index in range(0, len(items), size)]


def build_alignment_plan(
    gap_report: dict[str, Any],
    stub_proposal: dict[str, Any],
    reviewed_batch: dict[str, Any],
    *,
    batch_size: int = 10,
) -> dict[str, Any]:
    """
    Build a staged alignment plan from the TeX audit reports.

    Parameters
    ----------
    gap_report : dict[str, object]
        Parsed payload from ``generate_tex_ontology_gap_report.py``.
    stub_proposal : dict[str, object]
        Parsed payload from ``generate_tex_ontology_stubs.py``.
    reviewed_batch : dict[str, object]
        Parsed payload from ``generate_first_reviewed_tex_batch.py``.
    batch_size : int, default=10
        Maximum number of ontology-candidate items per staged batch.

    Returns
    -------
    dict[str, object]
        JSON-serializable staged alignment plan.

    Raises
    ------
    ValueError
        Raised when ``batch_size`` is smaller than ``1``.
    """
    if batch_size < 1:
        msg = "batch size must be at least 1"
        raise ValueError(msg)

    local_counts = gap_report["local_counts"]
    ontology_counts = gap_report["ontology_counts"]
    missing = gap_report["missing"]
    proposal_languages = stub_proposal["languages"]
    proposal_scripts = stub_proposal["scripts"]
    reviewed_languages = reviewed_batch["languages"]["aliases"]
    reviewed_pipeline_normalized_languages = reviewed_batch["languages"].get(
        "pipeline_normalized", []
    )
    reviewed_non_canonical_modules = reviewed_batch["languages"].get(
        "non_canonical_modules", []
    )
    reviewed_scripts = reviewed_batch["scripts"]["aliases"]
    production_script_candidates = [
        item for item in proposal_scripts if item["classification"] == "needs_specimen"
    ]

    script_batches = [
        {
            "batch": index,
            "kind": "scripts",
            "items": chunk,
        }
        for index, chunk in enumerate(
            _chunked(production_script_candidates, batch_size),
            start=1,
        )
    ]
    language_batches = [
        {
            "batch": index,
            "kind": "languages",
            "items": chunk,
        }
        for index, chunk in enumerate(
            _chunked(proposal_languages["canonical_candidates"], batch_size),
            start=1,
        )
    ]

    return {
        "policy": {
            "batch_size": batch_size,
            "alias_handling": ("support_only_aliases_stay_outside_production_ontology"),
        },
        "distance": {
            "local_tex_surface": local_counts,
            "production_ontology": ontology_counts,
            "missing": {
                "fontspec_scripts": len(missing["fontspec_scripts"]),
                "polyglossia_languages": len(missing["polyglossia_languages"]),
            },
        },
        "buckets": {
            "already_covered": {
                "fontspec_scripts": len(gap_report["covered"]["fontspec_scripts"]),
                "polyglossia_languages": len(
                    gap_report["covered"]["polyglossia_languages"]
                ),
            },
            "support_alias_work": {
                "script_alias_candidates": len(
                    [
                        item
                        for item in missing["fontspec_scripts"]
                        if item["classification"] == "needs_alias_mapping"
                    ]
                ),
                "language_alias_variants": len(proposal_languages["alias_variants"]),
                "pipeline_normalized_languages": len(
                    proposal_languages["pipeline_normalized"]
                ),
                "non_canonical_modules": len(
                    proposal_languages.get("non_canonical_modules", [])
                ),
                "reviewed_language_aliases": len(reviewed_languages),
                "reviewed_pipeline_normalized_languages": len(
                    reviewed_pipeline_normalized_languages
                ),
                "reviewed_non_canonical_modules": len(reviewed_non_canonical_modules),
                "reviewed_script_aliases": len(reviewed_scripts),
            },
            "production_ontology_work": {
                "script_stubs": len(production_script_candidates),
                "canonical_language_candidates": len(
                    proposal_languages["canonical_candidates"]
                ),
            },
            "non_ontology_local_tex_entries": {
                "fontspec_scripts": [
                    item["name"]
                    for item in missing["fontspec_scripts"]
                    if item["classification"] == "should_not_be_language"
                ]
            },
        },
        "support_work": {
            "reviewed_language_aliases": reviewed_languages,
            "reviewed_pipeline_normalized_languages": (
                reviewed_pipeline_normalized_languages
            ),
            "reviewed_non_canonical_modules": reviewed_non_canonical_modules,
            "reviewed_script_aliases": reviewed_scripts,
        },
        "production_batches": {
            "scripts": script_batches,
            "languages": language_batches,
        },
    }


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for alignment plan generation.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments for the alignment-plan generator.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gap-report",
        type=Path,
        default=_DEFAULT_GAP_REPORT,
        help="Path to the TeX ontology gap report JSON",
    )
    parser.add_argument(
        "--stub-proposal",
        type=Path,
        default=_DEFAULT_STUB_PROPOSAL,
        help="Path to the TeX ontology stub proposal JSON",
    )
    parser.add_argument(
        "--reviewed-batch",
        type=Path,
        default=_DEFAULT_REVIEWED_BATCH,
        help="Path to the first reviewed TeX batch JSON",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Maximum number of ontology-candidate items per staged batch",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Output JSON plan path",
    )
    return parser.parse_args()


def main() -> int:
    """
    Execute staged alignment plan generation.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process exit status code. Returns ``0`` on success.
    """
    args = parse_args()
    plan = build_alignment_plan(
        load_json_report(args.gap_report),
        load_json_report(args.stub_proposal),
        load_json_report(args.reviewed_batch),
        batch_size=args.batch_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {args.output}")
    print(
        "[OK] "
        f"script batches={len(plan['production_batches']['scripts'])} "
        f"language batches={len(plan['production_batches']['languages'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
