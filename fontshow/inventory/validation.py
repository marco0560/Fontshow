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

from collections import Counter, defaultdict
from typing import Any

from fontshow.constants.inventory import (
    STYLE_LEAK_RE,
    STYLE_SLANT_TOKENS,
    STYLE_WEIGHT_RANGES,
    STYLE_WIDTH_TOKENS,
)
from fontshow.core.cli_utils import (
    log_err,
    log_info,
    log_ok,
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

_VALIDATION_SUMMARY_WARNING_CODES = frozenset(
    {
        "missing_weight_class",
        "missing_width_class",
        "missing_subfamily",
    }
)


def _record_fatal_validation(
    font: dict[str, Any],
    *,
    index: int,
    fatal_categories: Counter[str],
    fatal_examples: dict[str, list[str]],
) -> int:
    """
    Validate one font entry and aggregate fatal error categories.

    Parameters
    ----------
    font : dict[str, Any]
        Inventory font entry being validated.
    index : int
        Position of the entry within the inventory.
    fatal_categories : collections.Counter[str]
        Counter updated in place with fatal error messages.
    fatal_examples : dict[str, list[str]]
        Mapping updated in place with sample paths per fatal category.

    Returns
    -------
    int
        ``1`` when the entry has at least one fatal error, otherwise ``0``.
    """
    entry_errors = validate_font_entry(font, index=index)
    if not entry_errors:
        return 0

    path = _get_font_path_for_diagnostics(font)
    for err in entry_errors:
        fatal_categories[err] += 1
        if path is not None and len(fatal_examples[err]) < 5:
            fatal_examples[err].append(path)

    return 1


def _record_validation_observations(
    font: dict[str, Any],
    *,
    index: int,
    observation_counts: Counter[str],
    observation_examples: dict[str, list[str]],
) -> None:
    """
    Aggregate non-fatal validation observations for one font entry.
    """
    ident = _format_font_identity(font, index=index)

    sample_text = font.get("sample_text")
    if isinstance(sample_text, dict) and not sample_text.get("text"):
        observation_counts["missing_internal_sample_text"] += 1
        if len(observation_examples["missing_internal_sample_text"]) < 5:
            observation_examples["missing_internal_sample_text"].append(ident)

    specimen_strategy = font.get("specimen_strategy")
    strategy_map = {
        "internal": "specimen_from_internal",
        "script": "specimen_from_script",
        "cmap": "specimen_from_cmap",
    }
    strategy_key = (
        strategy_map[specimen_strategy]
        if isinstance(specimen_strategy, str) and specimen_strategy in strategy_map
        else None
    )
    if strategy_key is not None:
        observation_counts[strategy_key] += 1
        if len(observation_examples[strategy_key]) < 5:
            observation_examples[strategy_key].append(ident)

    coverage = font.get("coverage")
    inference = font.get("inference")
    declared_languages = (
        coverage.get("languages") if isinstance(coverage, dict) else None
    )
    inferred_languages = (
        inference.get("languages") if isinstance(inference, dict) else None
    )

    if not declared_languages:
        observation_counts["missing_declared_languages"] += 1
        if len(observation_examples["missing_declared_languages"]) < 5:
            observation_examples["missing_declared_languages"].append(ident)
        if inferred_languages:
            observation_counts["inferred_languages_used"] += 1
            if len(observation_examples["inferred_languages_used"]) < 5:
                observation_examples["inferred_languages_used"].append(ident)


def _record_validation_warnings(
    font: dict[str, Any],
    *,
    index: int,
    warning_categories: Counter[str],
    warning_examples: dict[str, list[str]],
) -> None:
    """
    Aggregate actionable warning codes embedded in one font entry.
    """
    ident = _format_font_identity(font, index=index)
    raw_warnings = font.get("warnings", [])
    warning_list = raw_warnings if isinstance(raw_warnings, list) else []

    for warning in warning_list:
        code = warning.get("code")
        if not isinstance(code, str) or code not in _VALIDATION_SUMMARY_WARNING_CODES:
            continue
        warning_categories[code] += 1
        if len(warning_examples[code]) < 5:
            warning_examples[code].append(ident)


def _emit_validation_summary(
    *,
    fatal_categories: Counter[str],
    fatal_examples: dict[str, list[str]],
    warning_categories: Counter[str],
    warning_examples: dict[str, list[str]],
    observation_summary: tuple[Counter[str], dict[str, list[str]]],
) -> None:
    """
    Emit grouped validation summaries and verbose examples.
    """
    observation_counts, observation_examples = observation_summary

    if fatal_categories:
        summary = ", ".join(
            f"{message} ({count})" for message, count in fatal_categories.most_common()
        )
        log_err(f"Fatal validation categories: {summary}")
        fatal_details = ["Fatal validation examples:"]
        for message, examples in fatal_examples.items():
            if not examples:
                continue
            fatal_details.append(f"- {message}")
            for example in examples:
                fatal_details.append(f"  {example}")
        log_info(
            "Fatal validation examples available",
            verbose="\n".join(fatal_details),
        )

    if warning_categories:
        log_info(
            "Validation warning summary",
            extra=dict(sorted(warning_categories.items())),
        )
        warning_details = ["Validation warning examples:"]
        for code, examples in warning_examples.items():
            if not examples:
                continue
            warning_details.append(f"- {code}")
            for example in examples:
                warning_details.append(f"  {example}")
        log_info(
            "Validation warning examples available",
            verbose="\n".join(warning_details),
        )

    if observation_counts:
        log_info(
            "Validation observations", extra=dict(sorted(observation_counts.items()))
        )
        observation_details = ["Validation observation examples:"]
        for code, examples in observation_examples.items():
            if not examples:
                continue
            observation_details.append(f"- {code}")
            for example in examples:
                observation_details.append(f"  {example}")
        log_info(
            "Validation observation examples available",
            verbose="\n".join(observation_details),
        )


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
    fatal_categories: Counter[str] = Counter()
    fatal_examples: dict[str, list[str]] = defaultdict(list)
    warning_categories: Counter[str] = Counter()
    warning_examples: dict[str, list[str]] = defaultdict(list)
    observation_counts: Counter[str] = Counter()
    observation_examples: dict[str, list[str]] = defaultdict(list)

    for idx, font in enumerate(fonts):
        fatal_errors += _record_fatal_validation(
            font,
            index=idx,
            fatal_categories=fatal_categories,
            fatal_examples=fatal_examples,
        )
        _record_validation_observations(
            font,
            index=idx,
            observation_counts=observation_counts,
            observation_examples=observation_examples,
        )
        _record_validation_warnings(
            font,
            index=idx,
            warning_categories=warning_categories,
            warning_examples=warning_examples,
        )

    _emit_validation_summary(
        fatal_categories=fatal_categories,
        fatal_examples=fatal_examples,
        warning_categories=warning_categories,
        warning_examples=warning_examples,
        observation_summary=(observation_counts, observation_examples),
    )

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
            f" with {fatal_errors} fatal errors",
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
        True if the family name contains a style token not supported by
        the entry's own weight, width, or slant metadata.

    Notes
    -----
    This helper is intentionally heuristic. It suppresses common false
    positives where family names legitimately embed weight/width/slant
    qualifiers that agree with the font metadata.
    """
    fam = desc.get("family", "")
    if not isinstance(fam, str):
        return False

    subfamily = desc.get("subfamily", "")
    subfamily_lc = subfamily.lower() if isinstance(subfamily, str) else ""
    weight_class = desc.get("weight_class")
    width_class = desc.get("width_class")
    italic_angle = desc.get("italic_angle")

    for match in STYLE_LEAK_RE.finditer(fam):
        token = match.group(1).lower()

        if token in STYLE_WEIGHT_RANGES:
            lo, hi = STYLE_WEIGHT_RANGES[token]
            if isinstance(weight_class, int) and lo <= weight_class <= hi:
                continue
            if token == "regular" and subfamily_lc == "regular":
                continue
            if token == "bold" and "semi bold" in subfamily_lc:
                continue
            return True

        if token in STYLE_WIDTH_TOKENS:
            if token in {"condensed", "narrow"}:
                if isinstance(width_class, int) and width_class < 5:
                    continue
            elif (
                token == "extended" and isinstance(width_class, int) and width_class > 5
            ):
                continue
            return True

        if token in STYLE_SLANT_TOKENS:
            if isinstance(italic_angle, (int, float)) and italic_angle != 0:
                continue
            if token in subfamily_lc:
                continue
            return True

    return False
