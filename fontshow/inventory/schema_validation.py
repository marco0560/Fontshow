"""
Inventory schema validation helpers.

This module validates the structural correctness of Fontshow inventory
files against the supported JSON schema version.

Responsibilities
----------------
- Validate inventory structure against the JSON schema.
- Ensure the inventory schema version is supported.
- Report validation failures for malformed inventory data.

Design principles
-----------------
Structural validation is strict and raises errors on failure. Semantic
validation of inventory contents is handled separately by other modules.

Architectural role
------------------
This module belongs to the **inventory subsystem** and performs the
schema validation stage used during inventory parsing and validation.
"""

import json
from importlib.resources import files

from jsonschema import ValidationError, validate

from fontshow.core.global_constants import SCHEMA_VERSION
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import Severity

SUPPORTED_SCHEMA_VERSIONS = {SCHEMA_VERSION}


def _validate_inventory_schema_strict(data: dict) -> None:
    """
    Perform strict schema validation.

    Parameters
    ----------
    data : dict
        Inventory data.

    Raises
    ------
    ValueError
        If schema version is unsupported or validation fails.
    """

    schema_version = data.get("metadata", {}).get("schema_version")

    log_trace_cat(
        log,
        "validate",
        "schema validation started",
        extra={
            "schema_version": schema_version,
        },
    )

    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        msg = f"Unsupported inventory schema version: {schema_version}"
        log_trace_cat(
            log,
            "validate",
            "schema validation failed",
            extra={
                "schema_version": schema_version,
                "ruke": "schema_version_supported",
                "error": msg,
            },
        )
        raise ValueError(msg)

    schema_path = files("fontshow.schema") / "inventory_v1_2.json"

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except FileNotFoundError as err:
        msg = f"Schema resource not found: {schema_path}"
        log_trace_cat(
            log,
            "validate",
            "schema validation failed",
            extra={
                "schema_version": schema_version,
                "rule": "schema_resource_exists",
                "error": msg,
            },
        )
        raise ValueError(msg) from err
    try:
        validate(instance=data, schema=schema)
        log_trace_cat(
            log,
            "validate",
            "schema validation completed",
            extra={
                "schema_version": schema_version,
            },
        )
    except ValidationError as exc:
        msg = f"Inventory schema validation failed: {exc.message}"
        log_trace_cat(
            log,
            "validate",
            "schema validation failed",
            extra={
                "schema_version": schema_version,
                "rule": "jsonschema",
                "error": exc.message,
            },
        )
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

    log_trace_cat(
        log,
        "validate",
        "schema warning evaluation started",
        extra={
            "schema_version": schema_version,
        },
    )

    if schema_version is None:
        log_trace_cat(
            log,
            "validate",
            "schema warning returned",
            extra={
                "code": "schema_version_deprecated",
                "severity": Severity.WARN,
                "schema_version": "1.0",
            },
        )
        return [
            {
                "severity": Severity.WARN,
                "code": "schema_version_deprecated",
                "message": "Missing metadata.schema_version; assuming legacy schema 1.0",
                "schema_version": "1.0",
            }
        ]

    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        log_trace_cat(
            log,
            "validate",
            "schema warning returned",
            extra={
                "code": "schema_version_unknown",
                "severity": Severity.ERROR,
                "schema_version": schema_version,
            },
        )
        return [
            {
                "severity": Severity.ERROR,
                "code": "schema_version_unknown",
                "message": f"Unknown schema version: {schema_version}",
                "schema_version": schema_version,
            }
        ]

    try:
        _validate_inventory_schema_strict(data)
    except ValueError as exc:
        log_trace_cat(
            log,
            "validate",
            "schema warning returned",
            extra={
                "code": "invalid_schema",
                "severity": Severity.ERROR,
                "schema_version": schema_version,
            },
        )
        return [
            {
                "severity": Severity.ERROR,
                "code": "invalid_schema",
                "message": str(exc),
                "schema_version": schema_version,
            }
        ]

    log_trace_cat(
        log,
        "validate",
        "schema warning evaluation completed",
        extra={
            "schema_version": schema_version,
            "warnings_count": len(warnings),
        },
    )
    return warnings
