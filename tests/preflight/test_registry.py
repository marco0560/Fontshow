import pytest

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.registry import (
    clear_registry,
    get_registered_checks,
    register_check,
)


class DummyCheckA(BaseCheck):
    executable = False
    check_id = "dummy.a"

    def run(self):
        raise RuntimeError("not executed")


class DummyCheckB(BaseCheck):
    executable = False
    check_id = "dummy.b"

    def run(self):
        raise RuntimeError("not executed")


class NotACheck:
    pass


def setup_function():
    # Ensure isolation between tests
    clear_registry()


def test_register_single_check():
    register_check(DummyCheckA)

    checks = get_registered_checks()

    assert checks == [DummyCheckA]


def test_register_preserves_order():
    register_check(DummyCheckA)
    register_check(DummyCheckB)

    checks = get_registered_checks()

    assert checks == [DummyCheckA, DummyCheckB]


def test_register_is_idempotent():
    register_check(DummyCheckA)
    register_check(DummyCheckA)

    checks = get_registered_checks()

    assert checks == [DummyCheckA]


def test_register_rejects_non_basecheck():
    with pytest.raises(TypeError):
        register_check(NotACheck)


def test_clear_registry_resets_state():
    register_check(DummyCheckA)
    clear_registry()

    checks = get_registered_checks()

    assert checks == []
