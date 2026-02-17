from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fontshow.types import Severity, WarningInfo


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
