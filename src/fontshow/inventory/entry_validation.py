"""
Inventory entry validation helpers.

This module implements validation routines used to verify the semantic
consistency of individual font entries within a parsed inventory.

Responsibilities
----------------
- Validate required fields of normalized inventory entries.
- Enforce type and value constraints for entry attributes.
- Collect validation errors associated with individual font entries.

Design principles
-----------------
Validation helpers operate on normalized inventory structures and must
not perform orchestration or CLI interactions. They provide deterministic
checks that can be reused by multiple pipeline stages.

Architectural role
------------------
This module belongs to the **inventory subsystem** and supports semantic
validation of parsed inventory entries before they are consumed by
catalog generation or other downstream stages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fontshow.inventory.schema_accessors import get_font_metrics, get_font_typography

if TYPE_CHECKING:
    from fontshow.core.types import JSONDict

# ============================================================
# Helper functions
# ============================================================


def _validate_str_required(obj: JSONDict, key: str, errors: list[str]) -> None:
    """
    Validate that a required field is a non-empty string.

    Parameters
    ----------
    obj : JSONDict
        Entry dictionary being validated.
    key : str
        Required field name.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None
    """
    v = obj.get(key)
    if not isinstance(v, str) or not v:
        errors.append(f"Missing or invalid '{key}'")


def _validate_int_min(
    obj: JSONDict, key: str, min_value: int, errors: list[str]
) -> None:
    """
    Validate that a required integer field is at least a minimum value.

    Parameters
    ----------
    obj : JSONDict
        Entry dictionary being validated.
    key : str
        Required field name.
    min_value : int
        Minimum accepted integer value.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None
    """
    v = obj.get(key)
    if not isinstance(v, int) or v < min_value:
        errors.append(f"Missing or invalid '{key}'")


def _validate_int_range(
    obj: JSONDict, key: str, lo: int, hi: int, errors: list[str]
) -> None:
    """
    Validate that a required integer field falls within an inclusive range.

    Parameters
    ----------
    obj : JSONDict
        Entry dictionary being validated.
    key : str
        Required field name.
    lo : int
        Inclusive lower bound.
    hi : int
        Inclusive upper bound.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None
    """
    v = obj.get(key)
    if not isinstance(v, int) or not (lo <= v <= hi):
        errors.append(f"Missing or invalid '{key}'")


def _validate_obj_required(obj: JSONDict, key: str, errors: list[str]) -> None:
    """
    Validate that a required field is a dictionary object.

    Parameters
    ----------
    obj : JSONDict
        Entry dictionary being validated.
    key : str
        Required field name.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None
    """
    v = obj.get(key)
    if not isinstance(v, dict):
        errors.append(f"Missing or invalid '{key}'")


def _validate_bool_required(obj: JSONDict, key: str, errors: list[str]) -> None:
    """
    Validate that a required field is a boolean.

    Parameters
    ----------
    obj : JSONDict
        Entry dictionary being validated.
    key : str
        Required field name.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None
    """
    v = obj.get(key)
    if not isinstance(v, bool):
        errors.append(f"Missing or invalid '{key}'")


def _validate_number_required(obj: JSONDict, key: str, errors: list[str]) -> None:
    """
    Validate that a required field is numeric.

    Parameters
    ----------
    obj : JSONDict
        Entry dictionary being validated.
    key : str
        Required field name.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None
    """
    v = obj.get(key)
    if not isinstance(v, (int, float)):
        errors.append(f"Missing or invalid '{key}'")


def _validate_sample_text(entry: JSONDict, errors: list[str]) -> None:
    """
    Validate the normalized embedded sample-text block.

    Parameters
    ----------
    entry : JSONDict
        Inventory entry being validated.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None

    Notes
    -----
    The helper enforces the active schema expectation that
    ``sample_text.source`` is ``"font"`` and that the embedded text is a
    string. The text may be empty in raw or enriched inventories when
    no internal sample is available.
    """
    typography = get_font_typography(entry)
    sample_text = typography.get("sample_text")
    if not isinstance(sample_text, dict):
        errors.append("Missing or invalid 'sample_text'")
        return

    if sample_text.get("source") != "font":
        errors.append("Invalid 'sample_text.source'")

    text = sample_text.get("text")
    if not isinstance(text, str):
        errors.append("Missing or invalid 'sample_text.text'")


def _validate_specimen(entry: JSONDict, errors: list[str]) -> None:
    """
    Validate specimen-related fields of an inventory entry.

    Parameters
    ----------
    entry : JSONDict
        Inventory entry being validated.
    errors : list[str]
        Mutable error accumulator updated in place.

    Returns
    -------
    None

    Notes
    -----
    This helper validates specimen text presence, generation strategy,
    and glyph count metadata expected by downstream rendering code.
    """
    typography = get_font_typography(entry)
    specimen_text = typography.get("specimen_text")
    if not isinstance(specimen_text, str) or not specimen_text:
        errors.append("Missing or invalid 'specimen_text'")

    specimen_strategy = typography.get("specimen_strategy")
    if specimen_strategy not in (
        "internal",
        "script",
        "language",
        "pua",
        "cmap",
        "deferred",
        "validated-language-sample",
        "validated-fallback",
    ):
        errors.append("Invalid 'specimen_strategy'")

    specimen_glyph_count = typography.get("specimen_glyph_count")
    if specimen_glyph_count is not None and (
        not isinstance(specimen_glyph_count, int) or specimen_glyph_count < 1
    ):
        errors.append("Missing or invalid 'specimen_glyph_count'")


def validate_font_entry(entry: Any, *, index: int) -> list[str]:
    """
    Validate the structural integrity of a single font entry.

    Parameters
    ----------
    entry : Any
        Font entry object expected to be a dictionary.
    index : int
        Position of the entry within the inventory (diagnostic only).

    Returns
    -------
    list[str]
        List of validation error messages.
        Empty list indicates a structurally valid entry.

    Notes
    -----
    - Validation is schema-level only (no inference required).
    - Function is read-only and does not mutate the entry.
    - Identity fields may be omitted when base_names is present.
    - Optional sample_text field is validated if present.
    """
    _ = index  # for potential future use in error messages
    errors: list[str] = []

    if not isinstance(entry, dict):
        return ["entry is not an object"]

    # Schema 1.2 — required top-level fields
    _validate_str_required(entry, "family", errors)
    _validate_str_required(entry, "subfamily", errors)
    _validate_str_required(entry, "path", errors)
    _validate_str_required(entry, "postscript_name", errors)

    _validate_sample_text(entry, errors)

    _validate_specimen(entry, errors)

    metrics = dict(get_font_metrics(entry))
    _validate_int_min(metrics, "glyph_count", 1, errors)
    _validate_int_range(metrics, "weight_class", 1, 1000, errors)
    _validate_int_range(metrics, "width_class", 1, 9, errors)

    _validate_obj_required(entry, "coverage", errors)
    _validate_obj_required(entry, "inference", errors)
    _validate_obj_required(entry, "charset", errors)

    _validate_str_required(entry, "full_name", errors)
    _validate_str_required(entry, "version_string", errors)
    _validate_str_required(entry, "unique_font_id", errors)

    _validate_int_min(metrics, "units_per_em", 1, errors)

    _validate_int_min(metrics, "ascent", -(10**18), errors)
    _validate_int_min(metrics, "descent", -(10**18), errors)

    _validate_number_required(metrics, "italic_angle", errors)
    _validate_bool_required(metrics, "is_fixed_pitch", errors)

    return errors
