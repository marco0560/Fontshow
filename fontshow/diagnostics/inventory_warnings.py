"""
Inventory parsing diagnostics helpers.

This module contains utilities used by the inventory parsing pipeline to
format diagnostic messages, collect language inference warnings, and emit
debug information during parsing.

The functions here are pure helpers and do not perform orchestration or
CLI handling. They are called from the parse_inventory pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from fontshow.cli_utils import (
    log_info,
    log_warn,
)
from fontshow.types import FontRef, Severity

if TYPE_CHECKING:
    from fontshow.warnings import WarningInfo


def _format_font_identity(font: dict, index: int) -> str:
    """
    Build a human-readable identifier for a font entry.

    Parameters
    ----------
    font : dict
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
    - Compatible with schema 1.0 and 1.1 layouts.
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
            if subfamily is not None:
                name += f" ({family} {subfamily})"
            else:
                name += f" ({family})"
        return f"{label} {name}"

    return label


def _get_font_path_for_diagnostics(font: dict) -> str | None:
    """
    Return the best-available font file path for diagnostics.

    Parameters
    ----------
    font : dict
        Font entry dictionary from the inventory.

    Returns
    -------
    str | None
        Resolved path string according to preference order:
        1. font["path"] (schema >= 1.1)
        2. font["identity"]["file"] (schema 1.0)
        Returns None if no usable path is found.

    Notes
    -----
    - This function is read-only and MUST NOT mutate the input.
    - Used exclusively for human-readable diagnostics.
    """
    if isinstance(font, dict):
        if font.get("path"):
            return font.get("path")

        identity = font.get("identity")
        if isinstance(identity, dict):
            return identity.get("file")

    return None


# ============================================================
# Helper: extract language warning aggregates
# ============================================================


def _collect_language_warnings(
    font: FontRef,
) -> tuple[list[str], list[str], list[str], list[tuple[str, str, str]]]:
    """
    Aggregate warnings for grouped CLI display.

    Returns:
        normalized, duplicates, dropped, other_warnings
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
        extra: dict[str, Any] = extra_raw if isinstance(extra_raw, dict) else {}

        def _extract_lang(msg: str) -> str:
            if not msg:
                return ""
            m = re.search(r"'([^']+)'", msg)
            return m.group(1) if m else ""

        if code == "language_normalized":
            raw = extra.get("raw") or _extract_lang(message)
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
            raw = extra.get("raw") or _extract_lang(message)
            if raw:
                lang_dups.append(raw)
            continue

        if code == "language_dropped":
            raw = extra.get("raw") or _extract_lang(message)
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


def _emit_verbose_warnings(enriched: dict[str, Any]) -> None:
    """Emit grouped warnings for verbose CLI mode."""

    fonts = enriched.get("fonts", [])
    if not isinstance(fonts, list):
        return

    for idx, font in enumerate(fonts):
        if not isinstance(font, dict):
            continue

        ident = _format_font_identity(font, idx)

        norm, dups, dropped, other = _collect_language_warnings(cast("FontRef", font))

        if norm:
            log_info(f"{ident} normalized_languages: {', '.join(sorted(set(norm)))}")

        if dups:
            log_info(f"{ident} duplicate_languages: {', '.join(sorted(set(dups)))}")

        if dropped:
            log_warn(f"{ident} dropped_languages: {', '.join(sorted(set(dropped)))}")

        for _severity, code, message in other:
            log_warn(f"{ident} {code}: {message}")
