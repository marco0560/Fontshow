# fontshow/preflight/checks/font_discovery.py

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
