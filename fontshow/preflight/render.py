# fontshow/preflight/render.py

from collections.abc import Iterable

from fontshow.types import Severity

from .model import CheckResult, PreflightResult


def preflight_exit_code(result: PreflightResult) -> int:
    """
    Compute process exit code from preflight result severity.
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
