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

import os
import shutil
from pathlib import Path

from fontshow.preflight.checks import environment
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult, Severity


def _windows_lualatex_candidates() -> list[Path]:
    """
    Return deterministic Windows fallback locations for LuaLaTeX.

    Parameters
    ----------
    None

    Returns
    -------
    list[pathlib.Path]
        Candidate executable paths checked when ``lualatex`` is not
        discoverable via ``PATH`` on Windows.

    Notes
    -----
    The fallback is intentionally conservative and limited to common
    TeX Live installation roots. It does not recurse the filesystem or
    execute any external commands.
    """
    candidates: list[Path] = []

    texlive_root = Path("C:/texlive")
    if texlive_root.exists():
        for year_dir in sorted(texlive_root.iterdir(), reverse=True):
            if not year_dir.is_dir():
                continue
            candidates.append(year_dir / "bin" / "windows" / "lualatex.exe")

    profile_root = os.environ.get("USERPROFILE")
    if profile_root:
        candidates.append(
            Path(profile_root)
            / "AppData"
            / "Local"
            / "Programs"
            / "TeX Live"
            / "bin"
            / "win32"
            / "lualatex.exe"
        )

    return candidates


def has_lualatex() -> bool:
    """
    Detect availability of the LuaLaTeX engine.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        True if `lualatex` is discoverable in `PATH` or in a supported
        Windows fallback location.

    Notes
    -----
    This function performs a simple executable lookup only. It does not
    verify that the engine can successfully compile a document.

    On Windows, the check also inspects a small set of common TeX Live
    installation paths so preflight remains useful when the TeX Live
    bin directory is installed but not exported into ``PATH``.
    """
    if shutil.which("lualatex") is not None:
        return True

    if environment.detect_os() != "windows":
        return False

    return any(candidate.is_file() for candidate in _windows_lualatex_candidates())


class LuaLatexCheck(BaseCheck):
    """
    Preflight check for LuaLaTeX availability.

    Notes
    -----
    The check evaluates tool availability and coarse platform support
    only. It does not execute LuaLaTeX.
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

        Notes
        -----
        Linux bare-metal environments require LuaLaTeX for a successful
        result. CI and Windows environments use downgraded result
        severities to reflect partial or experimental support.
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
