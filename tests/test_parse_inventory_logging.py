import argparse
import importlib
import json
import logging
from pathlib import Path

import fontshow.logging_utils
import fontshow.parse_font_inventory
from tests.helpers import minimal_valid_entry


def test_inventory_parsing_emits_global_logs(
    enable_fontshow_logging,
    capture_fontshow_logs,
):
    importlib.reload(fontshow.logging_utils)
    importlib.reload(fontshow.parse_font_inventory)

    inventory = {
        "schema_version": "1.0",
        "fonts": [],
    }

    with capture_fontshow_logs.at_level(logging.INFO, logger="fontshow"):
        fontshow.parse_font_inventory.parse_inventory(
            inventory,
            level="medium",
        )

    messages = [rec.getMessage() for rec in capture_fontshow_logs.records]

    assert "font inventory parsing started" in messages
    assert "font inventory parsing completed" in messages


def test_schema_validation_logging(
    enable_fontshow_logging,
    capture_fontshow_logs,
):
    importlib.reload(fontshow.logging_utils)
    importlib.reload(fontshow.parse_font_inventory)

    inventory = {
        "schema_version": "1.0",
        "fonts": [],
    }

    with capture_fontshow_logs.at_level(logging.INFO, logger="fontshow"):
        fontshow.parse_font_inventory.parse_inventory(
            inventory,
            level="medium",
        )

    messages = [rec.getMessage() for rec in capture_fontshow_logs.records]

    assert "inventory schema validation requested" in messages
    assert "inventory schema validation completed" in messages


def test_parse_inventory_verbosity_levels(capsys, tmp_path):
    """
    Regression test for CLI verbosity semantics (Decision 0009).

    This test MUST provide an input file explicitly because it calls the
    runner directly (bypassing argparse defaults).
    """

    from fontshow.parse_font_inventory import main

    # Minimal valid inventory for validate-inventory mode
    inventory = {
        "metadata": {"schema_version": "1.0"},
        "fonts": [minimal_valid_entry()],
    }

    input_path = tmp_path / "font_inventory.json"
    input_path.write_text(json.dumps(inventory), encoding="utf-8")

    class Args:
        input = Path(input_path)
        validate_inventory = True
        quiet = False
        verbose = False
        infer_level = "medium"
        output = tmp_path / "font_inventory_enriched.json"

    # default
    args = Args()
    main(args)
    captured_default = capsys.readouterr().out

    # verbose
    args.verbose = True
    main(args)
    captured_verbose = capsys.readouterr().out

    # quiet
    args.verbose = False
    args.quiet = True
    main(args)
    captured_quiet = capsys.readouterr().out

    # Assertions
    assert captured_default.strip() != ""
    assert captured_verbose.strip() != ""
    assert captured_verbose != captured_default
    assert captured_quiet.strip() == ""


def test_parse_inventory_verbose_emits_schema_aware_identity(capsys, tmp_path):
    inventory = {
        "metadata": {"schema_version": "1.0"},
        "fonts": [
            {
                "identity": {
                    "file": "/fonts/A.ttf",
                    "face_index": 0,
                },
                "warnings": [
                    {
                        "code": "language_dropped",
                        "message": "Dropped language 'wen'",
                        "severity": "warning",
                    }
                ],
            },
            {
                "identity": {
                    "file": "/fonts/B.ttf",
                    "face_index": 1,
                },
                "warnings": [
                    {
                        "code": "language_dropped",
                        "message": "Dropped language 'pap'",
                        "severity": "warning",
                    }
                ],
            },
        ],
    }

    input_path = tmp_path / "inventory.json"
    output_path = tmp_path / "out.json"
    input_path.write_text(json.dumps(inventory))

    args = argparse.Namespace(
        input=input_path,
        output=output_path,
        validate_inventory=False,
        infer_level="medium",
        verbose=True,
        quiet=False,
    )

    fontshow.parse_font_inventory.run_parse_font_inventory(args)

    out = capsys.readouterr().out

    assert "font[0] A.ttf:0" in out
    assert "font[1] B.ttf:1" in out
