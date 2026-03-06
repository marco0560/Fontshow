import argparse
import json
import os
from pathlib import Path

from fontshow.create_catalog import (
    build_parser,
    run_create_catalog,
)
from fontshow.platform_metadata import collect_platform_metadata


def test_only_tex_artifact_created(tmp_path):
    inventory = {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": collect_platform_metadata(),
        },
        "fonts": [
            {"name": "Alpha", "coverage": {"languages": ["en"]}},
        ],
    }

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
    finally:
        os.chdir(old_cwd)

    files = list(tmp_path.iterdir())

    # Expect exactly:
    # - inventory file
    # - generated .tex file
    assert len(files) == 2

    tex_files = [p for p in files if p.suffix == ".tex"]
    assert len(tex_files) == 1

    # Ensure no unexpected artifacts
    for p in files:
        assert p.suffix in {".json", ".tex"}
