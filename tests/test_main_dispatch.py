"""
Exercise top-level CLI dispatch edge cases.

Responsibilities
----------------
- Verify dispatch normalization for ``None`` and ``SystemExit`` results.
- Ensure unexpected exceptions become exit code 2.
"""

from __future__ import annotations

from types import SimpleNamespace

import fontshow.__main__ as mainmod


def test_dispatch_command_normalizes_none_and_system_exit(monkeypatch):
    """
    Ensure command handlers returning ``None`` or raising ``SystemExit`` map correctly.
    """
    trace: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mainmod,
        "log_trace_cat",
        lambda _log, _cat, msg, extra: trace.append((msg, extra)),
    )

    args = SimpleNamespace(command="demo", func=lambda _args: None)
    assert mainmod.dispatch_command(args) == 0
    assert trace[-1] == ("cli dispatch completed", {"exit_code": 0})

    def _exit_none(_args):
        raise SystemExit

    args.func = _exit_none
    assert mainmod.dispatch_command(args) == 0
    assert trace[-1] == ("cli dispatch completed", {"exit_code": 0})

    def _exit_code(_args):
        raise SystemExit(7)

    args.func = _exit_code
    assert mainmod.dispatch_command(args) == 7
    assert trace[-1] == ("cli dispatch completed", {"exit_code": 7})


def test_dispatch_command_converts_unhandled_exception_to_exit_code_2(monkeypatch):
    """
    Ensure unexpected command crashes are normalized to exit code 2.
    """
    trace: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mainmod,
        "log_trace_cat",
        lambda _log, _cat, msg, extra: trace.append((msg, extra)),
    )

    def _boom(_args):
        msg = "boom"
        raise RuntimeError(msg)

    args = SimpleNamespace(command="demo", func=_boom)

    assert mainmod.dispatch_command(args) == 2
    assert trace[-1] == ("cli dispatch crashed", {})
