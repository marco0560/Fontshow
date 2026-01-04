# fontshow/preflight/checks/latex.py

import shutil

from fontshow.preflight.checks import environment
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult, Severity


def has_lualatex() -> bool:
    """
    Detect availability of the LuaLaTeX engine.
    """
    return shutil.which("lualatex") is not None


class LuaLatexCheck(BaseCheck):
    """
    Preflight check for LuaLaTeX availability.
    """

    check_id = "latex.capability"

    def run(self) -> CheckResult:
        os_name = environment.detect_os()
        execution_mode = environment.detect_execution_mode()

        if os_name == "linux":
            if execution_mode == "ci":
                if has_lualatex():
                    return CheckResult(
                        self.check_id,
                        Severity.INFO,
                        "LuaLaTeX available (CI environment)",
                        skipped=True,
                    )
                return CheckResult(
                    self.check_id,
                    Severity.ERROR,
                    "LuaLaTeX not available in CI",
                )

            # linux bare-metal
            if has_lualatex():
                return CheckResult(
                    self.check_id,
                    Severity.OK,
                    "LuaLaTeX available",
                )
            return CheckResult(
                self.check_id,
                Severity.ERROR,
                "LuaLaTeX not available",
            )

        if os_name == "windows":
            if has_lualatex():
                return CheckResult(
                    self.check_id,
                    Severity.WARN,
                    "LuaLaTeX available on Windows (experimental)",
                )
            return CheckResult(
                self.check_id,
                Severity.ERROR,
                "LuaLaTeX not available on Windows",
            )

        # macOS or unknown
        return CheckResult(
            self.check_id,
            Severity.ERROR,
            "LuaLaTeX not supported on this OS",
        )
