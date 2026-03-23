"""
Preflight check registry.

This module implements the internal registry used to store and retrieve
preflight check classes.

Responsibilities
----------------
- Register preflight check implementations.
- Provide access to the ordered list of registered checks.
- Support deterministic check execution order.

Design principles
-----------------
The registry is intentionally simple and deterministic. Check classes
are registered explicitly and the registration order is preserved to
ensure stable execution behaviour.

Architectural role
------------------
This module belongs to the **preflight subsystem** and provides the
registration mechanism used by the preflight runner.
"""

from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck

# Internal registry for preflight checks.
# This is intentionally explicit and deterministic.
_CHECK_REGISTRY: list[type[BaseCheck]] = []


def register_check(check_cls: type[BaseCheck]) -> None:
    """
    Register a preflight check class.

    Parameters
    ----------
    check_cls : type[BaseCheck]
        Check class to register.

    Returns
    -------
    None

    Raises
    ------
    TypeError
        If `check_cls` is not a subclass of `BaseCheck`.

    Notes
    -----
    Registration order is preserved and duplicate registrations are
    ignored.
    """
    # The type check is performed at runtime to ensure that only valid check classes are registered.
    if not issubclass(check_cls, BaseCheck):
        msg = f"Cannot register {check_cls!r}: not a subclass of BaseCheck"  # type: ignore[unreachable]
        raise TypeError(msg)

    if check_cls not in _CHECK_REGISTRY:
        _CHECK_REGISTRY.append(check_cls)


def get_registered_checks() -> list[type[BaseCheck]]:
    """
    Return the list of registered preflight check classes.

    Parameters
    ----------
    None

    Returns
    -------
    list[type[BaseCheck]]
        Shallow copy of the registered check classes.

    Notes
    -----
    A shallow copy is returned to prevent external mutation.
    """
    return list(_CHECK_REGISTRY)


def clear_registry() -> None:
    """
    Clear the registry.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    This function is intended for test isolation only.
    Production code is expected to register checks during import-time
    initialization rather than mutating the registry repeatedly.
    """
    _CHECK_REGISTRY.clear()
