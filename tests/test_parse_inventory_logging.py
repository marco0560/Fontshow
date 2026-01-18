import importlib
import logging

import fontshow.logging_utils
import fontshow.parse_font_inventory


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
