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
from typing import TYPE_CHECKING, Any, Literal, cast, overload

from fontshow.core.cli_utils import log_err, log_ok
from fontshow.core.global_constants import SCHEMA_VERSION
from fontshow.core.json_boundary import normalize_loaded_enums
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import Severity
from fontshow.inventory.metadata_processing import font_family
from fontshow.inventory.schema_validation import _validate_inventory_schema_strict
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

    Parameters
    ----------
    data : dict[str, Any]
        Inventory root object expected to contain a `fonts` list.

    Returns
    -------
    list[Any] | None
        The fonts list if present and valid, otherwise None.

    Notes
    -----
    This helper performs only container-shape validation. It does not
    validate individual font entries.
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

    Notes
    -----
    Grouping is stable and deterministic because it preserves the first
    occurrence of each family in the input order.
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

    Notes
    -----
    This helper performs shallow structural validation only. It does
    not validate schema details or per-font semantic correctness.
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


@overload
def _load_inventory(
    inv_path: Path,
    *,
    require_platform: bool = True,
    return_metadata: Literal[False] = False,
) -> tuple[int, list]: ...


@overload
def _load_inventory(
    inv_path: Path,
    *,
    require_platform: bool = True,
    return_metadata: Literal[True],
) -> tuple[int, list, dict[str, Any]]: ...


def _load_inventory(
    inv_path: Path,
    *,
    require_platform: bool = True,
    return_metadata: bool = False,
) -> tuple[int, list] | tuple[int, list, dict[str, Any]]:
    """
    Load and strictly validate an inventory file.

    Parameters
    ----------
    inv_path : pathlib.Path
        Path to the inventory JSON file.
    require_platform : bool, optional
        If True, enforce platform compatibility between inventory metadata
        and the current runtime environment.
    return_metadata : bool, optional
        If True, include the validated inventory metadata object in the
        return tuple.

    Returns
    -------
    tuple[int, list] | tuple[int, list, dict[str, Any]]
        A pair ``(exit_code, fonts)`` by default, or a triple
        ``(exit_code, fonts, metadata)`` when ``return_metadata`` is
        true:
        - exit_code == 0 → success, fonts contains validated descriptors.
        - exit_code == 1 → validation or load error (already logged), fonts empty.

    Raises
    ------
    None
        All filesystem, decoding, and validation exceptions handled by
        this helper are converted into logged error messages and a
        ``(1, [])`` result.

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

        failure_result: tuple[int, list] | tuple[int, list, dict[str, Any]]
        failure_result = (1, [], {}) if return_metadata else (1, [])

        if not isinstance(inventory, dict):
            log_err("Invalid inventory JSON: expected top-level object.")
            return failure_result

        metadata = inventory.get("metadata", {}) or {}
        if not isinstance(metadata, dict):
            log_err("Invalid inventory JSON: expected 'metadata' to be an object.")
            return failure_result

        schema_version = metadata.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            log_err(
                f"Unsupported inventory schema_version: {schema_version!r} "
                f"(required {SCHEMA_VERSION})"
            )
            return failure_result

        _validate_inventory_schema_strict(inventory)

        inv_env = metadata.get("run_environment")
        if require_platform and not isinstance(inv_env, dict):
            log_err(
                "Inventory missing required metadata.run_environment "
                f"(schema v{SCHEMA_VERSION})"
            )
            return failure_result

        if require_platform and isinstance(inv_env, dict):
            ok, mismatches = _enforce_platform(inv_env)
            if not ok:
                log_err(f"Inventory platform mismatch: {', '.join(mismatches)}")
                return failure_result

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
            return failure_result

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
            return failure_result

        log_ok(f"Inventory loaded: {inv_path} ({len(fonts)} fonts)")

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        log_err(f"failed to load inventory: {e}")
        return (1, [], {}) if return_metadata else (1, [])
    else:
        if return_metadata:
            return 0, fonts, metadata
        return 0, fonts
