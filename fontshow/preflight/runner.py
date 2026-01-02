import fontshow.preflight.checks.environment as environment
from fontshow.preflight.model import CheckResult, PreflightResult, Severity


def run_preflight() -> PreflightResult:
    """
    Execute preflight checks and return aggregated results.

    This function performs no I/O and does not raise SystemExit.
    """
    results: list[CheckResult] = []

    os_name = environment.detect_os()
    execution_mode = environment.detect_execution_mode()

    # Environment support check
    if os_name == "linux":
        if execution_mode == "bare-metal":
            results.append(
                CheckResult(
                    check_id="environment.support",
                    severity=Severity.OK,
                    message="Running on supported Linux environment",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="environment.support",
                    severity=Severity.WARN,
                    message="Running on Linux in a virtualized environment",
                )
            )

    elif os_name == "windows":
        results.append(
            CheckResult(
                check_id="environment.support",
                severity=Severity.WARN,
                message="Running on experimental Windows environment",
            )
        )

    elif os_name == "macos":
        results.append(
            CheckResult(
                check_id="environment.support",
                severity=Severity.ERROR,
                message="macOS is not supported in the current version",
            )
        )

    else:
        results.append(
            CheckResult(
                check_id="environment.support",
                severity=Severity.ERROR,
                message="Unsupported operating system",
            )
        )

    return PreflightResult(results=results)
