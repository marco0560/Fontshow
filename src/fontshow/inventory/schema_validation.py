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


def _schema_resource_name(schema_version: str) -> str:
    """
    Return the bundled JSON schema filename for a schema version.

    Parameters
    ----------
    schema_version : str
        Supported inventory schema version.

    Returns
    -------
    str
        Bundled schema filename for the requested version.
    """
    return f"inventory_v{schema_version.replace('.', '_')}.json"


def _validate_inventory_schema_strict(data: dict) -> None:
    """
    Perform strict schema validation.

    Parameters
    ----------
    data : dict
        Inventory data.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If `metadata.schema_version` is unsupported.
    ValueError
        If the schema resource file cannot be found.
    ValueError
        If the inventory fails JSON Schema validation.
    json.JSONDecodeError
        If the bundled schema resource exists but contains invalid JSON.

    Notes
    -----
    The function normalizes jsonschema validation failures into
    `ValueError` for callers, but schema resource loading may still
    propagate low-level JSON decoding failures if the bundled schema
    file is malformed.
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

    schema_path = files("fontshow.schema") / _schema_resource_name(schema_version)

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

    Parameters
    ----------
    data : dict
        Inventory document to validate.

    Returns
    -------
    list[dict]
        Structured schema warnings, empty if valid.

    Raises
    ------
    None
        This function is backward-compatible and MUST NOT raise.
        ValueError is handled internally

    Notes
    -----
    Missing or unknown schema versions are converted into structured
    error records instead of exceptions.
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
                "code": "schema_version_missing",
                "severity": Severity.ERROR,
                "schema_version": None,
            },
        )
        return [
            {
                "severity": Severity.ERROR,
                "code": "schema_version_missing",
                "message": (
                    "Missing metadata.schema_version; "
                    f"required schema version is {SCHEMA_VERSION}"
                ),
                "schema_version": None,
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
