import fontshow.preflight.checks.environment as environment
import fontshow.preflight.checks.font_discovery as font_discovery
import fontshow.preflight.checks.latex as latex
from fontshow.preflight.model import CheckResult, PreflightResult, Severity


def run_preflight() -> PreflightResult:
    results = []

    os_name = environment.detect_os()
    execution_mode = environment.detect_execution_mode()

    # --- Environment support (già esistente) ---
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

    # --- Font discovery capability ---
    if execution_mode == "ci":
        results.append(
            CheckResult(
                check_id="font_discovery.capability",
                severity=Severity.INFO,
                message="Font discovery checks skipped in CI environment",
                skipped=True,
            )
        )
    elif os_name == "linux":
        if font_discovery.has_fontconfig():
            results.append(
                CheckResult(
                    check_id="font_discovery.capability",
                    severity=Severity.OK,
                    message="Fontconfig backend available",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="font_discovery.capability",
                    severity=Severity.ERROR,
                    message="Fontconfig backend not found (fc-list missing)",
                )
            )
    elif os_name == "windows":
        results.append(
            CheckResult(
                check_id="font_discovery.capability",
                severity=Severity.WARN,
                message="Font discovery backend availability is experimental on Windows",
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="font_discovery.capability",
                severity=Severity.ERROR,
                message="No supported font discovery backend for this operating system",
            )
        )

    # --- latex.capability ---
    if execution_mode == "ci":
        results.append(
            CheckResult(
                check_id="latex.capability",
                severity=Severity.INFO,
                message="LuaLaTeX checks skipped in CI environment",
                skipped=True,
            )
        )
    elif os_name == "linux":
        if latex.has_lualatex():
            results.append(
                CheckResult(
                    check_id="latex.capability",
                    severity=Severity.OK,
                    message="LuaLaTeX engine available",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="latex.capability",
                    severity=Severity.ERROR,
                    message="LuaLaTeX engine not found (lualatex missing)",
                )
            )
    elif os_name == "windows":
        if latex.has_lualatex():
            results.append(
                CheckResult(
                    check_id="latex.capability",
                    severity=Severity.WARN,
                    message="LuaLaTeX available on experimental Windows environment",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="latex.capability",
                    severity=Severity.ERROR,
                    message="LuaLaTeX engine not found on Windows",
                )
            )
    else:
        results.append(
            CheckResult(
                check_id="latex.capability",
                severity=Severity.ERROR,
                message="LuaLaTeX is not supported on this operating system",
            )
        )

    return PreflightResult(results=results)
