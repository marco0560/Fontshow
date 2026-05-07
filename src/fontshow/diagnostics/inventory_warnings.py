"""
Inventory parsing diagnostic helpers.

This module provides utilities used during the inventory parsing stage
to build and emit diagnostic messages.

Responsibilities
----------------
- Format human-readable identifiers for inventory entries.
- Emit warnings related to language inference and metadata extraction.
- Provide diagnostic helpers used by the inventory parsing pipeline.

Design principles
-----------------
Diagnostics helpers operate on parsed inventory structures and must
not perform orchestration or CLI command handling. Their purpose is
to keep diagnostic logic separate from the core parsing workflow.

Architectural role
------------------
This module belongs to the **diagnostics subsystem** and supports the
inventory parsing stage implemented in `fontshow.cli.parse_inventory`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, cast

from fontshow.core.cli_utils import (
    log_info,
    log_warn,
)
from fontshow.core.types import FontRef, Severity

if TYPE_CHECKING:
    from collections.abc import Mapping

    from fontshow.core.types import WarningInfo


def _format_font_identity(font: FontRef, index: int) -> str:
    """
    Build a human-readable identifier for a font entry.

    Parameters
    ----------
    font : FontRef
        Font entry object.
    index : int
        Index of the font entry in the inventory.

    Returns
    -------
    str
        Human-readable identifier in the form:
        "font[<index>] <filename>[:<face_index>]".

    Notes
    -----
    - Uses only stable cross-schema identity fields such as path,
      family, and subfamily.
    - Intended for diagnostics and CLI output only.
    - Does not modify the font entry.
    """
    label = f"font[{index}]"

    path = _get_font_path_for_diagnostics(font)
    family = font.get("family")
    subfamily = font.get("subfamily")

    if path:
        name = Path(path).name
        if family is not None:
            name += f" ({family} {subfamily})"

        return f"{label} {name}"

    return label


def _get_font_path_for_diagnostics(font: FontRef) -> str | None:
    """
    Return the best-available font file path for diagnostics.

    Parameters
    ----------
    font : FontRef
        Font entry object from the inventory.

    Returns
    -------
    str | None
        Resolved path string from ``font["path"]`` when present.
        Returns None if no usable path is found.

    Notes
    -----
    - This function is read-only and MUST NOT mutate the input.
    - Used exclusively for human-readable diagnostics.
    - Legacy inventory layouts are not supported.
    """
    if isinstance(font, dict) and font.get("path"):
        return font.get("path")

    return None


# ============================================================
# Helper: extract language warning aggregates
# ============================================================


def _collect_language_warnings(
    font: FontRef,
) -> tuple[list[str], list[str], list[str], list[tuple[str, str, str]]]:
    """
    Aggregate warnings for grouped CLI display.

    Parameters
    ----------
    font : FontRef
        Font descriptor whose structured warnings are inspected.

    Returns
    -------
    tuple[list[str], list[str], list[str], list[tuple[str, str, str]]]
        Four-element tuple containing:
        - normalized language transformations
        - duplicate language tags
        - dropped language tags
        - other warning triples as ``(severity, code, message)``

    Notes
    -----
    The helper groups warning records for compact CLI presentation and
    only forwards non-language warnings when their severity is warning
    or error.
    """
    lang_norm_pairs: list[str] = []
    lang_dups: list[str] = []
    lang_dropped: list[str] = []
    other_warnings: list[tuple[str, str, str]] = []

    raw_warnings = font.get("warnings")
    warnings_list: list[WarningInfo] = (
        raw_warnings if isinstance(raw_warnings, list) else []
    )

    for warning in warnings_list:
        severity = warning.get("severity", Severity.WARN)

        code = str(warning.get("code", "unknown_warning"))
        message = str(warning.get("message", ""))

        extra_raw = warning.get("extra")
        extra: Mapping[str, object] = extra_raw if isinstance(extra_raw, dict) else {}

        def _extract_lang(msg: str) -> str:
            """
            Extract a quoted language token from a warning message.

            Parameters
            ----------
            msg : str
                Warning message text to inspect.

            Returns
            -------
            str
                Extracted token if a quoted substring is present,
                otherwise an empty string.
            """
            if not msg:
                return ""
            m = re.search(r"'([^']+)'", msg)
            return m.group(1) if m else ""

        if code == "language_normalized":
            raw_value = extra.get("raw")
            raw = raw_value if isinstance(raw_value, str) else _extract_lang(message)
            norm = extra.get("normalized")
            if isinstance(norm, str):
                if raw:
                    lang_norm_pairs.append(f"{raw} -> {norm}")
                else:
                    lang_norm_pairs.append(norm)
            elif raw:
                lang_norm_pairs.append(raw)
            continue

        if code == "language_duplicate":
            raw_value = extra.get("raw")
            raw = raw_value if isinstance(raw_value, str) else _extract_lang(message)
            if raw:
                lang_dups.append(raw)
            continue

        if code == "language_dropped":
            raw_value = extra.get("raw")
            raw = raw_value if isinstance(raw_value, str) else _extract_lang(message)
            if raw:
                lang_dropped.append(raw)
            continue

        if code in {"normalized_languages", "duplicate_languages", "dropped_languages"}:
            continue

        if severity in (Severity.WARN, Severity.ERROR):
            other_warnings.append((severity.name.lower(), code, message))

    return lang_norm_pairs, lang_dups, lang_dropped, other_warnings


# ============================================================
# Helper: verbose warning emitter
# ============================================================


def _emit_verbose_warnings(
    enriched: Mapping[str, object], *, enabled: bool = False
) -> None:
    """
    Emit grouped warnings for verbose CLI mode.

    Parameters
    ----------
    enriched : JSONDict
        Enriched inventory structure containing a ``fonts`` list.
    enabled : bool, optional
        Whether verbose warning emission is enabled for the current CLI
        invocation.

    Returns
    -------
    None

    Notes
    -----
    The function formats warning groups per font entry and routes them
    through CLI logging helpers without mutating the inventory.

    Duplicate warning payloads within a group are collapsed through
    ``set()`` before emission to keep CLI output compact.
    """
    if not enabled:
        return

    fonts = enriched.get("fonts", [])
    if not isinstance(fonts, list):
        return

    for idx, font in enumerate(fonts):
        if not isinstance(font, dict):
            continue

        font_ref = cast("FontRef", font)

        ident = _format_font_identity(font_ref, idx)

        norm, dups, dropped, other = _collect_language_warnings(font_ref)

        if norm:
            log_info(f"{ident} normalized_languages: {', '.join(sorted(set(norm)))}")

        if dups:
            log_info(f"{ident} duplicate_languages: {', '.join(sorted(set(dups)))}")

        if dropped:
            log_warn(f"{ident} dropped_languages: {', '.join(sorted(set(dropped)))}")

        for _severity, code, message in other:
            log_warn(f"{ident} {code}: {message}")
