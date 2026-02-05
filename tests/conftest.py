import importlib
import logging
import os
import sys

import pytest

from fontshow.__main__ import main as fontshow_main
from tests.helpers import run_cli

# ---------------------------------------------------------------------------
# Path & import hygiene
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_syspath():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
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
    import fontshow.logging_utils

    importlib.reload(fontshow.logging_utils)


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

    # 🔴 fondamentale
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


class _FakeSeverity:
    def __init__(self, name: str):
        self.name = name


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
    mode = request.param

    def fake_run(_args):
        if mode == "ok":
            return 0
        msg = "parse failed"
        raise ValueError(msg)

    from fontshow import parse_font_inventory

    patch_cli_func(monkeypatch, parse_font_inventory, fake_run)


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

    from fontshow import create_catalog

    monkeypatch.setattr(create_catalog, "main", fake_run)
