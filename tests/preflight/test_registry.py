"""
Verify preflight check registry behavior.

This module tests the registry responsible for managing the set of
available preflight checks.

Responsibilities
----------------
- Ensure checks can be registered and cleared correctly.
- Verify registry lookup and enumeration semantics.

Design principles
-----------------
Registry tests focus on structural integrity of the registration
mechanism without executing check logic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and validates
the integrity of the preflight check registry.
"""

import pytest

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.registry import (
    clear_registry,
    get_registered_checks,
    register_check,
)


class DummyCheckA(BaseCheck):
    """
    Minimal concrete check used to verify registry behavior.

    Notes
    -----
    The check is never meant to execute successfully in these tests;
    only its class identity and registry membership matter.
    """

    executable = False
    check_id = "dummy.a"

    def run(self):
        """
        Fail immediately if executed unexpectedly during a registry test.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Always raised because registry tests must not execute check logic.
        """
        msg = "not executed"
        raise RuntimeError(msg)


class DummyCheckB(BaseCheck):
    """
    Second minimal concrete check used to verify ordering and deduplication.

    Notes
    -----
    This check exists only as a distinct registry entry for structural tests.
    """

    executable = False
    check_id = "dummy.b"

    def run(self):
        """
        Fail immediately if executed unexpectedly during a registry test.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Always raised because registry tests must not execute check logic.
        """
        msg = "not executed"
        raise RuntimeError(msg)


class NotACheck:
    """
    Non-`BaseCheck` sentinel used to verify registry type rejection.

    Notes
    -----
    This class intentionally does not inherit from `BaseCheck`.
    """


def setup_function():
    """
    Reset the preflight registry before each test for isolation.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    # Ensure isolation between tests
    clear_registry()


def test_register_single_check():
    """
    Verify that registering one check yields a one-item registry.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    register_check(DummyCheckA)

    checks = get_registered_checks()

    assert checks == [DummyCheckA]


def test_register_preserves_order():
    """
    Verify that explicit registration order is preserved by the registry.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    register_check(DummyCheckA)
    register_check(DummyCheckB)

    checks = get_registered_checks()

    assert checks == [DummyCheckA, DummyCheckB]


def test_register_is_idempotent():
    """
    Verify that registering the same check twice does not duplicate it.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    register_check(DummyCheckA)
    register_check(DummyCheckA)

    checks = get_registered_checks()

    assert checks == [DummyCheckA]


def test_register_rejects_non_basecheck():
    """
    Verify that non-`BaseCheck` classes are rejected by the registry.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with pytest.raises(TypeError):
        register_check(NotACheck)


def test_clear_registry_resets_state():
    """
    Verify that clearing the registry removes previously registered checks.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    register_check(DummyCheckA)
    clear_registry()

    checks = get_registered_checks()

    assert checks == []
