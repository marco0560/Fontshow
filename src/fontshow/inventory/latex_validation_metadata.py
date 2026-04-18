"""
Helpers for schema v1.4 LaTeX validation metadata.

This module collects deterministic, best-effort metadata about the
local LaTeX toolchain so inventories can record the runtime surface
relevant to future loadability validation work.

Responsibilities
----------------
- Collect version metadata for LuaLaTeX and related packages.
- Build the schema v1.4 ``metadata.validation.lualatex`` structure.
- Avoid hard dependency on a local TeX installation.

Design principles
-----------------
Collection is best-effort and read-only. Missing tools or packages
yield ``None`` values rather than errors so inventory generation
remains environment-independent.

Architectural role
------------------
This module belongs to the **inventory subsystem** and provides schema
metadata used by inventory producers.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.latex.policy import get_render_policy_version

LOADABILITY_PROBE_VERSION = "loadability-probe-v2"


def _read_command_stdout(*argv: str) -> str | None:
    """
    Execute a command and return decoded standard output.

    Parameters
    ----------
    *argv : str
        Command and arguments to execute.

    Returns
    -------
    str | None
        Decoded stdout on success, otherwise ``None``.
    """
    try:
        proc = subprocess.run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    stdout = proc.stdout.strip()
    return stdout or None


def _extract_engine_version(output: str | None) -> str | None:
    """
    Extract a LuaLaTeX engine version from command output.

    Parameters
    ----------
    output : str | None
        Text emitted by ``lualatex --version``.

    Returns
    -------
    str | None
        Parsed engine version when detected, otherwise ``None``.
    """
    if not output:
        return None
    match = re.search(r"Version ([^\s]+)", output)
    if match:
        return match.group(1)
    return output.splitlines()[0].strip() if output.splitlines() else None


def _find_tex_package_path(package_name: str) -> Path | None:
    """
    Locate a TeX package file using ``kpsewhich``.

    Parameters
    ----------
    package_name : str
        Package basename without extension.

    Returns
    -------
    pathlib.Path | None
        Resolved package path when available, otherwise ``None``.
    """
    kpsewhich_bin = shutil.which("kpsewhich")
    if kpsewhich_bin is None:
        return None
    stdout = _read_command_stdout(kpsewhich_bin, f"{package_name}.sty")
    if not stdout:
        return None
    return Path(stdout.splitlines()[0].strip())


def _extract_package_version(package_name: str) -> str | None:
    """
    Extract a TeX package version from a ``.sty`` file header.

    Parameters
    ----------
    package_name : str
        Package basename without extension.

    Returns
    -------
    str | None
        Parsed package version when available, otherwise ``None``.
    """
    package_path = _find_tex_package_path(package_name)
    if package_path is None or not package_path.exists():
        return None
    try:
        text = package_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    match = re.search(
        r"\\Provides(?:Expl)?Package\{[^}]+\}\[[^\]]* v([^\]\s]+)",
        text,
    )
    if match:
        return match.group(1)
    return None


def build_latex_runtime_fingerprint(metadata: dict[str, object]) -> str | None:
    """
    Build a deterministic fingerprint for the LuaLaTeX runtime surface.

    Parameters
    ----------
    metadata : dict[str, object]
        Schema-compatible ``metadata.validation.lualatex`` mapping or a
        partial mapping containing the runtime fields of interest.

    Returns
    -------
    str | None
        Stable SHA-256 fingerprint when enough runtime information is
        available, otherwise ``None``.

    Notes
    -----
    The fingerprint intentionally depends only on stable runtime inputs
    and loadability-probe semantics already recorded in the inventory
    metadata. Probe outcome fields are excluded so a valid runtime can
    be compared before or after probing.
    """
    engine = metadata.get("engine")
    if not isinstance(engine, str) or not engine.strip():
        return None

    components: list[str] = []
    for key in (
        "engine",
        "engine_version",
        "luaotfload_version",
        "fontspec_version",
        "polyglossia_version",
        "render_policy_version",
    ):
        value = metadata.get(key)
        normalized = value.strip() if isinstance(value, str) else ""
        components.append(f"{key}={normalized}")

    payload = "\n".join(components).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def attach_latex_runtime_fingerprint(
    metadata: dict[str, object],
) -> dict[str, object]:
    """
    Return a copy of the metadata block with fingerprint populated.

    Parameters
    ----------
    metadata : dict[str, object]
        Schema-compatible ``metadata.validation.lualatex`` mapping.

    Returns
    -------
    dict[str, object]
        Shallow copy of ``metadata`` with ``runtime_fingerprint`` set to
        the deterministic runtime fingerprint when derivable.
    """
    enriched = dict(metadata)
    enriched["runtime_fingerprint"] = build_latex_runtime_fingerprint(enriched)
    return enriched


def collect_latex_validation_metadata() -> dict[str, object]:
    """
    Collect the schema v1.4 LaTeX validation metadata block.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, object]
        Schema-compatible ``metadata.validation.lualatex`` mapping.

    Notes
    -----
    The returned block records the local LaTeX toolchain surface even
    when no loadability probing has been attempted yet. Probe-specific
    fields remain ``None`` until future loadability work populates them.
    """
    lualatex_bin = shutil.which("lualatex")
    engine = "lualatex" if lualatex_bin is not None else None
    engine_version = _extract_engine_version(
        _read_command_stdout(lualatex_bin, "--version") if lualatex_bin else None
    )
    metadata: dict[str, Any] = {
        "attempted": False,
        "engine": engine,
        "engine_version": engine_version,
        "luaotfload_version": _extract_package_version("luaotfload"),
        "fontspec_version": _extract_package_version("fontspec"),
        "polyglossia_version": _extract_package_version("polyglossia"),
        "runtime_fingerprint": None,
        "render_policy_version": (
            f"{get_render_policy_version()}+{LOADABILITY_PROBE_VERSION}"
        ),
    }
    return attach_latex_runtime_fingerprint(metadata)
