"""
Inventory validation helpers.

This module implements validation logic applied to parsed Fontshow
inventory structures.

Responsibilities
----------------
- Apply JSON schema validation to inventory documents.
- Perform structural checks on the inventory container and entries.
- Produce deterministic error reporting for invalid inventories.

Design principles
-----------------
Validation helpers operate purely on in-memory inventory structures and
must not perform CLI orchestration or file I/O. They enforce structural
and semantic constraints while keeping pipeline modules focused on
workflow coordination.

Architectural role
------------------
This module belongs to the **inventory subsystem** and implements the
validation stage used during inventory parsing and validation workflows.
"""

from __future__ import annotations

import re
from typing import Any

from fontshow.core.cli_utils import (
    log_err,
    log_info,
    log_ok,
    log_warn,
)
from fontshow.core.logging_utils import log
from fontshow.core.types import Severity
from fontshow.core.warnings import add_structured_warning
from fontshow.diagnostics.inventory_warnings import (
    _format_font_identity,
    _get_font_path_for_diagnostics,
)
from fontshow.inventory.entry_validation import validate_font_entry
from fontshow.inventory.schema_validation import validate_inventory_schema


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


def _apply_schema_validation(data: dict[str, Any]) -> None:
    """
    Validate the inventory schema and attach resulting structured warnings.

    Parameters
    ----------
    data : dict[str, Any]
        Inventory document to validate and annotate.

    Returns
    -------
    None

    Notes
    -----
    The function delegates schema validation to
    `validate_inventory_schema()` and injects the returned warnings into
    the inventory root via `add_structured_warning()`.

    Existing inventory content is preserved; only warning records may be
    appended to the root warning collection.
    """

    log.info(
        "inventory schema validation requested",
        extra={"schema_version": data.get("schema_version")},
    )
    log.debug("inventory schema validation started")

    schema_warnings = validate_inventory_schema(data)

    log.info(
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

        log.debug(
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


def is_non_opentype_face(face: dict) -> bool:
    """
    Canonical detection of non-OpenType / bitmap faces.

    Parameters
    ----------
    face : dict
        Face-level extraction result produced by fontTools helpers.

    Returns
    -------
    bool
        True only when the face was rejected with the specific
        fontTools error indicating that it is not a TrueType or
        OpenType font.

    Notes
    -----
    Preserves EXACT previous behaviour:
    only detects faces rejected by fontTools with the
    specific 'Not a TrueType or OpenType font' error.

    This helper is intentionally narrow and should not be treated as a
    general classifier for all unsupported font formats.
    """
    if face.get("ok") is False:
        err = face.get("error") or ""
        return "Not a TrueType or OpenType font" in err
    return False


def is_structurally_unloadable_face(face: dict) -> bool:
    """
    Detect faces that are structurally missing mandatory OpenType tables.

    Parameters
    ----------
    face : dict
        Face-level extraction result produced by fontTools helpers.

    Returns
    -------
    bool
        True when the face claims successful extraction but lacks
        mandatory OpenType tables or any supported glyph table.

    Notes
    -----
    Deterministic, fontTools-derived check (no LaTeX, no luaotfload-tool).
    Conservative: only flags faces that claim ok=True but have missing tables.

    The check is limited to table-presence heuristics and does not prove
    that a face is otherwise valid or renderable.
    """
    if face.get("ok") is not True:
        return False

    tables = face.get("tables")
    if not isinstance(tables, list):
        return False

    table_set = set(tables)

    required = {"cmap", "head", "hhea", "hmtx", "maxp", "name", "post"}
    if not required.issubset(table_set):
        return True

    # Must have a glyph table: TrueType glyf or CFF/CFF2.
    return (
        ("glyf" not in table_set)
        and ("CFF " not in table_set)
        and ("CFF2" not in table_set)
    )


_STYLE_LEAK_RE = re.compile(
    r"\b("
    r"bold|italic|oblique|light|regular|medium|"
    r"semibold|extrabold|black|thin|"
    r"condensed|narrow|extended"
    r")\b",
    re.IGNORECASE,
)


def has_style_leak_in_family(desc: dict) -> bool:
    """
    Detect whether a family name appears to contain style qualifiers.

    Parameters
    ----------
    desc : dict
        Font descriptor whose family field is inspected.

    Returns
    -------
    bool
        True if the family name matches the style-leak heuristic regex.

    Notes
    -----
    This helper is used as a conservative signal that style information
    may have leaked into the normalized family field.
    """
    fam = desc.get("family", "")
    if not isinstance(fam, str):
        return False
    return bool(_STYLE_LEAK_RE.search(fam))
