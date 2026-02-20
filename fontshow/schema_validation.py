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

from fontshow.global_constants import SCHEMA_VERSION
from fontshow.logging_utils import log, log_trace_cat
from fontshow.types import Severity

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

    schema_path = (
        Path(__file__).parent.parent / "docs" / "schema" / "font_inventory.schema.json"
    )

    if not schema_path.exists():
        msg = f"Schema file not found: {schema_path}"
        log_trace_cat(
            log,
            "validate",
            "schema validation failed",
            extra={
                "schema_version": schema_version,
                "rule": "schema_file_exists",
                "error": msg,
            },
        )
        raise ValueError(msg)

    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)

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
