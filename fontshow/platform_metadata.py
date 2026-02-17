from __future__ import annotations

import getpass
import os
import platform
import socket
from pathlib import Path
from typing import Any

from fontshow.types import ExecutionContext


def _detect_execution_context() -> ExecutionContext:
    # WSL detection
    if "WSL_DISTRO_NAME" in os.environ:
        return ExecutionContext.WSL

    proc_version = Path("/proc/version")
    if proc_version.exists():
        try:
            if "microsoft" in proc_version.read_text().lower():
                return ExecutionContext.WSL
        except OSError:
            pass

    # Container detection
    if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
        return ExecutionContext.CONTAINER

    return ExecutionContext.NATIVE


def collect_platform_metadata() -> dict[str, Any]:
    """
    Canonical platform metadata extractor.

    This function is the SINGLE SOURCE OF TRUTH for runtime platform
    metadata across dump → parse → create_catalog.

    Output structure MUST remain schema-compatible.
    """

    ctx = _detect_execution_context()

    return {
        "os": platform.system(),
        "kernel": platform.release(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "execution_context": {
            "type": ctx.to_json(),
        },
    }
