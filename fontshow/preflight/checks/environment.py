# fontshow/preflight/checks/environment.py

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult, Severity


def detect_os() -> str:
    import platform

    system = platform.system().lower()
    if system.startswith("linux"):
        return "linux"
    if system.startswith("windows"):
        return "windows"
    if system.startswith("darwin"):
        return "macos"
    return "unknown"


def detect_execution_mode() -> str:
    import os
    from pathlib import Path

    if os.environ.get("CI"):
        return "ci"
    if "WSL_DISTRO_NAME" in os.environ:
        return "wsl"
    if Path("/.dockerenv").exists():
        return "container"
    return "bare-metal"


class EnvironmentSupportCheck(BaseCheck):
    check_id = "environment.support"

    def run(self) -> CheckResult:
        os_name = detect_os()
        execution_mode = detect_execution_mode()

        if os_name == "linux" and execution_mode == "bare-metal":
            return CheckResult(
                self.check_id,
                Severity.OK,
                "Running on supported Linux bare-metal environment",
            )

        if os_name in {"linux", "windows"}:
            return CheckResult(
                self.check_id,
                Severity.WARN,
                f"Running on {os_name} in a {execution_mode} environment",
            )

        return CheckResult(
            self.check_id,
            Severity.ERROR,
            f"Unsupported operating system: {os_name}",
        )
