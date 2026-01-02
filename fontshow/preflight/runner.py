from .model import CheckResult, PreflightResult


def run_preflight() -> PreflightResult:
    """
    Execute preflight checks and return aggregated results.

    This function performs no I/O and does not raise SystemExit.
    """
    results: list[CheckResult] = []

    # Placeholder: real checks will be added incrementally
    return PreflightResult(results=results)
