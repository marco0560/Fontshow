from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, exceptions as jsonschema_exceptions

# Path allo schema (documentato e versionato)
SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "schema"
    / "inventory-1.1.schema.json"
)


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def validate_inventory_schema(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Validate a Fontshow inventory against the JSON Schema v1.1.

    This function supports both raw (schema_version = 1.0) and enriched
    (schema_version = 1.1) inventories.

    It returns structured warnings for recoverable situations and raises
    an exception only for unrecoverable schema violations.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed inventory data.

    Returns
    -------
    list[dict[str, Any]]
        A list of structured warnings.
    """
    warnings: list[dict[str, Any]] = []

    # --- Backward compatibility for raw inventories ----------------------
    if "metadata" not in data:
        data["metadata"] = {"schema_version": "1.0"}
    elif "schema_version" not in data.get("metadata", {}):
        data["metadata"]["schema_version"] = "1.0"
    # ---------------------------------------------------------------------

    schema = _load_schema()
    validator = Draft202012Validator(schema)

    # Collect all schema errors (do not stop at first)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        # Non-recoverable: inventory does not conform to schema at all
        raise jsonschema_exceptions.ValidationError(
            f"Inventory does not conform to schema 1.1: {errors[0].message}"
        )

    # Semantic checks beyond pure schema
    metadata = data.get("metadata", {})
    schema_version = metadata.get("schema_version")

    if schema_version == "1.0":
        warnings.append(
            {
                "code": "schema_version_deprecated",
                "message": (
                    "Inventory schema_version is 1.0. " "Schema 1.1 is recommended."
                ),
                "severity": "info",
            }
        )
    elif schema_version != "1.1":
        warnings.append(
            {
                "code": "schema_version_unknown",
                "message": (
                    f"Unknown schema_version '{schema_version}'. "
                    "Validation performed against schema 1.1."
                ),
                "severity": "warning",
            }
        )

    return warnings
