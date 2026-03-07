"""
Platform runtime detection helpers.

This module provides small utilities and constants that describe the
current execution platform. These values are computed at import time and
used by various subsystems to adapt behaviour when platform-specific
differences matter (for example filesystem handling or LaTeX invocation).

Responsibilities
----------------
- Detect the current operating system.
- Provide simple boolean flags for common platform checks.
- Centralize runtime platform knowledge so other modules do not perform
  ad-hoc platform detection.

Design principles
-----------------
Platform detection must live in a dedicated infrastructure module so
that domain and rendering modules (catalog, inventory, latex, etc.)
never depend on pipeline scripts or CLI entrypoints. This keeps the
dependency graph clean and prevents circular imports.

Architectural role
------------------
This module belongs to the **platform infrastructure layer** and may be
imported by any other module in the project that requires knowledge of
the runtime environment.
"""

import sys

from fontshow.inventory.platform_metadata import collect_platform_metadata

if sys.platform == "win32":
    # modulo specifico Windows
    IS_WINDOWS = True
    IS_LINUX = False
elif sys.platform.startswith("linux"):
    IS_LINUX = True
    IS_WINDOWS = False
    # eventuale alternativa per altri OS
else:
    IS_WINDOWS = False
    IS_LINUX = False


def _inventory_platform_mismatch(inv_env: dict, runtime: dict) -> list[str]:
    """
    Compare inventory and runtime platform metadata and report mismatches.

    Parameters
    ----------
    inv_env : dict
        Inventory run-environment metadata.
    runtime : dict
        Runtime platform metadata collected from the current system.

    Returns
    -------
    list[str]
        List of metadata keys that differ between inventory and runtime.
        Empty if no mismatch is detected.
    """

    def _norm(v: object) -> str:
        """
        Normalize a value for platform metadata comparison.

        Parameters
        ----------
        v : object
            Value to normalize.

        Returns
        -------
        str
            Lowercased and stripped string representation of the value.
        """
        return str(v).strip().lower()

    mismatches: list[str] = []

    for key in ("os", "machine"):
        if _norm(inv_env.get(key)) != _norm(runtime.get(key)):
            mismatches.append(key)

    inv_ctx = inv_env.get("execution_context")
    run_ctx = runtime.get("execution_context")

    if _norm(inv_ctx) != _norm(run_ctx):
        mismatches.append("execution_context")

    return mismatches


def _enforce_platform(inv_env: dict) -> tuple[bool, list[str]]:
    """
    Enforce inventory/platform compatibility.

    Parameters
    ----------
    inv_env : dict
        Inventory run-environment metadata.

    Returns
    -------
    tuple[bool, list[str]]
        A pair (ok, mismatches):
        - ok is True if inventory matches runtime platform.
        - mismatches contains the differing metadata keys.
    """
    runtime = collect_platform_metadata()
    mismatches = _inventory_platform_mismatch(inv_env, runtime)
    return (not mismatches), mismatches
