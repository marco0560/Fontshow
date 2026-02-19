"""
JSON read-boundary normalization.

Invariant:
    In-memory: enums are enums
    On disk: enums are strings

This module performs the **single allowed conversion**
after JSON load and before the data enters the core pipeline.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from fontshow.types import Severity


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
