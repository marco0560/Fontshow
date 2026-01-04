from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fontshow.preflight.checks.base import BaseCheck

import fontshow.preflight.checks.environment as environment
import fontshow.preflight.checks.font_discovery as font_discovery
import fontshow.preflight.checks.latex as latex

# NOTE:
# The following imports are part of the public runner API and are
# intentionally exposed for test monkeypatching.

__all__ = [
    "run_preflight",
    "CHECKS",
    "environment",
    "font_discovery",
    "latex",
]

from fontshow.preflight.checks.environment import EnvironmentSupportCheck
from fontshow.preflight.checks.font_discovery import FontDiscoveryCheck
from fontshow.preflight.checks.latex import LuaLatexCheck
from fontshow.preflight.model import CheckResult, PreflightResult

# Public check registry (source of truth).
#
# - Used by the runner to define default execution order.
# - Used by tests to assert the BaseCheck contract and expected coverage.
# - Keep this list deterministic: no dynamic discovery here.
#
# Selection (enable/disable subsets) is handled by run_preflight(), but CHECKS
# remains the authoritative registry of built-in checks.
CHECKS = [
    EnvironmentSupportCheck,
    FontDiscoveryCheck,
    LuaLatexCheck,
]


def _select_checks(
    *,
    enabled: set[str] | None,
    disabled: set[str] | None,
) -> list[type[BaseCheck]]:
    selected = []

    for check_cls in CHECKS:
        cid = check_cls.check_id

        if enabled is not None and cid not in enabled:
            continue
        if disabled is not None and cid in disabled:
            continue

        selected.append(check_cls)

    return selected


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
    2. Otherwise, checks are selected from CHECKS using `enabled` / `disabled`.

    By default, all checks listed in CHECKS are executed in deterministic order.
    """
    results: list[CheckResult] = []

    if checks is not None:
        active_checks = checks
    else:
        active_checks = _select_checks(enabled=enabled, disabled=disabled)

    for check_cls in active_checks:
        check = check_cls()
        results.append(check.run())

    return PreflightResult(results)
