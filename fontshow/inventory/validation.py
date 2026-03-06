"""
Inventory validation helpers.

This module contains the validation logic used by the inventory parsing
pipeline to ensure that font inventory JSON data conforms to the expected
schema and structural constraints before further processing.

Responsibilities
----------------
- Apply JSON schema validation to the inventory document.
- Perform structural checks on the inventory container and entries.
- Provide deterministic error reporting for invalid inventories.

Design notes
------------
The functions in this module are called from the `parse_inventory` pipeline
but do not perform any orchestration, CLI interaction, or file I/O. They
operate purely on in-memory data structures and raise exceptions when
validation fails.

This separation keeps the pipeline module (`parse_font_inventory.py`)
focused on orchestration while the inventory domain module encapsulates
all validation rules.
"""

from __future__ import annotations

import logging
from typing import Any

from fontshow.cli_utils import (
    log_err,
    log_info,
    log_ok,
    log_warn,
)
from fontshow.diagnostics.inventory_warnings import (
    _format_font_identity,
    _get_font_path_for_diagnostics,
)
from fontshow.inventory.entry_validation import validate_font_entry
from fontshow.schema_validation import validate_inventory_schema
from fontshow.types import Severity
from fontshow.warnings import add_structured_warning

# ============================================================
# Set up logger
# ============================================================
logger = logging.getLogger("fontshow")


def validate_inventory(
    data: object,
) -> int:
    """
    Validate a Fontshow font inventory structure.

     Parameters
     ----------
     data : dict[str, Any]
         Parsed inventory JSON object.

     Returns
     -------
     int
         Number of font entries with fatal validation errors.
         Zero indicates a valid inventory.

     Notes
     -----
     - Performs both fatal validation and non-fatal consistency checks.
     - Validation is exhaustive: all entries are inspected in one pass.
     - Function never raises and does not mutate inference results.
     - Structured warnings may be injected into the inventory.

     This function performs two distinct classes of checks:

     1. Fatal validation errors:
        These indicate that one or more font entries are structurally or
        semantically invalid according to the current data model.
        Fatal errors are reported as ERROR and cause the validation to fail
        (non-zero return value).

     2. Non-fatal consistency warnings:
        These highlight incomplete or suspicious entries that may still be
        usable, but are worth reporting to the user.
        Warnings do not cause validation failure.
    """
    fatal_errors = 0
    warnings = 0

    from collections.abc import Mapping

    if not isinstance(data, Mapping):
        log_err("Inventory root is not a JSON object")
        return 1

    data = dict(data)  # defensive copy to allow safe normalization
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        log_err("'metadata' field missing or not an object (schema 1.2 required)")
        return 1

    schema_version = metadata.get("schema_version")
    if schema_version != "1.2":
        log_err(
            f"Unsupported schema_version '{schema_version}': only '1.2' is accepted"
        )
        return 1

    raw_fonts = data.get("fonts")

    if not isinstance(raw_fonts, list):
        log_err("'fonts' field missing or not a list")
        return 1

    fonts: list[dict[str, Any]] = [f for f in raw_fonts if isinstance(f, dict)]

    for idx, font in enumerate(fonts):
        # ---------- Fatal entry validation ----------
        entry_errors = validate_font_entry(font, index=idx)
        if entry_errors:
            fatal_errors += 1
            path = _get_font_path_for_diagnostics(font)

            log_err(f"[ERR] font[{idx}]")
            log_err(f"  path: {path}")
            for err in entry_errors:
                log_err(f"  - {err}")
    for idx, font in enumerate(fonts):
        ident = _format_font_identity(font, index=idx)
        for warning in font.get("warnings", []):
            log_warn(f"Warning [{ident}]: {warning['code']} - {warning['message']}")

    if fatal_errors == 0:
        # NOTE:
        # Do NOT replace this with a generic "OK" message.
        # Unlike preflight or dump-fonts, parse-inventory is a
        # user-facing diagnostic command and must emit a
        # human-readable success message.
        #
        # See: docs/decisions/0009-cli-verbosity-contract.md
        log_ok(
            "Inventory validation completed (no fatal errors)",
            f"Validation completed for {len(fonts)} font entries",
        )
    else:
        log_info(
            "Inventory validation completed with fatal errors",
            f"Validation completed for {len(fonts)} font entries"
            f" with {fatal_errors} fatal errors and {warnings} warnings",
        )

    return fatal_errors


# ============================================================
# Helper: schema validation + warning injection
# ============================================================


def _apply_schema_validation(data: dict[str, Any]) -> None:
    """Validate schema and inject structured warnings into inventory."""

    logger.info(
        "inventory schema validation requested",
        extra={"schema_version": data.get("schema_version")},
    )
    logger.debug("inventory schema validation started")

    schema_warnings = validate_inventory_schema(data)

    logger.info(
        "inventory schema validation completed",
        extra={
            "schema_version": data.get("schema_version"),
            "warnings_count": len(schema_warnings),
        },
    )

    if schema_warnings:
        severity_counts: dict[Severity, int] = {}
        for w in schema_warnings:
            sev = w.get("severity", Severity.WARN)
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        logger.debug(
            "inventory schema validation produced warnings",
            extra={
                "schema_version": data.get("schema_version"),
                "severity_counts": severity_counts,
            },
        )

    for warning in schema_warnings:
        add_structured_warning(
            data,
            code=warning["code"],
            message=warning["message"],
            severity=warning["severity"],
        )
