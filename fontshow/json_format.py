"""
JSON formatting helpers.

This module provides a small, dependency-free JSON pretty-printer
used for stable, human-friendly output artifacts.

Design goal:
- Keep object/array indentation (like json.dumps(indent=2))
- Compact short numeric arrays (e.g. Unicode ranges) onto a single line

This is intentionally formatting-only: it MUST NOT change data.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from fontshow.logging_utils import log, log_trace_cat
from fontshow.types import Severity


def _is_short_numeric_list(value: Any, *, max_len: int) -> bool:
    """
    Determine whether a value is a short numeric list eligible for compact formatting.

    Parameters
    ----------
    value : Any
        Candidate value to inspect.
    max_len : int
        Maximum allowed list length for compact one-line formatting.

    Returns
    -------
    bool
        True if the value is:
        - a list,
        - non-empty,
        - length ≤ max_len,
        - composed exclusively of int or float (excluding bool),
        otherwise False.

    Notes
    -----
    - Boolean values are explicitly excluded even though bool is a subclass of int.
    - Used internally by `dumps_pretty()` to decide whether to collapse
      numeric arrays onto a single line.
    - Pure formatting heuristic; does not alter data.
    """
    if not isinstance(value, list):
        return False
    if len(value) == 0 or len(value) > max_len:
        return False
    for x in value:
        if isinstance(x, bool) or not isinstance(x, int | float):
            return False
    return True


def dumps_pretty(
    value: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    compact_numeric_lists_max_len: int = 8,
) -> str:
    """
    Serialize a Python object to JSON with stable indentation and compact numeric lists.

    Parameters
    ----------
    value : Any
        Python object to serialize.
    indent : int, default=2
        Number of spaces per indentation level.
    ensure_ascii : bool, default=False
        If True, escape all non-ASCII characters.
    sort_keys : bool, default=False
        If True, mapping keys are sorted lexicographically.
    compact_numeric_lists_max_len : int, default=8
        Maximum length for numeric lists to be rendered on a single line.

    Returns
    -------
    str
        JSON-formatted string with deterministic layout and trailing newline.

    Notes
    -----
    Contract:
    - Formatting-only function: MUST NOT change data semantics.
    - Output is deterministic given identical input and parameters.
    - Always appends a trailing newline.

    Behavior:
    - Preserves standard JSON indentation style for objects and arrays.
    - Compacts short numeric lists (e.g., Unicode ranges) onto one line.
    - Converts `Severity` enums using `Severity.to_json()`.
    - Converts generic Enum values to lowercase string names.
    - Supports arbitrary nested structures via recursive rendering.
    - Logs TRACE diagnostics for formatting lifecycle and compacting decisions.

    Design rationale:
    - Keeps human-readable structure for large objects.
    - Avoids vertical bloat for small numeric arrays.
    - Provides stable output for diff-friendly artifacts.
    """
    log_trace_cat(
        log,
        "raw",
        "json formatting started",
        extra={
            "indent": indent,
            "ensure_ascii": ensure_ascii,
            "sort_keys": sort_keys,
            "compact_numeric_lists_max_len": compact_numeric_lists_max_len,
        },
    )

    def write(v: Any, level: int) -> str:
        # --- Severity normalization (canonical) ---
        if isinstance(v, Severity):
            return json.dumps(v.to_json(), ensure_ascii=ensure_ascii)

        # --- Generic Enum normalization (safe fallback) ---
        if isinstance(v, Enum):
            return json.dumps(v.name.lower(), ensure_ascii=ensure_ascii)

        # --- Primitive types ---
        if v is None or isinstance(v, str | int | float | bool):
            return json.dumps(v, ensure_ascii=ensure_ascii)

        # --- Mapping (dict-like) ---
        if isinstance(v, Mapping):
            items = list(v.items())
            if sort_keys:
                items.sort(key=lambda kv: str(kv[0]))
            if not items:
                return "{}"

            pad = " " * (indent * level)
            pad_in = " " * (indent * (level + 1))
            out = ["{\n"]

            for i, (k, val) in enumerate(items):
                key_s = json.dumps(str(k), ensure_ascii=ensure_ascii)
                out.append(f"{pad_in}{key_s}: {write(val, level + 1)}")
                out.append(",\n" if i < len(items) - 1 else "\n")

            out.append(f"{pad}}}")
            return "".join(out)

        # --- Sequence (list-like, excluding bytes) ---
        if isinstance(v, Sequence) and not isinstance(v, bytes | bytearray):
            if _is_short_numeric_list(v, max_len=compact_numeric_lists_max_len):
                log_trace_cat(
                    log,
                    "raw",
                    "json compact numeric list applied",
                    extra={
                        "length": len(v),
                        "max_len": compact_numeric_lists_max_len,
                    },
                )
                return json.dumps(
                    list(v),
                    ensure_ascii=ensure_ascii,
                    separators=(", ", ": "),
                )

            seq = list(v)
            if not seq:
                return "[]"

            pad = " " * (indent * level)
            pad_in = " " * (indent * (level + 1))
            out = ["[\n"]

            for i, item in enumerate(seq):
                out.append(f"{pad_in}{write(item, level + 1)}")
                out.append(",\n" if i < len(seq) - 1 else "\n")

            out.append(f"{pad}]")
            return "".join(out)

        # --- Fallback ---
        return json.dumps(v, ensure_ascii=ensure_ascii)

    out = write(value, 0) + "\n"
    log_trace_cat(
        log,
        "raw",
        "json formatting completed",
        extra={
            "bytes": len(out.encode("utf-8")),
        },
    )
    return out
