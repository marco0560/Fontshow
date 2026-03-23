"""
Inventory utility helpers.

This module provides lightweight helper functions used during inventory
generation and metadata extraction.

Responsibilities
----------------
- Provide deterministic helpers used during inventory construction.
- Implement subprocess wrappers for external tool execution.
- Generate stable identifiers for font entries.
- Provide cache keys and other small utilities used by the inventory
  pipeline.

Design principles
-----------------
Utilities in this module must remain lightweight and independent from
pipeline orchestration. They are safe to import across inventory,
catalog, and CLI layers.

Architectural role
------------------
This module belongs to the **inventory subsystem** and provides shared
helper functions used during inventory generation.
"""

import hashlib
import subprocess
from pathlib import Path

from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.core.cli_utils import log_err


def run_command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Execute a subprocess command and capture combined stdout/stderr.

    Parameters
    ----------
    argv : list[str]
        Argument vector to pass to subprocess.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process object with stdout captured as text and
        stderr redirected to stdout. The process is not checked for
        non-zero exit status.

    Raises
    ------
    RuntimeError
        If the subprocess exceeds `SUBPROCESS_TIMEOUT_SECONDS` and is
        converted from `subprocess.TimeoutExpired` into a deterministic
        inventory-layer failure.

    Notes
    -----
    This helper does not raise on non-zero exit status; callers must
    inspect ``returncode`` explicitly.
    """
    try:
        return subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        log_err(
            f"fontconfig subprocess timed out "
            f"(timeout={SUBPROCESS_TIMEOUT_SECONDS}s, argv={argv})"
        )
        msg = "fontconfig subprocess timed out"
        raise RuntimeError(msg) from exc


def make_font_id(path: str, ttc_index: int | None) -> str:
    """
    Build a stable, reproducible identifier for a font face.

    Parameters
    ----------
    path : str
        Filesystem path to the font file.
    ttc_index : int | None
        Face index for TrueType Collections, or None for single-face fonts.

    Returns
    -------
    str
        Short hexadecimal identifier derived from path and TTC index.

    Notes
    -----
    Intended for comparison, caching, and debugging purposes.
    """
    key = f"{path}|{ttc_index if ttc_index is not None else 'single'}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


# -----------------------
# Cache
# -----------------------


def font_cache_key(path: Path, ttc_index: int | None = None) -> str:
    """
    Return a stable cache key for a font face.

    Parameters
    ----------
    path : pathlib.Path
        Path to the font file.
    ttc_index : int | None, optional
        Face index for TrueType Collections (None for single-face fonts).

    Returns
    -------
    str
        SHA-256 hexadecimal digest suitable for use as a cache filename.

    Notes
    -----
    The key combines:
    - absolute file path,
    - file modification time (nanoseconds),
    - file size,
    - optional TTC face index.

    Ensures cache invalidation when the font file changes.

    Raises
    ------
    OSError
        Propagates filesystem errors raised while statting or resolving
        the target path.
    """
    st = path.stat()
    idx = "" if ttc_index is None else f"|ttc:{ttc_index}"
    key = f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}{idx}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
