"""
Inventory entry validation helpers.

Extracted from parse_font_inventory.py during module refactoring.

These helpers validate semantic consistency of parsed font entries
before they are used by downstream catalog generation.
"""

from __future__ import annotations

from typing import Any

# ============================================================
# Helper functions
# ============================================================


def _validate_str_required(obj: dict, key: str, errors: list[str]) -> None:
    v = obj.get(key)
    if not isinstance(v, str) or not v:
        errors.append(f"Missing or invalid '{key}'")


def _validate_int_min(obj: dict, key: str, min_value: int, errors: list[str]) -> None:
    v = obj.get(key)
    if not isinstance(v, int) or v < min_value:
        errors.append(f"Missing or invalid '{key}'")


def _validate_int_range(
    obj: dict, key: str, lo: int, hi: int, errors: list[str]
) -> None:
    v = obj.get(key)
    if not isinstance(v, int) or not (lo <= v <= hi):
        errors.append(f"Missing or invalid '{key}'")


def _validate_obj_required(obj: dict, key: str, errors: list[str]) -> None:
    v = obj.get(key)
    if not isinstance(v, dict):
        errors.append(f"Missing or invalid '{key}'")


def _validate_bool_required(obj: dict, key: str, errors: list[str]) -> None:
    v = obj.get(key)
    if not isinstance(v, bool):
        errors.append(f"Missing or invalid '{key}'")


def _validate_number_required(obj: dict, key: str, errors: list[str]) -> None:
    v = obj.get(key)
    if not isinstance(v, (int, float)):
        errors.append(f"Missing or invalid '{key}'")


def _validate_sample_text(entry: dict, errors: list[str]) -> None:
    sample_text = entry.get("sample_text")
    if not isinstance(sample_text, dict):
        errors.append("Missing or invalid 'sample_text'")
        return

    if sample_text.get("source") != "font":
        errors.append("Invalid 'sample_text.source'")

    text = sample_text.get("text")
    if not isinstance(text, str) or not text:
        errors.append("Missing or invalid 'sample_text.text'")


def _validate_specimen(entry: dict, errors: list[str]) -> None:
    specimen_text = entry.get("specimen_text")
    if not isinstance(specimen_text, str) or not specimen_text:
        errors.append("Missing or invalid 'specimen_text'")

    specimen_strategy = entry.get("specimen_strategy")
    if specimen_strategy not in ("internal", "script", "cmap"):
        errors.append("Invalid 'specimen_strategy'")

    specimen_glyph_count = entry.get("specimen_glyph_count")
    if not isinstance(specimen_glyph_count, int) or specimen_glyph_count < 1:
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

    _validate_int_min(entry, "glyph_count", 1, errors)
    _validate_int_range(entry, "weight_class", 1, 1000, errors)
    _validate_int_range(entry, "width_class", 1, 9, errors)

    _validate_obj_required(entry, "coverage", errors)
    _validate_obj_required(entry, "inference", errors)
    _validate_obj_required(entry, "charset", errors)

    _validate_str_required(entry, "full_name", errors)
    _validate_str_required(entry, "version_string", errors)
    _validate_str_required(entry, "unique_font_id", errors)

    _validate_int_min(entry, "units_per_em", 1, errors)

    _validate_int_min(entry, "ascent", -(10**18), errors)
    _validate_int_min(entry, "descent", -(10**18), errors)

    _validate_number_required(entry, "italic_angle", errors)
    _validate_bool_required(entry, "is_fixed_pitch", errors)

    return errors
