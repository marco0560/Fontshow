import argparse
import json
import os
from pathlib import Path

from fontshow.create_catalog import (
    build_parser,
    run_create_catalog,
)
from fontshow.platform_metadata import collect_platform_metadata


def _run(tmp_path, inventory):
    tmp_path.mkdir(parents=True, exist_ok=True)

    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps(inventory), encoding="utf-8")

    parser = argparse.ArgumentParser()
    build_parser(parser)

    args = parser.parse_args(
        [
            "--inventory",
            str(inv),
            "--quiet",
        ]
    )

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        rc = run_create_catalog(args)
        assert rc == 0

        tex_files = list(tmp_path.glob("*.tex"))
        assert len(tex_files) == 1
        return tex_files[0].read_bytes()
    finally:
        os.chdir(old_cwd)


def test_deterministic_catalog_output(tmp_path):
    inventory = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": collect_platform_metadata(),
        },
        "fonts": [
            {"name": "Alpha", "coverage": {"languages": ["en"]}},
            {"name": "Beta", "coverage": {"languages": ["fr"]}},
        ],
    }

    out1 = _run(tmp_path / "run1", inventory)
    out2 = _run(tmp_path / "run2", inventory)

    assert out1 == out2
