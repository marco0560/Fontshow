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
from typing import TYPE_CHECKING, Any

from fontshow.inventory.platform_metadata import collect_platform_metadata
from fontshow.preflight.model import CheckResult, Severity

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================
# Canonical minimal VALID schema-1.2 font entry
# ============================================================


def minimal_font_entry_v12() -> dict[str, Any]:
    """
    Canonical minimal VALID font entry for schema 1.2.

    Deterministic and schema-compliant.

    Returns
    -------
    dict[str, Any]
        Minimal schema-valid font descriptor used by structural and
        integration tests.
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

    Returns
    -------
    dict[str, Any]
        Minimal schema-valid inventory containing one font entry and
        runtime metadata.
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

    Parameters
    ----------
    lang : str | None, optional
        Language string emitted in the fake ``lang:`` field.
    scripts : list[str] | None, optional
        Script tags converted into fake ``capability`` entries.
    decorative : bool | None, optional
        Decorative flag emitted when provided.
    color : bool | None, optional
        Color-font flag emitted when provided.
    variable : bool | None, optional
        Variable-font flag emitted when provided.
    returncode : int, optional
        Return code exposed by the fake subprocess result.

    Returns
    -------
    types.SimpleNamespace
        Object compatible with the result of `run_command()`, exposing
        ``stdout``, ``stderr``, and ``returncode`` attributes.
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


def create_fake_font_file(tmp_path: Path, name: str) -> Path:
    """
    Create a deterministic fake font file for discovery or dump tests.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to host the fake file.
    name : str
        Filename to create under the temporary directory.

    Returns
    -------
    pathlib.Path
        Path to the created fake file.
    """
    path = tmp_path / name
    path.write_bytes(b"")
    return path


def simulate_linux_discovery(monkeypatch, paths: list[Path]) -> None:
    """
    Patch Linux discovery to return the provided candidates via fc-list output.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the Fontconfig command wrapper.
    paths : list[pathlib.Path]
        Candidate filesystem paths to expose through the fake discovery output.

    Returns
    -------
    None
    """
    stdout = "\n".join(str(path) for path in paths)
    monkeypatch.setattr(
        "fontshow.platform.font_discovery.run_command",
        lambda _cmd: SimpleNamespace(returncode=0, stdout=stdout),
    )


def simulate_dump_discovery(
    monkeypatch, paths: list[Path], *, skipped_legacy: int
) -> None:
    """
    Patch dump-fonts discovery inputs and last-run discovery stats.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace dump-fonts discovery helpers.
    paths : list[pathlib.Path]
        Discovered font paths to feed into the dump pipeline.
    skipped_legacy : int
        Legacy-extension skip count to expose via discovery stats.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_installed_font_files",
        lambda: paths,
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.get_last_discovery_stats",
        lambda: {"skipped_legacy_extension": skipped_legacy},
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fc_query_extract_many",
        lambda *_args, **_kwargs: {},
    )


def simulate_unloadable_font(monkeypatch, faces: int = 1) -> None:
    """
    Patch fontTools extraction to return structurally unloadable faces.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace fontTools extraction in dump-fonts tests.
    faces : int, optional
        Number of unloadable faces emitted for the same file.

    Returns
    -------
    None
    """

    def fake_fonttools_extract_all(path, **kwargs):
        return [
            {
                "ok": True,
                "container": "TTC",
                "ttc_index": index,
                "tables": ["name"],
            }
            for index in range(faces)
        ]

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
        fake_fonttools_extract_all,
    )


def capture_dump_summary(
    monkeypatch,
) -> tuple[list[str], list[tuple[str, dict | None]]]:
    """
    Capture dump-fonts warning and info messages.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace CLI logging helpers.

    Returns
    -------
    tuple[list[str], list[tuple[str, dict | None]]]
        Captured warning messages and ``(message, extra)`` info records.
    """
    warnings: list[str] = []
    infos: list[tuple[str, dict | None]] = []

    def fake_log_warn(message, **kwargs):
        warnings.append(message)

    def fake_log_info(message, **kwargs):
        infos.append((message, kwargs.get("extra")))

    monkeypatch.setattr("fontshow.cli.dump_fonts.log_warn", fake_log_warn)
    monkeypatch.setattr("fontshow.cli.dump_fonts.log_info", fake_log_info)
    return warnings, infos


def _ok_result(check_id: str):
    """
    Build a minimal successful `CheckResult` for preflight test doubles.

    Parameters
    ----------
    check_id : str
        Identifier assigned to the fake check result.

    Returns
    -------
    CheckResult
        Successful check result with stubbed message text.
    """
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
    """
    Run preflight with environment detection forced to a specific matrix cell.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to patch environment detection and disable
        capability-dependent checks.
    os_name : str
        Operating-system classification to force.
    execution_mode : str
        Execution-mode classification to force.

    Returns
    -------
    PreflightResult
        Result returned by `run_preflight` for the patched environment.

    Notes
    -----
    LuaLaTeX and Fontconfig capability checks are removed so the result
    depends only on environment-support policy.
    """
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
    Invoke a CLI entrypoint and capture normalized exit code plus combined output.

    Parameters
    ----------
    main_func : collections.abc.Callable
        CLI main function, for example `fontshow.__main__.main`.
    argv : list[str]
        Argument vector including the program name.

    Returns
    -------
    tuple[int, str]
        Pair ``(exit_code, stdout)`` capturing normalized CLI semantics
        and stdout output only.

    Raises
    ------
    None
        Unexpected exceptions from the entrypoint are intentionally
        converted into exit code ``2`` instead of being re-raised.

    Notes
    -----
    Stdout and stderr are redirected into separate buffers so tests can
    assert stdout semantics without conflating them with diagnostics
    emitted on stderr.
    """
    old_argv = sys.argv
    sys.argv = argv[:]  # important: copy argv exactly as CLI would receive it

    stdout = StringIO()
    stderr = StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
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
