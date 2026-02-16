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

    Contract:
    - Must be called immediately after json.load/json.loads
    - Converts known enum string fields to internal Enum objects
    - Idempotent and safe on already-normalized data
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
