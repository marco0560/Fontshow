"""
Pytest configuration and shared fixtures for Fontshow tests.

Responsibilities
----------------
- Provide global pytest fixtures used across the test suite.
- Configure import paths and runtime environment for tests.
- Offer shared helpers for invoking the Fontshow CLI in tests.

Design principles
-----------------
Test infrastructure must remain deterministic and isolated from the
developer environment. Fixtures here centralize setup logic so tests
remain concise and reproducible.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and provides
shared pytest configuration and fixtures for the Fontshow test suite.
"""

import importlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from fontshow.__main__ import main as fontshow_main
from tests.helpers import run_cli

# ---------------------------------------------------------------------------
# Path & import hygiene
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_syspath():
    root = (Path(__file__).parent / "..").resolve()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root)


@pytest.fixture(scope="session", autouse=True)
def ensure_fontshow_import_is_clean():
    yield
    for name in list(sys.modules):
        if name.startswith("fontshow"):
            del sys.modules[name]


# ---------------------------------------------------------------------------
# Logging control
# ---------------------------------------------------------------------------


@pytest.fixture
def enable_fontshow_logging(monkeypatch):
    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", "DEBUG")
    import fontshow.core.logging_utils

    importlib.reload(fontshow.core.logging_utils)


@pytest.fixture
def disable_fontshow_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def silence_root_logger():
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    yield
    root.handlers[:] = old_handlers


@pytest.fixture
def capture_fontshow_logs(caplog):
    logger = logging.getLogger("fontshow")

    # 🔴 mandatory
    old_propagate = logger.propagate
    logger.propagate = True

    with caplog.at_level(logging.DEBUG):
        yield caplog

    logger.propagate = old_propagate


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner():
    def _run(argv):
        return run_cli(fontshow_main, argv)

    return _run


# ---------------------------------------------------------------------------
# Helper: patch argparse dispatch
# ---------------------------------------------------------------------------


def patch_cli_func(monkeypatch, module, fake_func):
    """
    Patch the command entrypoint AFTER argparse parsing.
    """
    monkeypatch.setattr(module, "main", fake_func)


# ---------------------------------------------------------------------------
# PRE-FLIGHT
# ---------------------------------------------------------------------------


@dataclass
class _FakeSeverity:
    name: str


class _FakePreflightResult:
    def __init__(self, ok: bool):
        self.results = []
        self.overall_severity = _FakeSeverity("OK" if ok else "ERROR")


@pytest.fixture
def stub_preflight(monkeypatch, request):
    # Default behavior if fixture is not parametrized
    mode = getattr(request, "param", "ok")
    ok = mode == "ok"

    def fake_run(args):
        if ok:
            print("Preflight passed.")
            return 0
        print("Preflight failed.")
        return 1

    import fontshow.preflight

    # Patch the actual function used by argparse
    monkeypatch.setattr(
        fontshow.preflight,
        "run",
        fake_run,
        raising=False,  # attribute may not exist yet
    )


# ---------------------------------------------------------------------------
# DUMP FONTS
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_dump_fonts(monkeypatch, request):
    mode = request.param

    def fake_run(_args):
        if mode == "ok":
            return 0
        msg = "dump failed"
        raise RuntimeError(msg)

    from fontshow import dump_fonts

    patch_cli_func(monkeypatch, dump_fonts, fake_run)


# ---------------------------------------------------------------------------
# PARSE INVENTORY
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_parse_inventory(monkeypatch, request):
    import copy

    import fontshow.cli.parse_inventory as mod

    mode = request.param

    def fake_parse_inventory(data, *_args, **_kwargs):
        if mode == "fail":
            msg = "parse failed"
            raise ValueError(msg)

        if mode == "boom":
            msg = "internal error"
            raise RuntimeError(msg)

        # ok
        return copy.deepcopy(data)

    original_runner = mod.run_parse_font_inventory

    def patched_runner(args, **kwargs):
        return original_runner(
            args,
            parse_inventory_fn=fake_parse_inventory,
            **kwargs,
        )

    monkeypatch.setattr(mod, "run_parse_font_inventory", patched_runner)


# ---------------------------------------------------------------------------
# CREATE CATALOG
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_create_catalog(monkeypatch, request):
    mode = request.param

    def fake_run(args):
        if mode == "ok":
            return 0
        if mode == "fail":
            return 1
        if mode == "boom":
            raise RuntimeError(mode)
        return 2  # explicit fallback (non-None exit code)

    from fontshow import create_catalog

    monkeypatch.setattr(create_catalog, "main", fake_run)


# ---------------------------------------------------------------------------
# Clean verbosity state between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_cli_state():
    from fontshow.core.cli_utils import set_cli_mode

    set_cli_mode(False, False)
