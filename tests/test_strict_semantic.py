import argparse
import json

from fontshow.create_catalog import build_parser, run_create_catalog


def test_strict_semantic_fails(tmp_path):
    inv = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [
            {
                "name": "BrokenFont",
                "coverage": {"languages": ["xx"]},
            }
        ],
    }

    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inv), encoding="utf-8")

    # Create real parser (as CLI does)
    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(p),
            "--strict-semantic",
            "--quiet",
        ]
    )

    rc = run_create_catalog(args)
    assert rc == 1


def test_strict_semantic_fails_on_non_language_issue(tmp_path):
    inv = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [
            {
                "name": "SomeFont",
                "coverage": {"languages": ["en"]},
            }
        ],
        # Simulate a semantic issue not related to language
        "warnings": [
            {
                "severity": "warning",
                "code": "semantic_inconsistency",
                "message": "Inconsistent metadata detected",
            }
        ],
    }

    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inv), encoding="utf-8")

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(p),
            "--strict-semantic",
            "--quiet",
        ]
    )

    rc = run_create_catalog(args)
    assert rc == 1
