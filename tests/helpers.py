"""
Test helper utilities for the Fontshow test suite.

Responsibilities
----------------
- Provide helper functions for constructing minimal inventory and font
  structures used in tests.
- Offer utilities for invoking the CLI and capturing output streams.
- Centralize reusable testing primitives shared across modules.

Design principles
-----------------
Helpers encapsulate common setup logic so that individual tests remain
focused on behavior verification rather than environment preparation.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and provides
utility functions used throughout the Fontshow test suite.
"""

from __future__ import annotations

import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace
from typing import Any

from fontshow.inventory.platform_metadata import collect_platform_metadata
from fontshow.preflight.model import CheckResult, Severity

# ============================================================
# Canonical minimal VALID schema-1.2 font entry
# ============================================================


def minimal_font_entry_v12() -> dict[str, Any]:
    """
    Canonical minimal VALID font entry for schema 1.2.

    Deterministic and schema-compliant.
    """

    return {
        "path": "/fake/font.ttf",
        "family": "Test",
        "subfamily": "Regular",
        "typographic_subfamily": "Regular",
        "full_name": "Test Regular",
        "postscript_name": "Test-Regular",
        "version_string": "1.0",
        "unique_font_id": "test-regular-1.0",
        "units_per_em": 1000,
        "ascent": 800,
        "descent": -200,
        "weight_class": 400,
        "width_class": 5,
        "italic_angle": 0,
        "is_fixed_pitch": False,
        "glyph_count": 1,
        "coverage": {
            "unicode_blocks": {},
            "scripts": [],
            "languages": [],
        },
        "inference": {
            "level": "medium",
            "scripts": [],
            "languages": [],
            "declared_scripts": [],
            "declared_languages": [],
            "unicode_blocks": {},
        },
        "charset": {
            "ranges": [],
        },
        "sample_text": {
            "source": "font",
            "text": "A",
        },
        "specimen_text": "A",
        "specimen_strategy": "cmap",
        "specimen_glyph_count": 1,
    }


# ============================================================
# Canonical minimal VALID schema-1.2 inventory
# ============================================================


def minimal_inventory_v12() -> dict[str, Any]:
    """
    Canonical minimal VALID inventory for schema 1.2.
    """

    return {
        "metadata": {
            "schema_version": "1.2",
            "run_environment": collect_platform_metadata(),
            "input_inventory_tool": "fontshow-test",
            "input_inventory_tool_version": "0.1",
            "inference_level": "medium",
            "fonttools": {
                "available": True,
                "fontconfig_charset_included": False,
                "version": "4.38.0",
            },
        },
        "fonts": [minimal_font_entry_v12()],
    }


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
