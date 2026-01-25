"""
Schema validation utilities for Fontshow inventory files.

This module validates the *structural correctness* of inventory files.

Supported schema versions:
    - 1.0
    - 1.1

This module performs schema validation only.
Semantic validation is handled separately.
"""

import json
from pathlib import Path

from jsonschema import ValidationError, validate

SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}


def validate_inventory_schema(data: dict, *, schema_version: str) -> None:
    """
    Validate inventory data against a specific schema version.

    Parameters
    ----------
    data : dict
        Parsed inventory data.
    schema_version : str
        Inventory schema version to validate against.

    Raises
    ------
    ValueError
        If the schema version is unsupported or the input
        does not conform to the selected schema.
    """

    if not isinstance(schema_version, str):
        raise ValueError("schema_version must be a string")

    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported inventory schema version: {schema_version}")

    schema_path = (
        Path(__file__).parent.parent
        / "docs"
        / "schema"
        / f"inventory-{schema_version}.schema.json"
    )

    if not schema_path.exists():
        raise ValueError(f"Schema file not found: {schema_path}")

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        raise ValueError(f"Inventory schema validation failed: {exc.message}") from exc
