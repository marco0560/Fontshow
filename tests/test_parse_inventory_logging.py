import argparse
import importlib
import json
import logging
from pathlib import Path

import fontshow.cli.parse_inventory
import fontshow.core.logging_utils
from tests.helpers import minimal_font_entry_v12, minimal_inventory_v12


def test_inventory_parsing_emits_global_logs(
    enable_fontshow_logging,
    capture_fontshow_logs,
):
    importlib.reload(fontshow.core.logging_utils)
    importlib.reload(fontshow.cli.parse_inventory)

    inventory = minimal_inventory_v12()

    with capture_fontshow_logs.at_level(logging.INFO, logger="fontshow"):
        fontshow.cli.parse_inventory.parse_inventory(
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
    importlib.reload(fontshow.core.logging_utils)
    importlib.reload(fontshow.cli.parse_inventory)

    inventory = minimal_inventory_v12()

    with capture_fontshow_logs.at_level(logging.INFO, logger="fontshow"):
        fontshow.cli.parse_inventory.parse_inventory(
            inventory,
            level="medium",
        )

    messages = [rec.getMessage() for rec in capture_fontshow_logs.records]

    assert "inventory schema validation requested" in messages
    assert "inventory schema validation completed" in messages


def test_parse_inventory_verbosity_levels(capsys, tmp_path):
    """
    CLI verbosity contract (strict mode):

    quiet   -> silent
    default -> limited output
    verbose -> detailed output
    """

    from fontshow.cli.parse_inventory import main
    from fontshow.core.cli_utils import set_cli_mode

    # --- HARD RESET of global CLI state (test isolation) ---
    set_cli_mode(False, False)

    inventory = minimal_inventory_v12()

    input_path = tmp_path / "font_inventory.json"
    input_path.write_text(json.dumps(inventory), encoding="utf-8")

    class Args:
        input = Path(input_path)
        validate_inventory = True
        quiet = False
        verbose = False
        infer_level = "medium"
        output = tmp_path / "font_inventory_enriched.json"

    # -------------------------------
    # quiet → silent
    # -------------------------------
    set_cli_mode(True, False)
    args = Args()
    args.quiet = True
    args.verbose = False
    main(args)
    captured_quiet = capsys.readouterr().out

    # -------------------------------
    # default → limited output
    # -------------------------------
    set_cli_mode(False, False)
    args = Args()
    args.quiet = False
    args.verbose = False
    main(args)
    captured_default = capsys.readouterr().out

    # -------------------------------
    # verbose → detailed output
    # -------------------------------
    set_cli_mode(False, True)
    args = Args()
    args.quiet = False
    args.verbose = True
    main(args)
    captured_verbose = capsys.readouterr().out

    assert captured_quiet.strip() == ""
    assert captured_default.strip() != ""
    assert captured_verbose.strip() != ""


def test_parse_inventory_verbose_emits_schema_aware_identity(capsys, tmp_path):
    inventory = minimal_inventory_v12()

    font_a = minimal_font_entry_v12()
    font_a["path"] = "/fonts/A.ttf"
    font_a["family"] = "A"
    font_a["warnings"] = [
        {
            "code": "language_dropped",
            "message": "Dropped language 'wen'",
            "severity": "warning",
        }
    ]

    font_b = minimal_font_entry_v12()
    font_b["path"] = "/fonts/B.ttf"
    font_b["family"] = "B"
    font_b["warnings"] = [
        {
            "code": "language_dropped",
            "message": "Dropped language 'pap'",
            "severity": "warning",
        }
    ]

    inventory["fonts"] = [font_a, font_b]

    input_path = tmp_path / "inventory.json"
    output_path = tmp_path / "out.json"
    input_path.write_text(json.dumps(inventory))

    args = argparse.Namespace(
        input=input_path,
        output=output_path,
        validate_inventory=False,
        infer_level="medium",
        strict_bcp47=False,
        verbose=True,
        quiet=False,
    )

    fontshow.cli.parse_inventory.run_parse_font_inventory(args)

    captured = capsys.readouterr()
    combined = captured.out + captured.err

    assert "normalized_languages" in combined or "dropped_languages" in combined
    assert "font[1] B.ttf" in combined
