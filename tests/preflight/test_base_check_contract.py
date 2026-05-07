"""
Verify BaseCheck inheritance contract.

This module tests the structural contract required for preflight checks
in the Fontshow validation framework.

Responsibilities
----------------
- Ensure all registered checks inherit from BaseCheck.
- Verify that the preflight check abstraction is respected.

Design principles
-----------------
Contract tests validate structural invariants of the preflight system
without executing full check logic, ensuring deterministic and fast
verification.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and validates
the integrity of the preflight check abstraction used by the
validation subsystem.
"""

from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult


def test_all_checks_are_subclasses_of_basecheck():
    """
    Verify that all registered checks subclass `BaseCheck`.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for check_cls in BaseCheck.registry:
        assert issubclass(check_cls, BaseCheck), (
            f"{check_cls.__name__} does not subclass BaseCheck"
        )


def test_all_checks_define_check_id():
    """
    Verify that every registered check defines a non-empty string ``check_id``.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for check_cls in BaseCheck.registry:
        assert hasattr(check_cls, "check_id"), f"{check_cls.__name__} missing check_id"
        assert isinstance(check_cls.check_id, str), (
            f"{check_cls.__name__}.check_id is not a string"
        )
        assert check_cls.check_id.strip(), f"{check_cls.__name__}.check_id is empty"


def test_check_ids_are_unique():
    """
    Verify that ``check_id`` values are unique across registered checks.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    check_ids = [check_cls.check_id for check_cls in BaseCheck.registry]
    assert len(check_ids) == len(set(check_ids)), (
        f"Duplicate check_id found: {check_ids}"
    )


def test_all_checks_implement_run_method():
    """
    Verify that all registered checks expose a callable `run()` method.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for check_cls in BaseCheck.registry:
        assert hasattr(check_cls, "run"), f"{check_cls.__name__} missing run()"
        assert callable(check_cls.run), f"{check_cls.__name__}.run is not callable"


def test_run_returns_checkresult(monkeypatch):
    """
    Calling run() on each *concrete* check must return a CheckResult instance.

    Environment-dependent behavior is neutralized via monkeypatching.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to stabilize environment-dependent preflight checks.

    Returns
    -------
    None
    """
    try:
        from fontshow.preflight import runner

        monkeypatch.setattr(runner.environment, "detect_os", lambda: "linux")
        monkeypatch.setattr(
            runner.environment, "detect_execution_mode", lambda: "bare-metal"
        )
    except Exception:  # noqa: BLE001,S110
        # (intentional: defensive test plumbing must not fail contract tests)
        pass

    for check_cls in BaseCheck.registry:
        # Skip non-executable (sentinel / test-only) checks
        if not getattr(check_cls, "executable", True):
            continue

        check = check_cls()
        result = check.run()
        assert isinstance(result, CheckResult), (
            f"{check_cls.__name__}.run() did not return CheckResult"
        )
