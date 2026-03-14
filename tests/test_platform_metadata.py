"""
Verify platform metadata detection edge cases.

Responsibilities
----------------
- Ensure execution-context detection handles WSL, container, and native cases.
- Verify metadata collection falls back to ``"unknown"`` for empty providers.
- Keep platform metadata tests deterministic through monkeypatching.
"""

from __future__ import annotations

from pathlib import Path

from fontshow.core.types import ExecutionContext
from fontshow.inventory import platform_metadata


def test_detect_execution_context_prefers_wsl_environment(monkeypatch):
    """
    Ensure WSL environment variables take precedence over filesystem probes.
    """
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

    assert platform_metadata._detect_execution_context() is ExecutionContext.WSL


def test_detect_execution_context_falls_back_to_container_on_proc_read_error(
    monkeypatch,
):
    """
    Ensure container detection still works when ``/proc/version`` cannot be read.
    """
    real_path = Path

    class FakePath:
        def __init__(self, value: str):
            self._path = value

        def exists(self) -> bool:
            return self._path in {"/proc/version", "/.dockerenv"}

        def read_text(self) -> str:
            if self._path == "/proc/version":
                msg = "simulated read failure"
                raise OSError(msg)
            return ""

    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.setattr(platform_metadata, "Path", FakePath)

    try:
        assert (
            platform_metadata._detect_execution_context() is ExecutionContext.CONTAINER
        )
    finally:
        monkeypatch.setattr(platform_metadata, "Path", real_path)


def test_detect_execution_context_returns_native_without_markers(monkeypatch):
    """
    Ensure native execution is reported when no WSL or container markers exist.
    """

    class FakePath:
        def __init__(self, _value: str):
            pass

        def exists(self) -> bool:
            return False

        def read_text(self) -> str:
            return ""

    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.setattr(platform_metadata, "Path", FakePath)

    assert platform_metadata._detect_execution_context() is ExecutionContext.NATIVE


def test_collect_platform_metadata_uses_unknown_for_empty_runtime_fields(monkeypatch):
    """
    Ensure empty platform providers are normalized to ``"unknown"`` fields.
    """
    monkeypatch.setattr(
        platform_metadata, "_detect_execution_context", lambda: ExecutionContext.OTHER
    )
    monkeypatch.setattr(platform_metadata.platform, "system", lambda: "")
    monkeypatch.setattr(platform_metadata.platform, "release", lambda: "")
    monkeypatch.setattr(platform_metadata.platform, "version", lambda: "")
    monkeypatch.setattr(platform_metadata.platform, "machine", lambda: "")
    monkeypatch.setattr(platform_metadata.platform, "python_version", lambda: "")
    monkeypatch.setattr(platform_metadata.platform, "platform", lambda: "fake-platform")
    monkeypatch.setattr(platform_metadata.socket, "gethostname", lambda: "")
    monkeypatch.setattr(platform_metadata.getpass, "getuser", lambda: "tester")

    metadata = platform_metadata.collect_platform_metadata()

    assert metadata["os"] == "unknown"
    assert metadata["os_release"] == "unknown"
    assert metadata["kernel"] == "unknown"
    assert metadata["machine"] == "unknown"
    assert metadata["python_version"] == "unknown"
    assert metadata["hostname"] == "unknown"
    assert metadata["execution_context"] == "other"
    assert metadata["platform"] == "fake-platform"
    assert metadata["username"] == "tester"
