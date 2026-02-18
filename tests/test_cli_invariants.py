import argparse
import json

from fontshow.create_catalog import build_parser, run_create_catalog


def _run(tmp_path, inventory):
    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inventory), encoding="utf-8")

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(p),
            "--quiet",
        ]
    )

    return run_create_catalog(args)


def test_cli_invalid_schema(tmp_path):
    inv = {
        "metadata": {"schema_version": "1.1"},
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_missing_run_environment(tmp_path):
    inv = {
        "metadata": {"schema_version": "1.2"},
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_platform_mismatch(tmp_path, monkeypatch):
    inv = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": {
                "os": "fake-os",
                "machine": "fake-cpu",
                "execution_context": {"type": "fake"},
            },
        },
        "fonts": [{"name": "A", "coverage": {"languages": ["en"]}}],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_missing_fonts(tmp_path):
    inv = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": {
                "os": "x",
                "machine": "y",
                "execution_context": {"type": "z"},
            },
        }
    }

    rc = _run(tmp_path, inv)
    assert rc == 1


def test_cli_malformed_font_descriptor(tmp_path):
    inv = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": {
                "os": "x",
                "machine": "y",
                "execution_context": {"type": "z"},
            },
        },
        "fonts": ["not-a-dict"],
    }

    rc = _run(tmp_path, inv)
    assert rc == 1
