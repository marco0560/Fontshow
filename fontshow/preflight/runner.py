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

# Public check registry (used by tests)
CHECKS = [
    EnvironmentSupportCheck,
    FontDiscoveryCheck,
    LuaLatexCheck,
]


def run_preflight(*, checks: list[type] | None = None) -> PreflightResult:
    """
    Execute preflight checks.

    Parameters
    ----------
    checks:
        Optional list of Check classes to execute.
        Defaults to the full CHECKS registry.
    """
    results: list[CheckResult] = []

    active_checks = checks or CHECKS

    for check_cls in active_checks:
        check = check_cls()
        results.append(check.run())

    return PreflightResult(results=results)
