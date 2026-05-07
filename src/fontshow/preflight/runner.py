"""
Preflight execution engine.

This module implements the core logic responsible for executing the
registered preflight checks and aggregating their results.

Responsibilities
----------------
- Select and execute preflight check classes.
- Aggregate check results into a structured preflight report.
- Provide deterministic execution order for built-in checks.
- Support runtime check registration.

Design principles
-----------------
The runner orchestrates check execution but does not implement the
checks themselves. Individual checks remain isolated classes that
produce structured results consumed by this module.

Architectural role
------------------
This module belongs to the **preflight subsystem** and implements the
execution stage responsible for running environment validation checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import Severity
from fontshow.preflight.checks import environment, font_discovery, latex, ontology
from fontshow.preflight.model import CheckResult, PreflightResult
from fontshow.preflight.registry import get_registered_checks

if TYPE_CHECKING:
    from fontshow.preflight.checks.base import BaseCheck

# NOTE:
# The following symbols are part of the public runner API and are
# intentionally exposed for test monkeypatching (tests patch
# runner.environment / runner.font_discovery / runner.latex).
__all__ = [
    "run_preflight",
    "CHECKS",
    "environment",
    "font_discovery",
    "latex",
    "ontology",
]

# Import built-in check classes (must exist before CHECKS is defined)
from fontshow.preflight.checks.environment import EnvironmentSupportCheck
from fontshow.preflight.checks.font_discovery import FontDiscoveryCheck
from fontshow.preflight.checks.latex import LuaLatexCheck
from fontshow.preflight.checks.ontology import OntologyCheck

# Built-in checks (stable, explicit). Registry may add more checks at runtime,
# but CHECKS remains the authoritative list of built-in checks for tests/docs.
CHECKS: list[type[BaseCheck]] = [
    EnvironmentSupportCheck,
    FontDiscoveryCheck,
    LuaLatexCheck,
    OntologyCheck,
]


def _select_checks(
    *,
    checks: list[type[BaseCheck]],
    enabled: set[str] | None,
    disabled: set[str] | None,
) -> list[type[BaseCheck]]:
    """
    Filter candidate checks according to enabled and disabled sets.

    Parameters
    ----------
    checks : list[type[BaseCheck]]
        Candidate check classes to filter.
    enabled : set[str] | None
        Optional whitelist of check identifiers.
    disabled : set[str] | None
        Optional blacklist of check identifiers.

    Returns
    -------
    list[type[BaseCheck]]
        Ordered list of selected check classes.

    Notes
    -----
    Filtering preserves input order and applies the enabled whitelist
    before the disabled blacklist.
    """
    selected: list[type[BaseCheck]] = []

    for check_cls in checks:
        cid = check_cls.check_id

        if enabled is not None and cid not in enabled:
            continue
        if disabled is not None and cid in disabled:
            continue

        selected.append(check_cls)

    return selected


def _resolve_checks() -> list[type[BaseCheck]]:
    """
    Resolve the effective list of checks to execute.

    Parameters
    ----------
    None

    Returns
    -------
    list[type[BaseCheck]]
        Registered checks if the registry is non-empty, otherwise the
        built-in `CHECKS` list.

    Notes
    -----
    Priority:
    1. Registered checks (if any).
    2. Built-in `CHECKS` fallback.
    """
    registered = get_registered_checks()
    return registered if registered else CHECKS


def run_preflight(
    *,
    enabled: set[str] | None = None,
    disabled: set[str] | None = None,
    checks: list[type[BaseCheck]] | None = None,
) -> PreflightResult:
    """
    Run preflight checks and aggregate their results.

    Parameters
    ----------
    enabled : set[str] | None, optional
        Optional whitelist of check identifiers to run when ``checks``
        is not provided.
    disabled : set[str] | None, optional
        Optional blacklist of check identifiers to skip when ``checks``
        is not provided.
    checks : list[type[BaseCheck]] | None, optional
        Explicit check classes to execute. When provided, this overrides
        registry resolution and ``enabled`` / ``disabled`` filtering.

    Returns
    -------
    PreflightResult
        Aggregate result containing one ``CheckResult`` for each
        executed or skipped check.

    Raises
    ------
    Exception
        Propagates exceptions raised while instantiating a check class
        or executing ``check.run()``. This runner intentionally does
        not mask unexpected check failures.

    Notes
    -----
    Selection precedence:
    1. If ``checks`` is provided, only those check classes are
       executed. Intended for tests and advanced usage.
    2. Otherwise, checks are selected from the resolved registry using
       ``enabled`` and ``disabled``.

    By default, all checks listed in ``CHECKS`` are executed in
    deterministic order.
    """
    log_trace_cat(
        log,
        "flow",
        "preflight started",
        extra={
            "enabled_count": None if enabled is None else len(enabled),
            "disabled_count": None if disabled is None else len(disabled),
            "checks_override": checks is not None,
        },
    )

    results: list[CheckResult] = []

    if checks is not None:
        active_checks = checks
    else:
        base_checks = _resolve_checks()
        active_checks = _select_checks(
            checks=base_checks,
            enabled=enabled,
            disabled=disabled,
        )

    for check_cls in active_checks:
        if not getattr(check_cls, "executable", True):
            results.append(
                CheckResult(
                    check_id=check_cls.check_id,
                    severity=Severity.INFO,
                    skipped=True,
                    message="Check skipped (executable=False)",
                )
            )
            continue
        log_trace_cat(
            log,
            "flow",
            "preflight check started",
            extra={
                "check_id": check_cls.check_id,
            },
        )
        check = check_cls()
        result = check.run()
        log_trace_cat(
            log,
            "flow",
            "preflight check completed",
            extra={
                "check_id": check_cls.check_id,
                "severity": result.severity.name,
                "skipped": result.skipped,
            },
        )
        results.append(result)

    log_trace_cat(
        log,
        "flow",
        "preflight completed",
        extra={
            "checks_run": len(results),
        },
    )

    return PreflightResult(results)
