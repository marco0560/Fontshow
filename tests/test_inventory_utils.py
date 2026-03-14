"""
Exercise inventory utility edge cases.

Responsibilities
----------------
- Verify subprocess timeout normalization.
- Pin command-not-found behavior and cache-key failure propagation.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fontshow.inventory import utils


def test_run_command_converts_timeout_to_runtime_error(monkeypatch):
    """
    Ensure subprocess timeouts are logged and normalized.
    """
    errors: list[str] = []

    def _timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["fc-query"], timeout=1)

    monkeypatch.setattr(utils.subprocess, "run", _timeout)
    monkeypatch.setattr(utils, "log_err", errors.append)

    with pytest.raises(RuntimeError, match="fontconfig subprocess timed out"):
        utils.run_command(["fc-query", "/tmp/font.ttf"])

    assert errors == [
        f"fontconfig subprocess timed out (timeout={utils.SUBPROCESS_TIMEOUT_SECONDS}s, argv=['fc-query', '/tmp/font.ttf'])"
    ]


def test_run_command_propagates_command_not_found(monkeypatch):
    """
    Ensure missing executables are not silently converted.
    """
    monkeypatch.setattr(
        utils.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )

    with pytest.raises(FileNotFoundError, match="missing"):
        utils.run_command(["fc-query"])


def test_font_cache_key_propagates_stat_failures(monkeypatch, tmp_path):
    """
    Ensure cache-key generation preserves filesystem failures.
    """
    path = tmp_path / "font.ttf"
    path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        Path,
        "stat",
        lambda self: (_ for _ in ()).throw(OSError("stat failed")),
    )

    with pytest.raises(OSError, match="stat failed"):
        utils.font_cache_key(path)
