# fontshow/preflight/render.py

from collections.abc import Iterable

from .model import CheckResult, PreflightResult, Severity


def render_preflight_results(
    results: Iterable[CheckResult],
    verbose: bool = False,
) -> list[str]:
    """
    Render preflight results into human-readable lines.

    Returns a list of lines ready to be printed.
    """
    lines: list[str] = []

    for r in results:
        if r.severity is Severity.INFO and not verbose:
            continue
        if r.severity is Severity.OK and not verbose:
            continue

        prefix = {
            Severity.INFO: "[INFO]",
            Severity.OK: "[OK  ]",
            Severity.WARN: "[WARN]",
            Severity.ERROR: "[ERR ]",
        }[r.severity]

        lines.append(f"{prefix} {r.check_id}: {r.message}")

    return lines


def preflight_exit_code(result: PreflightResult) -> int:
    if result.overall_severity is Severity.ERROR:
        return 1
    return 0
