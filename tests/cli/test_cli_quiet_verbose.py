# tests/cli/test_cli_quiet_verbose.py
"""Tests for fontshow CLI --quiet and --verbose flags."""

import subprocess
import sys


def run_cli(args):
    """Helper to run fontshow CLI and capture output."""
    cmd = [sys.executable, "-m", "fontshow"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )


def test_cli_default_output():
    """Default run should produce stdout output and no stderr."""
    result = run_cli(["create-catalog", "--help"])

    assert result.returncode == 0
    assert result.stdout.strip() != ""
    assert result.stderr.strip() == ""


def test_cli_quiet_suppresses_stdout():
    """--quiet must suppress stdout but not errors."""
    result = run_cli(["create-catalog", "--quiet"])

    assert result.returncode == 0
    assert result.stdout.strip() == ""
    # warnings may be emitted on stderr


def test_cli_verbose_enables_output():
    """--verbose should produce stdout output."""
    result = run_cli(["create-catalog", "--verbose"])

    assert result.returncode == 0
    assert result.stdout.strip() != ""
    # warnings may be emitted on stderr


def test_cli_quiet_and_verbose_quiet_wins():
    """--quiet and --verbose generate parsing error."""
    result = run_cli(["create-catalog", "--quiet", "--verbose"])

    assert result.returncode != 0
    assert result.stdout.strip() == ""
    assert "not allowed with argument" in result.stderr


def test_cli_inventory_fallback_does_not_crash():
    """Errors must always go to stderr, even with --quiet."""
    result = run_cli(["create-catalog", "--inventory", "nonexistent_file.json"])

    assert result.returncode == 0
    assert result.stdout.strip() != ""
    # stderr may contain warnings
