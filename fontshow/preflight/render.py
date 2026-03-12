"""
Preflight result rendering helpers.

This module implements utilities used to transform preflight check
results into human-readable output for the command-line interface.

Responsibilities
----------------
- Convert preflight results into formatted text lines.
- Compute deterministic process exit codes from check outcomes.
- Provide presentation helpers used by the preflight CLI entry point.

Design principles
-----------------
Rendering logic is kept separate from check execution so that the
preflight runner produces structured results while this module
handles only presentation concerns.

Architectural role
------------------
This module belongs to the **preflight subsystem** and implements the
presentation layer used by the preflight CLI interface.
"""

from collections.abc import Iterable

from fontshow.core.types import Severity

from .model import CheckResult, PreflightResult


def preflight_exit_code(result: PreflightResult) -> int:
    """
    Compute process exit code from preflight result severity.

    Parameters
    ----------
    result : PreflightResult
        Aggregate preflight result to evaluate.

    Returns
    -------
    int
        `1` when any check has error severity, otherwise `0`.
    """
    if result.overall_severity is Severity.ERROR:
        return 1
    return 0


def render_preflight_results(
    results: Iterable[CheckResult],
    verbose: bool = False,
) -> list[str]:
    """
    Render preflight results into human-readable lines.

    Parameters
    ----------
    results : Iterable[CheckResult]
        Check results to render.
    verbose : bool, optional
        Reserved verbosity flag for future rendering variants.

    Returns
    -------
    list[str]
        Formatted output lines suitable for CLI presentation.
    """
    _ = verbose  # reserved for future verbosity-aware rendering
    lines: list[str] = []

    for r in results:
        prefix = {
            Severity.INFO: "[INFO]",
            Severity.OK: "[OK  ]",
            Severity.WARN: "[WARN]",
            Severity.ERROR: "[ERR ]",
        }[r.severity]

        lines.append(f"{prefix} {r.check_id}: {r.message}")

    return lines
