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
from typing import Any

from fontshow.logging_utils import log, log_trace_cat


def _is_short_numeric_list(value: Any, *, max_len: int) -> bool:
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
    """Serialize *value* to JSON with stable indentation and compact numeric lists."""

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
        if v is None or isinstance(v, str | int | float | bool):
            return json.dumps(v, ensure_ascii=ensure_ascii)

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
