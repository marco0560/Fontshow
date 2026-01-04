# tests/preflight/test_check_contract.py

from __future__ import annotations

import inspect

import pytest

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult
from fontshow.preflight.runner import CHECKS


@pytest.mark.parametrize("check_cls", CHECKS)
def test_preflight_checks_respect_contract(check_cls: type[BaseCheck]) -> None:
    # 1) Must inherit from BaseCheck
    assert issubclass(
        check_cls, BaseCheck
    ), f"{check_cls.__name__} must inherit from BaseCheck"

    # 2) Must expose a non-empty check_id at class level (preferred)
    check_id = getattr(check_cls, "check_id", None)
    assert isinstance(check_id, str) and check_id.strip(), (
        f"{check_cls.__name__} must define a non-empty class attribute "
        f"check_id (got: {check_id!r})"
    )

    # 3) Must have run(self) method with no required positional args beyond self
    run = getattr(check_cls, "run", None)
    assert callable(run), f"{check_cls.__name__} must define a run() method"

    sig = inspect.signature(check_cls.run)
    params = list(sig.parameters.values())

    # Expect at least 'self'
    assert params, f"{check_cls.__name__}.run() must accept 'self'"

    # No extra required params beyond self
    required_beyond_self = [
        p
        for p in params[1:]
        if p.default is inspect._empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    assert not required_beyond_self, (
        f"{check_cls.__name__}.run() must not require extra args; "
        f"required params: {[p.name for p in required_beyond_self]}"
    )

    # 4) Instantiable without args, and returns a CheckResult
    check = check_cls()
    result = check.run()
    assert isinstance(
        result, CheckResult
    ), f"{check_cls.__name__}.run() must return CheckResult (got: {type(result).__name__})"
