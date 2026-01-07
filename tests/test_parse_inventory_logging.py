import importlib
import logging

import fontshow.parse_font_inventory


def test_inventory_parsing_emits_global_logs(enable_fontshow_logging, caplog):
    importlib.reload(fontshow.parse_font_inventory)

    inventory = {
        "schema_version": "1.0",
        "fonts": [],
    }

    with caplog.at_level(logging.INFO):
        fontshow.parse_font_inventory.parse_inventory(
            inventory,
            level="medium",
        )

    messages = [rec.message for rec in caplog.records]
    assert "font inventory parsing started" in messages
    assert "font inventory parsing completed" in messages


def test_font_entry_logging(enable_fontshow_logging, caplog):
    importlib.reload(fontshow.parse_font_inventory)

    inventory = {
        "schema_version": "1.0",
        "fonts": [
            {
                "path": "/fake/font.ttf",
                "identity": {"family": "Fake", "style": "Regular"},
                "coverage": {},
            }
        ],
    }

    with caplog.at_level(logging.DEBUG):
        fontshow.parse_font_inventory.parse_inventory(
            inventory,
            level="medium",
        )

    messages = [rec.message for rec in caplog.records]

    assert "font entry parsing started" in messages
    assert "font entry parsing completed" in messages


def test_schema_validation_logging(enable_fontshow_logging, caplog):
    importlib.reload(fontshow.parse_font_inventory)

    inventory = {
        "schema_version": "1.0",
        "fonts": [],
    }

    with caplog.at_level(logging.INFO):
        fontshow.parse_font_inventory.parse_inventory(
            inventory,
            level="medium",
        )

    assert any("inventory schema validation" in rec.message for rec in caplog.records)
