"""
Inventory I/O and normalization helpers.

This module provides utilities used to load, validate, and normalize
font inventory data structures before they are consumed by higher-level
catalog generation logic.

Responsibilities
----------------
- Load inventory JSON data from disk.
- Normalize filesystem paths contained in the inventory.
- Validate the structural integrity of inventory containers.
- Convert inventory structures into descriptor lists suitable for
  catalog generation.

Design principles
-----------------
The helpers in this module operate purely on inventory data and perform
no catalog rendering or LaTeX generation. They isolate inventory loading
and normalization logic so that catalog modules can assume a clean and
consistent in-memory representation.

Architectural role
------------------
This module belongs to the **inventory domain layer**. It forms the
boundary between raw inventory files produced by discovery/parsing
pipelines and the catalog subsystem that renders those fonts into the
final LaTeX catalog.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, cast

from fontshow.catalog.metadata import font_family
from fontshow.core.cli_utils import log_err, log_ok
from fontshow.core.global_constants import SCHEMA_VERSION
from fontshow.core.json_boundary import normalize_loaded_enums
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import Severity
from fontshow.inventory.semantic_validation import enforce_semantic_validation
from fontshow.platform.runtime import _enforce_platform

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from fontshow.core.types import CatalogFontEntryV12


# ============================================================
# Helper: validate fonts container
# ============================================================


def _validate_fonts_container(data: dict[str, Any]) -> list[Any] | None:
    """
    Validate and return the 'fonts' container from an inventory JSON.

    Returns
    -------
    list[Any] | None
        The fonts list if present and valid, otherwise None.
    """
    fonts = data.get("fonts")

    if not isinstance(fonts, list):
        return None

    return fonts


def as_font_desc_list(fonts: Sequence[object]) -> list[CatalogFontEntryV12]:
    """
    Normalize a sequence of font descriptor objects.

    Parameters
    ----------
    fonts : collections.abc.Sequence[object]
        Sequence expected to contain font descriptor dictionaries.

    Returns
    -------
    list[CatalogFontEntryV12]
        List of validated font descriptor dictionaries.

    Raises
    ------
    TypeError
        If any element in `fonts` is not a dictionary.

    Notes
    -----
    Legacy coercion of non-dictionary entries is not supported.
    """
    out: list[CatalogFontEntryV12] = []
    for f in fonts:
        if not isinstance(f, dict):
            msg = f"Unexpected font entry type {type(f)} for font '{f}'"
            raise TypeError(msg)
        out.append(cast("CatalogFontEntryV12", f))
    return out


def group_fonts_by_family(
    fonts: list[CatalogFontEntryV12],
) -> list[CatalogFontEntryV12]:
    """
    Reduce a list of font entries to one entry per family.

    Parameters
    ----------
    fonts : list[dict]
        List of font descriptor dictionaries.

    Returns
    -------
    list[dict]
        List containing a single representative font for each family.
        The first encountered font per family is preserved, and the
        order of first occurrence is maintained.
    """
    families: OrderedDict[str, Any] = OrderedDict()
    for font in fonts:
        fam = font_family(font)
        families.setdefault(fam, []).append(font)
    result = [entries[0] for entries in families.values()]

    log_trace_cat(
        log,
        "flow",
        "fonts grouped by family",
        extra={
            "families": len(result),
            "input_fonts": len(fonts),
        },
    )

    return result


# ============================================================
# Inventory loading (pipeline mode)
# ============================================================


def load_font_inventory(path: Path) -> list[dict]:
    """
    Load and validate a Fontshow inventory file.

    Parameters
    ----------
    path : pathlib.Path
        Path to the inventory JSON file.

    Returns
    -------
    list[dict]
        List of normalized font descriptor dictionaries.

    Raises
    ------
    RuntimeError
        If validation fails or the inventory is incompatible.

    Notes
    -----
    Delegates strict validation to `_load_inventory()` while preserving
    the exception-based contract expected by library callers.
    """
    rc, fonts = _load_inventory(path, require_platform=False)

    if rc != 0:
        msg = "Invalid or incompatible inventory"
        raise RuntimeError(msg)

    return fonts


def _normalize_inventory_paths(inventory: dict) -> None:
    """
    Normalize inventory font entries so that `identity.file` is present when
    a file path is available.

    Parameters
    ----------
    inventory : dict
        Inventory dictionary expected to contain a `fonts` list with font
        descriptor mappings.

    Returns
    -------
    None

    Notes
    -----
    - Does not modify the schema version.
    - Does not delete fields.
    - Does not emit warnings.
    - Operation is idempotent.
    """

    fonts = inventory.get("fonts", [])
    for font in fonts:
        identity = font.get("identity")

        if not isinstance(identity, dict):
            continue

        if "file" in identity:
            continue

        if "path" in font:
            identity["file"] = font["path"]


def _validate_fonts_structure(inventory: dict) -> tuple[bool, list]:
    """
    Validate the structure of the `fonts` section in an inventory.

    Parameters
    ----------
    inventory : dict
        Inventory dictionary expected to contain a `fonts` list.

    Returns
    -------
    tuple[bool, list]
        A pair (ok, fonts):
        - ok is True if the `fonts` section exists, is a non-empty list,
          and all elements are dictionaries.
        - fonts is the extracted list (or an empty list on failure).
    """
    if "fonts" not in inventory:
        return False, []

    fonts = inventory.get("fonts")
    if not isinstance(fonts, list):
        return False, []

    if not fonts:
        return False, []

    if any(not isinstance(f, dict) for f in fonts):
        return False, []

    return True, fonts


def _load_inventory(
    inv_path: Path, *, require_platform: bool = True
) -> tuple[int, list]:
    """
    Load and strictly validate an inventory file.

    Parameters
    ----------
    inv_path : pathlib.Path
        Path to the inventory JSON file.
    require_platform : bool, optional
        If True, enforce platform compatibility between inventory metadata
        and the current runtime environment.

    Returns
    -------
    tuple[int, list]
        A pair (exit_code, fonts):
        - exit_code == 0 → success, fonts contains validated descriptors.
        - exit_code == 1 → validation or load error (already logged), fonts empty.

    Notes
    -----
    Validation rejects:
    - Invalid schema version.
    - Missing required metadata.
    - Platform-incompatible inventories (when require_platform is True).
    - Malformed or empty `fonts` section.
    - Semantic validation failures.

    Validation is always strict; non-strict operation is not supported.
    """
    try:
        with inv_path.open(encoding="utf-8") as f:
            inventory = json.load(f)

        if not isinstance(inventory, dict):
            log_err("Invalid inventory JSON: expected top-level object.")
            return 1, []

        metadata = inventory.get("metadata", {}) or {}
        if not isinstance(metadata, dict):
            log_err("Invalid inventory JSON: expected 'metadata' to be an object.")
            return 1, []

        schema_version = metadata.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            log_err(
                f"Unsupported inventory schema_version: {schema_version!r} "
                f"(required {SCHEMA_VERSION})"
            )
            return 1, []

        inv_env = metadata.get("run_environment")
        if require_platform and not isinstance(inv_env, dict):
            log_err("Inventory missing required metadata.run_environment (schema v1.2)")
            return 1, []

        if require_platform and isinstance(inv_env, dict):
            ok, mismatches = _enforce_platform(inv_env)
            if not ok:
                log_err(f"Inventory platform mismatch: {', '.join(mismatches)}")
                return 1, []

        log_trace_cat(
            log,
            "flow",
            "inventory JSON loaded",
            extra={
                "fonts_count": len(inventory.get("fonts", [])),
                "path": str(inv_path),
            },
        )

        normalize_loaded_enums(inventory)

        ok_fonts, fonts = _validate_fonts_structure(inventory)
        if not ok_fonts:
            log_err("Invalid inventory JSON: malformed or empty 'fonts' section.")
            return 1, []

        _normalize_inventory_paths(inventory)

        ok, semantic_warnings = enforce_semantic_validation(
            inventory,
            strict=True,
        )
        log_trace_cat(
            log,
            "flow",
            "semantic validation completed",
            extra={
                "ok": ok,
                "warnings": len(semantic_warnings),
            },
        )

        if not ok:
            for w in semantic_warnings:
                sev = w.get("severity", Severity.INFO)
                if sev in (Severity.ERROR, Severity.WARN):
                    log_err(w.get("message", "semantic validation error"))
            return 1, []

        log_ok(f"Inventory loaded: {inv_path} ({len(fonts)} fonts)")

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        log_err(f"failed to load inventory: {e}")
        return 1, []
    else:
        return 0, fonts
