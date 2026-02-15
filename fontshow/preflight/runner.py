from __future__ import annotations

from typing import TYPE_CHECKING

from fontshow.logging_utils import log, log_trace_cat
from fontshow.preflight.checks import environment, font_discovery, latex
from fontshow.preflight.model import CheckResult, PreflightResult, Severity
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
]

# Import built-in check classes (must exist before CHECKS is defined)
from fontshow.preflight.checks.environment import EnvironmentSupportCheck
from fontshow.preflight.checks.font_discovery import FontDiscoveryCheck
from fontshow.preflight.checks.latex import LuaLatexCheck

# Built-in checks (stable, explicit). Registry may add more checks at runtime,
# but CHECKS remains the authoritative list of built-in checks for tests/docs.
CHECKS: list[type[BaseCheck]] = [
    EnvironmentSupportCheck,
    FontDiscoveryCheck,
    LuaLatexCheck,
]


def _select_checks(
    *,
    checks: list[type[BaseCheck]],
    enabled: set[str] | None,
    disabled: set[str] | None,
) -> list[type[BaseCheck]]:
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

    Priority:
    1. Registered checks (if any)
    2. Built-in CHECKS fallback
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
    Run preflight checks and return a PreflightResult.

    Selection precedence:
    1. If `checks` is provided, only those check classes are executed.
       (Intended for tests and advanced usage.)
    2. Otherwise, checks are selected from the resolved registry using
       `enabled` / `disabled`.

    By default, all checks listed in CHECKS are executed in deterministic order.
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
