from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck

# Internal registry for preflight checks.
# This is intentionally explicit and deterministic.
_CHECK_REGISTRY: list[type[BaseCheck]] = []


def register_check(check_cls: type[BaseCheck]) -> None:
    """
    Register a preflight check class.

    The class must be a subclass of BaseCheck.
    Registration order is preserved.
    """
    if not issubclass(check_cls, BaseCheck):
        msg = f"Cannot register {check_cls!r}: not a subclass of BaseCheck"
        raise TypeError(msg)

    if check_cls not in _CHECK_REGISTRY:
        _CHECK_REGISTRY.append(check_cls)


def get_registered_checks() -> list[type[BaseCheck]]:
    """
    Return the list of registered preflight check classes.

    A shallow copy is returned to prevent external mutation.
    """
    return list(_CHECK_REGISTRY)


def clear_registry() -> None:
    """
    Clear the registry.

    This function is intended for test isolation only.
    """
    _CHECK_REGISTRY.clear()
