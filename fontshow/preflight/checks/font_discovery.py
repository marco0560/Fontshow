"""
Font discovery capability checks.

This module implements the preflight check verifying that the system
supports font discovery required by the inventory generation pipeline.

Responsibilities
----------------
- Detect availability of the `fc-list` command used by Fontconfig.
- Evaluate whether font discovery is supported on the current platform.
- Produce structured results describing discovery capability.

Design principles
-----------------
Font discovery checks verify only the availability of required system
tools and do not perform actual font enumeration. The module isolates
environment capability checks from the inventory pipeline.

Architectural role
------------------
This module belongs to the **preflight subsystem** and implements the
font discovery capability check used during environment validation.
"""

import shutil

from fontshow.preflight.checks import environment
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult, Severity


def has_fontconfig() -> bool:
    """
    Detect availability of fontconfig (fc-list).
    """

    return shutil.which("fc-list") is not None


class FontDiscoveryCheck(BaseCheck):
    """
    Preflight check for font discovery capability.
    """

    check_id = "font_discovery.capability"

    def run(self) -> CheckResult:
        os_name = environment.detect_os()
        execution_mode = environment.detect_execution_mode()

        if os_name == "linux":
            if execution_mode == "ci":
                return CheckResult(
                    self.check_id,
                    Severity.INFO,
                    "Font discovery skipped in CI environment",
                    skipped=True,
                )

            if has_fontconfig():
                return CheckResult(
                    self.check_id,
                    Severity.OK,
                    "fontconfig available",
                )

            return CheckResult(
                self.check_id,
                Severity.ERROR,
                "fontconfig not available",
            )

        if os_name == "windows":
            return CheckResult(
                self.check_id,
                Severity.WARN,
                "Font discovery limited on Windows",
            )

        # macOS or unknown
        return CheckResult(
            self.check_id,
            Severity.ERROR,
            "Font discovery not supported on this OS",
        )
