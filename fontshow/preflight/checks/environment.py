import os
import platform
from typing import Literal

OSName = Literal["linux", "windows", "macos", "unknown"]

ExecutionMode = Literal[
    "ci",
    "wsl",
    "container",
    "bare-metal",
]


def detect_os() -> OSName:
    """
    Detect the operating system in a normalized form.

    Returns:
        "linux", "windows", "macos", or "unknown"
    """
    system = platform.system().lower()

    if system == "linux":
        return "linux"
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"

    return "unknown"  # fallback for unsupported or unrecognized systems


def is_ci() -> bool:
    """
    Detect whether the code is running in a CI environment.
    """
    return os.environ.get("GITHUB_ACTIONS") == "true"


def is_wsl() -> bool:
    """
    Detect Windows Subsystem for Linux (WSL).
    """
    if platform.system().lower() != "linux":
        return False

    try:
        with open("/proc/version", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def is_container() -> bool:
    """
    Best-effort detection of containerized execution.
    """
    if os.path.exists("/.dockerenv"):
        return True

    try:
        with open("/proc/1/cgroup", encoding="utf-8") as f:
            return any("docker" in line or "container" in line for line in f)
    except OSError:
        return False


def detect_execution_mode() -> ExecutionMode:
    """
    Detect the execution mode of the current environment.
    """
    if is_ci():
        return "ci"
    if is_wsl():
        return "wsl"
    if is_container():
        return "container"
    return "bare-metal"
