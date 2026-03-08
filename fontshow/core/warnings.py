"""
Structured warning utilities.

This module provides helpers used across the Fontshow pipeline to
attach structured warning objects to inventory data structures.

Responsibilities
----------------
- Provide the canonical structured warning emitter.
- Attach machine-readable warnings to inventory or font entries.
- Ensure warnings follow a consistent schema across pipeline stages.

Design principles
-----------------
Warnings must be emitted through a single centralized helper so that
all pipeline stages produce consistent warning structures. The helper
must remain lightweight and must not depend on higher-level orchestration
logic.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and implements
the shared warning mechanism used by the inventory, catalog, and CLI
subsystems.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fontshow.core.types import Severity, WarningInfo


def add_structured_warning(
    container: dict[str, Any],
    *,
    code: str,
    message: str,
    severity: Severity,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Canonical structured warning emitter.

    Single source of truth across:
    - dump
    - parse
    - create_catalog
    - validation

    Container must be:
        font dict OR inventory dict

    Attach a structured warning to an inventory node.

    Parameters
    ----------
    target : dict
        Inventory root or font entry.
    code : str
        Machine-readable warning code.
    message : str
        Human-readable warning message.
    severity : Severity, optional
        Severity level (default: ``"Severity.WARN"``).

    Notes
    -----
    - Warnings are appended to the ``warnings`` list of the target.
    - The target dictionary is modified in place.
    """

    w: WarningInfo = {
        "code": code,
        "message": message,
        "severity": severity,
    }

    if extra:
        w["extra"] = extra

    container.setdefault("warnings", []).append(w)
