"""
Platform metadata extraction helpers.

This module collects runtime platform metadata used to describe the
environment in which a Fontshow inventory was generated.

Responsibilities
----------------
- Detect the execution environment (native, container, WSL).
- Collect operating system and kernel information.
- Capture host and runtime metadata such as hostname and Python version.
- Produce schema-compatible metadata structures.

Design principles
-----------------
Platform metadata must be gathered in a deterministic and portable
manner using only standard library facilities. The module acts as the
single source of truth for runtime metadata across inventory generation
and downstream pipeline stages.

Architectural role
------------------
This module belongs to the **inventory subsystem** and provides runtime
environment metadata included in Fontshow inventories.
"""

from __future__ import annotations

import getpass
import os
import platform
import socket
from pathlib import Path
from typing import Any

from fontshow.core.types import ExecutionContext


def _detect_execution_context() -> ExecutionContext:
    """
    Detect the current runtime execution context.

    Parameters
    ----------
    None

    Returns
    -------
    ExecutionContext
        Detected runtime context such as native, WSL, or container.

    Notes
    -----
    Detection is best-effort and relies on environment variables,
    `/proc/version`, and container marker files.
    """
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

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, Any]
        Schema-compatible runtime metadata describing operating system,
        Python runtime, host identity, and execution context.

    Notes
    -----
    This function is the SINGLE SOURCE OF TRUTH for runtime platform
    metadata across dump → parse → create_catalog.
    Output structure MUST remain schema-compatible (schema 1.2).

    The returned mapping contains both schema-required fields and a
    small set of additional informational fields allowed by the schema.
    """

    ctx = _detect_execution_context()

    os_name = platform.system() or "unknown"
    os_release = platform.release() or "unknown"
    kernel = platform.version() or "unknown"
    machine = platform.machine() or "unknown"
    python_version = platform.python_version() or "unknown"
    hostname = socket.gethostname() or "unknown"

    return {
        # ---- Required by schema ----
        "os": os_name,
        "os_release": os_release,
        "kernel": kernel,
        "machine": machine,
        "python_version": python_version,
        "hostname": hostname,
        "execution_context": ctx.to_json(),  # MUST be string per schema
        # ---- Allowed additional fields (schema allows additionalProperties) ----
        "platform": platform.platform(),
        "username": getpass.getuser(),
    }
