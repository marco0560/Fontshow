import argparse
import json
import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

from fontshow import __version__
from fontshow.schema_validation import validate_inventory_schema


def add_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )


def cli_validate_inventory() -> int:
    """
    CLI entry point for validating a Fontshow inventory against the JSON schema.
    """
    parser = argparse.ArgumentParser(
        prog="fontshow-validate",
        description="Validate a Fontshow inventory file against the JSON Schema.",
    )
    parser.add_argument(
        "path",
        help="Path to the inventory JSON file to validate",
    )

    args = parser.parse_args()
    inventory_path = Path(args.path)

    if not inventory_path.exists():
        print(f"Error: file not found: {inventory_path}", file=sys.stderr)
        return 1

    try:
        with inventory_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON file: {e}", file=sys.stderr)
        return 1

    try:
        warnings = validate_inventory_schema(data)
    except ValidationError as e:
        print("Schema validation failed:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 1

    for w in warnings:
        print(f"[{w['severity']}] {w['code']}: {w['message']}")

    print("Schema validation passed.")
    return 0
