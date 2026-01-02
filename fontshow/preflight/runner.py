from fontshow.preflight.checks.environment import detect_execution_mode, detect_os

from .model import CheckResult, PreflightResult

os_name = detect_os()
mode = detect_execution_mode()

# la traduzione in CheckResult arriverà nel prossimo step


def run_preflight() -> PreflightResult:
    """
    Execute preflight checks and return aggregated results.

    This function performs no I/O and does not raise SystemExit.
    """
    results: list[CheckResult] = []

    # Placeholder: real checks will be added incrementally
    return PreflightResult(results=results)
