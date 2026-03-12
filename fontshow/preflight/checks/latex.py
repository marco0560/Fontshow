"""
LuaLaTeX capability checks.

This module implements the preflight check verifying that the LuaLaTeX
engine required for catalog generation is available on the system.

Responsibilities
----------------
- Detect availability of the `lualatex` executable.
- Evaluate LuaLaTeX capability according to the current platform.
- Produce structured results describing LaTeX support.

Design principles
-----------------
The module checks only the presence of the LuaLaTeX engine and does not
perform document compilation. Platform-specific behavior is evaluated
based on runtime environment detection.

Architectural role
------------------
This module belongs to the **preflight subsystem** and implements the
LaTeX capability check executed during environment validation.
"""

import shutil

from fontshow.preflight.checks import environment
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult, Severity


def has_lualatex() -> bool:
    """
    Detect availability of the LuaLaTeX engine.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        True if `lualatex` is discoverable in `PATH`.
    """
    return shutil.which("lualatex") is not None


class LuaLatexCheck(BaseCheck):
    """
    Preflight check for LuaLaTeX availability.
    """

    check_id = "latex.capability"

    def run(self) -> CheckResult:
        """
        Execute the LuaLaTeX capability check.

        Parameters
        ----------
        None

        Returns
        -------
        CheckResult
            Structured result describing whether the `lualatex` engine is
            available and supported in the current environment.
        """
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
