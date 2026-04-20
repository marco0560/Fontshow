"""Verify the opt-in benchmark workflow wiring."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "scripts" / "setup_benchmark_fonts.sh"
BENCHMARK_SCRIPT = REPO_ROOT / "scripts" / "benchmark.sh"
LOADABILITY_BENCHMARK_SCRIPT = (
    REPO_ROOT / "scripts" / "benchmark_loadability_batches.sh"
)
LOADABILITY_REPLAY_SCRIPT = REPO_ROOT / "scripts" / "run_loadability_probe.py"
FONT_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "fonts_dir"
READINESS_ENV = "FONTSHOW_BENCHMARK_READINESS"
SETUP_COMMAND = "scripts/setup_benchmark_fonts.sh light"


def _skip_unless_readiness_enabled() -> None:
    """
    Skip optional readiness checks unless explicitly requested.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    if os.environ.get(READINESS_ENV) != "1":
        pytest.skip(f"set {READINESS_ENV}=1 to run benchmark readiness checks")


def test_benchmark_scripts_expose_help_without_external_tools() -> None:
    """
    Ensure benchmark scripts can be inspected without Hyperfine or fonts.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for script in (SETUP_SCRIPT, BENCHMARK_SCRIPT, LOADABILITY_BENCHMARK_SCRIPT):
        result = subprocess.run(
            ["bash", str(script), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout

    replay_result = subprocess.run(
        [sys.executable, str(LOADABILITY_REPLAY_SCRIPT), "--help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert replay_result.returncode == 0
    assert "Replay LuaLaTeX loadability probing" in replay_result.stdout


def test_hyperfine_readiness_check_is_opt_in() -> None:
    """
    Verify Hyperfine availability only for explicit benchmark readiness runs.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    _skip_unless_readiness_enabled()

    assert shutil.which("hyperfine") is not None


def test_benchmark_font_fixture_readiness_is_opt_in() -> None:
    """
    Verify generated benchmark fonts only for explicit readiness runs.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    _skip_unless_readiness_enabled()

    assert FONT_FIXTURE_DIR.is_dir(), (
        f"benchmark font fixture directory is missing: {FONT_FIXTURE_DIR}; "
        f"run `{SETUP_COMMAND}` first"
    )
    assert any(FONT_FIXTURE_DIR.rglob("*.ttf")), (
        f"benchmark font fixture directory contains no .ttf files: "
        f"{FONT_FIXTURE_DIR}; run `{SETUP_COMMAND}` first"
    )
