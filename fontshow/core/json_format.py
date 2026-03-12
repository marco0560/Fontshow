"""
JSON formatting utilities.

This module implements a deterministic JSON pretty-printer used by
Fontshow when producing human-readable artifacts.

Responsibilities
----------------
- Provide stable and deterministic JSON formatting.
- Preserve indentation and readability for structured objects.
- Compact short numeric arrays (such as Unicode ranges) onto a
  single line.

Design principles
-----------------
Formatting logic must never alter data semantics. The module performs
presentation-only transformations while preserving the exact data
content.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and provides
stable JSON formatting used by inventory generation, parsing, and
catalog output.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import Severity


class _PrettyJSONWriter:
    """
    Internal stateful JSON writer used by `dumps_pretty()`.

    Parameters
    ----------
    None

    Notes
    -----
    The writer caches indentation strings and serialized keys to keep
    recursive pretty-printing deterministic and efficient. It is an
    internal helper and not part of the public formatting API.
    """

    def __init__(
        self,
        *,
        indent: int,
        ensure_ascii: bool,
        sort_keys: bool,
        compact_numeric_lists_max_len: int,
    ) -> None:
        """
        Initialize writer configuration and internal caches.

        Parameters
        ----------
        indent : int
            Number of spaces per indentation level.
        ensure_ascii : bool
            Whether non-ASCII characters must be escaped.
        sort_keys : bool
            Whether mapping keys should be emitted in sorted order.
        compact_numeric_lists_max_len : int
            Maximum list length eligible for one-line numeric formatting.

        Returns
        -------
        None
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.sort_keys = sort_keys
        self.compact_numeric_lists_max_len = compact_numeric_lists_max_len

        self._indent_cache: dict[int, str] = {0: ""}
        self._key_cache: dict[str, str] = {}

    # ---------- helpers ----------

    def _pad(self, level: int) -> str:
        """
        Return cached indentation padding for a nesting level.

        Parameters
        ----------
        level : int
            Nesting depth to convert into leading spaces.

        Returns
        -------
        str
            Indentation string for the requested level.
        """
        s = self._indent_cache.get(level)
        if s is None:
            s = " " * (self.indent * level)
            self._indent_cache[level] = s
        return s

    def _primitive(self, v: Any) -> str:
        """
        Serialize a primitive JSON-compatible value.

        Parameters
        ----------
        v : Any
            Primitive value to serialize.

        Returns
        -------
        str
            JSON text for null, booleans, strings, or numbers.
        """
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        return json.dumps(v, ensure_ascii=self.ensure_ascii)

    # ---------- writers ----------

    def write(self, v: Any, level: int) -> str:
        """
        Serialize an arbitrary value using the writer's formatting rules.

        Parameters
        ----------
        v : Any
            Value to serialize.
        level : int
            Current nesting depth.

        Returns
        -------
        str
            Deterministically formatted JSON fragment.
        """
        if isinstance(v, Severity):
            return json.dumps(v.to_json(), ensure_ascii=self.ensure_ascii)

        if isinstance(v, Enum):
            return json.dumps(v.name.lower(), ensure_ascii=self.ensure_ascii)

        if v is None or isinstance(v, (str, int, float, bool)):
            return self._primitive(v)

        if isinstance(v, Mapping):
            return self._write_mapping(v, level)

        if isinstance(v, Sequence) and not isinstance(v, (bytes, bytearray)):
            return self._write_sequence(v, level)

        return json.dumps(v, ensure_ascii=self.ensure_ascii)

    def _write_mapping(self, v: Mapping[Any, Any], level: int) -> str:
        """
        Serialize a mapping with stable indentation and optional key sorting.

        Parameters
        ----------
        v : Mapping[Any, Any]
            Mapping to serialize.
        level : int
            Current nesting depth.

        Returns
        -------
        str
            Formatted JSON object literal.
        """
        items = list(v.items())
        if self.sort_keys:
            items.sort(key=lambda kv: str(kv[0]))
        if not items:
            return "{}"

        pad = self._pad(level)
        pad_in = self._pad(level + 1)
        out = ["{\n"]

        for i, (k, val) in enumerate(items):
            k_str = str(k)
            key_s = self._key_cache.get(k_str)
            if key_s is None:
                key_s = json.dumps(k_str, ensure_ascii=self.ensure_ascii)
                self._key_cache[k_str] = key_s

            out.append(f"{pad_in}{key_s}: {self.write(val, level + 1)}")
            out.append(",\n" if i < len(items) - 1 else "\n")

        out.append(f"{pad}}}")
        return "".join(out)

    def _write_sequence(self, v: Sequence[Any], level: int) -> str:
        """
        Serialize a sequence with compact handling for short numeric lists.

        Parameters
        ----------
        v : Sequence[Any]
            Sequence to serialize.
        level : int
            Current nesting depth.

        Returns
        -------
        str
            Formatted JSON array literal.
        """
        if _is_short_numeric_list(v, max_len=self.compact_numeric_lists_max_len):
            return json.dumps(
                list(v),
                ensure_ascii=self.ensure_ascii,
                separators=(", ", ": "),
            )

        seq = list(v)
        if not seq:
            return "[]"

        pad = self._pad(level)
        pad_in = self._pad(level + 1)
        out = ["[\n"]

        for i, item in enumerate(seq):
            out.append(f"{pad_in}{self.write(item, level + 1)}")
            out.append(",\n" if i < len(seq) - 1 else "\n")

        out.append(f"{pad}]")
        return "".join(out)


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

    writer = _PrettyJSONWriter(
        indent=indent,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        compact_numeric_lists_max_len=compact_numeric_lists_max_len,
    )

    out = writer.write(value, 0) + "\n"

    log_trace_cat(
        log,
        "raw",
        "json formatting completed",
        extra={
            "bytes": len(out.encode("utf-8")),
        },
    )
    return out
