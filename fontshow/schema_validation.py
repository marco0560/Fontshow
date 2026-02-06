"""
Schema validation utilities for Fontshow inventory files.

This module validates the *structural correctness* of inventory files.

Design principles
-----------------
- Structural validation is strict and raises on failure
- Public API remains backward-compatible
- Semantic validation is handled elsewhere
- Schema version selection is explicit
"""

import json
from pathlib import Path

from jsonschema import ValidationError, validate

SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}


def _validate_inventory_schema_strict(data: dict, *, schema_version: str) -> None:
    """
    Perform strict schema validation.

    Parameters
    ----------
    data : dict
        Inventory data.
    schema_version : str
        Schema version to validate against.

    Raises
    ------
    ValueError
        If schema version is unsupported or validation fails.
    """

    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        msg = f"Unsupported inventory schema version: {schema_version}"
        raise ValueError(msg)

    schema_path = (
        Path(__file__).parent.parent
        / "docs"
        / "schema"
        / f"inventory-{schema_version}.schema.json"
    )

    if not schema_path.exists():
        msg = f"Schema file not found: {schema_path}"
        raise ValueError(msg)

    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        msg = f"Inventory schema validation failed: {exc.message}"
        raise ValueError(msg) from exc


def validate_inventory_schema(data: dict) -> list[dict]:
    """
    Validate inventory structure and return structured warnings.

    This function is backward-compatible and MUST NOT raise.

    Returns
    -------
    list[dict]
        Structured schema warnings, empty if valid.
    """

    warnings: list[dict] = []

    schema_version = data.get("metadata", {}).get("schema_version")

    if schema_version is None:
        return [
            {
                "severity": "warning",
                "code": "schema_version_deprecated",
                "message": "Missing metadata.schema_version; assuming legacy schema 1.0",
                "schema_version": "1.0",
            }
        ]

    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        return [
            {
                "severity": "error",
                "code": "schema_version_unknown",
                "message": f"Unknown schema version: {schema_version}",
                "schema_version": schema_version,
            }
        ]

    try:
        _validate_inventory_schema_strict(
            data,
            schema_version=schema_version,
        )
    except ValueError as exc:
        return [
            {
                "severity": "error",
                "code": "invalid_schema",
                "message": str(exc),
                "schema_version": schema_version,
            }
        ]

    return warnings
