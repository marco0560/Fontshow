"""
Environment capability checks.

This module implements the preflight check responsible for verifying
that the current execution environment is supported by Fontshow.

Responsibilities
----------------
- Detect the operating system used to run Fontshow.
- Detect the execution mode (bare-metal, container, WSL, CI).
- Report whether the detected environment is supported.

Design principles
-----------------
Environment detection is implemented using lightweight runtime checks
without relying on external tools. The module produces structured
results describing environment compatibility.

Architectural role
------------------
This module belongs to the **preflight subsystem** and provides the
environment support check executed during the preflight validation
pipeline.
"""

from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult, Severity


def detect_os() -> str:
    """
    Detect the normalized operating-system identifier for the host.

    Parameters
    ----------
    None

    Returns
    -------
    str
        One of ``"linux"``, ``"windows"``, ``"macos"``, or
        ``"unknown"``.
    """
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
    """
    Detect the high-level execution mode of the current environment.

    Parameters
    ----------
    None

    Returns
    -------
    str
        One of ``"ci"``, ``"wsl"``, ``"container"``, or
        ``"bare-metal"``.
    """
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
    """
    Preflight check evaluating whether the runtime environment is supported.

    Parameters
    ----------
    None
    """

    check_id = "environment.support"

    def run(self) -> CheckResult:
        """
        Execute the environment support check.

        Parameters
        ----------
        None

        Returns
        -------
        CheckResult
            Structured result describing whether the detected OS and
            execution mode are fully supported, partially supported, or
            unsupported.
        """
        os_name = detect_os()
        execution_mode = detect_execution_mode()

        log_trace_cat(
            log,
            "raw",
            "environment detected",
            extra={
                "os_name": os_name,
                "execution_mode": execution_mode,
            },
        )

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
