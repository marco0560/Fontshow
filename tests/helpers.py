import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace

from fontshow.preflight.model import CheckResult, Severity


def minimal_valid_entry(extra: dict | None = None) -> dict:
    entry = {
        "path": "/usr/share/fonts/test.ttf",
        "format": "TrueType",
        "style": "Regular",
        "family": "Test Family",
        "identity": {
            "file": "/usr/share/fonts/test.ttf",
            "family": "Test Family",
            "style": "Regular",
        },
        "base_names": ["Test Family"],
    }

    if extra:
        entry.update(extra)

    return entry


# Environment-matrix tests must not depend on host capabilities
# (LuaLaTeX, fontconfig, etc.). We remove capability checks entirely.


def make_fc_query_output(
    *,
    lang: str | None = None,
    scripts: list[str] | None = None,
    decorative: bool | None = None,
    color: bool | None = None,
    variable: bool | None = None,
    returncode: int = 0,
):
    """
    Factory helper for mocking fc-query output.

    Returns an object compatible with the result of run_command(),
    exposing a 'stdout' attribute.
    """
    lines: list[str] = []

    if lang:
        lines.append(f"lang: {lang}")

    if scripts:
        caps = " ".join(f"otlayout:{s}" for s in scripts)
        lines.append(f'capability: "{caps}"')

    if decorative is not None:
        lines.append(f"decorative: {'true' if decorative else 'false'}")

    if color is not None:
        lines.append(f"color: {'true' if color else 'false'}")

    if variable is not None:
        lines.append(f"variable: {'true' if variable else 'false'}")

    return SimpleNamespace(stdout="\n".join(lines), stderr="", returncode=returncode)


def _ok_result(check_id: str):
    return CheckResult(
        check_id=check_id,
        severity=Severity.OK,
        message="stubbed OK",
        skipped=False,
    )


def run_preflight_with_environment(
    monkeypatch,
    *,
    os_name: str,
    execution_mode: str,
):
    # Environment detection
    monkeypatch.setattr(
        "fontshow.preflight.checks.environment.detect_os",
        lambda: os_name,
    )
    monkeypatch.setattr(
        "fontshow.preflight.checks.environment.detect_execution_mode",
        lambda: execution_mode,
    )

    from fontshow.preflight.runner import CHECKS

    monkeypatch.setattr(
        "fontshow.preflight.runner.CHECKS",
        [
            check
            for check in CHECKS
            if check.__name__ not in {"LuaLatexCheck", "FontDiscoveryCheck"}
        ],
    )

    monkeypatch.setattr(
        "fontshow.preflight.checks.font_discovery.FontDiscoveryCheck.run",
        lambda self: CheckResult(
            check_id="font.discovery",
            severity=Severity.OK,
            message="Font discovery mocked as available",
        ),
    )

    from fontshow.preflight.checks.environment import EnvironmentSupportCheck
    from fontshow.preflight.runner import run_preflight

    return run_preflight(checks=[EnvironmentSupportCheck])


def run_cli(main_func, argv):
    """
    Invoke a CLI entrypoint capturing exit code and stdout.

    Args:
        main_func: CLI main function (e.g. fontshow.__main__.main)
        argv: argument vector, including program name

    Returns:
        (exit_code, stdout)
    """
    old_argv = sys.argv
    sys.argv = argv[:]  # important: copy argv exactly as CLI would receive it

    stdout = StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stdout):
            try:
                # Call the real CLI entrypoint.
                # It is expected to read sys.argv[1:].
                result = main_func()

                # Normalize return value to CLI semantics
                if isinstance(result, int):
                    raise SystemExit(result)  # noqa: TRY301
                raise SystemExit(0)  # noqa: TRY301

            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1

            except Exception:  # noqa: BLE001
                # (intentional: map any unexpected error to exit code 2)
                code = 2
    finally:
        sys.argv = old_argv

    return code, stdout.getvalue()
