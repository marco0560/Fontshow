from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult
from fontshow.preflight.runner import CHECKS


def test_all_checks_are_subclasses_of_basecheck():
    """
    All checks registered in CHECKS must subclass BaseCheck.
    """
    for check_cls in CHECKS:
        assert issubclass(
            check_cls, BaseCheck
        ), f"{check_cls.__name__} does not subclass BaseCheck"


def test_all_checks_define_check_id():
    """
    Each check must define a non-empty string check_id.
    """
    for check_cls in CHECKS:
        assert hasattr(check_cls, "check_id"), f"{check_cls.__name__} missing check_id"
        assert isinstance(
            check_cls.check_id, str
        ), f"{check_cls.__name__}.check_id is not a string"
        assert check_cls.check_id.strip(), f"{check_cls.__name__}.check_id is empty"


def test_check_ids_are_unique():
    """
    check_id values must be unique across all registered checks.
    """
    check_ids = [check_cls.check_id for check_cls in CHECKS]
    assert len(check_ids) == len(
        set(check_ids)
    ), f"Duplicate check_id found: {check_ids}"


def test_all_checks_implement_run_method():
    """
    All checks must implement a run() method.
    """
    for check_cls in CHECKS:
        assert hasattr(check_cls, "run"), f"{check_cls.__name__} missing run()"
        assert callable(
            getattr(check_cls, "run")
        ), f"{check_cls.__name__}.run is not callable"


def test_run_returns_checkresult(monkeypatch):
    """
    Calling run() on each check must return a CheckResult instance.

    Environment-dependent behavior is neutralized via monkeypatching.
    """
    # Neutralize environment detection for safety
    try:
        from fontshow.preflight import runner

        monkeypatch.setattr(runner.environment, "detect_os", lambda: "linux")
        monkeypatch.setattr(
            runner.environment, "detect_execution_mode", lambda: "bare-metal"
        )
    except Exception:
        # Defensive: test should not fail due to environment plumbing
        pass

    for check_cls in CHECKS:
        check = check_cls()
        result = check.run()
        assert isinstance(
            result, CheckResult
        ), f"{check_cls.__name__}.run() did not return CheckResult"
