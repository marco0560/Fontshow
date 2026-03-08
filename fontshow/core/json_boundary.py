"""
JSON boundary normalization utilities.

This module handles normalization steps performed immediately after
loading Fontshow JSON inventories.

Responsibilities
----------------
- Convert serialized enum values into internal Enum objects.
- Enforce the invariant between on-disk JSON representations and
  in-memory data structures.

Design principles
-----------------
The JSON boundary is the only location where conversion between
serialized and in-memory representations is permitted. All subsequent
pipeline stages operate on normalized in-memory structures.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and implements
the normalization step applied at the JSON input boundary of the
Fontshow pipeline.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from fontshow.core.types import Severity


def normalize_loaded_enums(data: dict[str, Any]) -> None:
    """
    Normalize enum-encoded JSON fields after loading.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed JSON object loaded from disk. The structure is modified in place.

    Returns
    -------
    None
        The function performs in-place normalization and returns nothing.

    Notes
    -----
    Contract:
    - Must be called immediately after json.load/json.loads.
    - Converts known enum string fields to internal Enum objects.
    - Idempotent and safe on already-normalized data.
    - Unknown or invalid enum values are ignored without raising.

    Behavior:
    - Maintains invariant:
        In-memory → enums are Enum objects
        On-disk   → enums are strings
    - Currently normalizes:
        warnings[].severity → Severity enum
    """
    # --- warnings.severity ---
    warnings = data.get("warnings")
    if isinstance(warnings, list):
        for w in warnings:
            if not isinstance(w, dict):
                continue
            sev = w.get("severity")
            if isinstance(sev, str):
                with suppress(ValueError):
                    w["severity"] = Severity.from_str(sev)
