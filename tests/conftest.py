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
    """
    Ensure that fontshow modules are not cached across test sessions.
    """
    yield
    for name in list(sys.modules):
        if name.startswith("fontshow"):
            del sys.modules[name]


# ---------------------------------------------------------------------------
# Logging control (USED BY MANY NON-CLI TESTS)
# ---------------------------------------------------------------------------


@pytest.fixture
def enable_fontshow_logging(monkeypatch):
    """
    Enable Fontshow structured logging for tests.

    This fixture:
    - sets FONTSHOW_LOG_LEVEL=DEBUG
    - reloads fontshow.logging_utils so the setting is applied

    Notes:
    - Modules that depend on logging_utils and read configuration at import
      time (e.g. dump_fonts, parse_font_inventory) MUST be reloaded explicitly
      by the test after using this fixture.
    """
    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", "DEBUG")

    import fontshow.logging_utils

    importlib.reload(fontshow.logging_utils)


@pytest.fixture
def disable_fontshow_logging():
    """
    Disable all logging temporarily.
    """
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def silence_root_logger():
    """
    Temporarily silence the root logger.
    """
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    yield
    root.handlers[:] = old_handlers


@pytest.fixture
def capture_fontshow_logs(caplog):
    """
    Attach pytest caplog handler to the 'fontshow' logger.

    This is required because fontshow uses:
      - a dedicated logger ('fontshow')
      - propagate = False
      - its own StreamHandler

    The fixture ensures log records are visible to caplog.
    """
    logger = logging.getLogger("fontshow")
    logger.addHandler(caplog.handler)

    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner():
    """
    Run fontshow CLI commands and capture (exit_code, stdout).
    """

    def _run(argv):
        return run_cli(fontshow_main, argv)

    return _run


# ---------------------------------------------------------------------------
# Preflight stubs (CLI-only)
# ---------------------------------------------------------------------------


class _FakeSeverity:
    def __init__(self, name: str):
        self.name = name


class _FakePreflightResult:
    """
    Minimal object matching the real PreflightResult contract:
    - .results → iterable of CheckResult (can be empty)
    - .overall_severity.name → "OK" or "ERROR"
    """

    def __init__(self, ok: bool):
        self.results = []
        self.overall_severity = _FakeSeverity("OK" if ok else "ERROR")


@pytest.fixture
def stub_preflight(monkeypatch, request):
    """
    Parametrized stub for CLI tests.

    Usage:
        @pytest.mark.parametrize("stub_preflight", ["ok"], indirect=True)
        @pytest.mark.parametrize("stub_preflight", ["fail"], indirect=True)

    Behaviour:
      - ok   → preflight succeeds, exit code 0
      - fail → preflight fails, exit code 1
    """
    mode = request.param
    ok = mode == "ok"

    def fake_run_preflight(*args, **kwargs):
        return _FakePreflightResult(ok=ok)

    # IMPORTANT:
    # Patch the symbol as imported by the CLI entrypoint
    monkeypatch.setattr(
        "fontshow.preflight.__main__.run_preflight",
        fake_run_preflight,
    )

    monkeypatch.setattr(
        "fontshow.preflight.__main__.preflight_exit_code",
        lambda result: 0 if ok else 1,
    )


class _FakeDumpFontsResult:
    def __init__(self, ok: bool):
        self.ok = ok


@pytest.fixture
def stub_dump_fonts(monkeypatch, request):
    mode = request.param
    ok = mode == "ok"

    def fake_run_dump_fonts(*args, **kwargs):
        if not ok:
            raise RuntimeError("dump failed")
        return 0

    monkeypatch.setattr(
        "fontshow.dump_fonts._run_dump_fonts",
        fake_run_dump_fonts,
    )


class _FakeParseInventoryResult(dict):
    pass


@pytest.fixture
def stub_parse_inventory(monkeypatch, request):
    mode = request.param
    ok = mode == "ok"

    def fake_parse_inventory(inv, *args, **kwargs):
        if not ok:
            raise ValueError("parse failed")
        return {"schema_version": "1.1", "fonts": []}

    monkeypatch.setattr(
        "fontshow.parse_font_inventory._run_parse_inventory",
        fake_parse_inventory,
    )


@pytest.fixture
def stub_create_catalog(monkeypatch, request):
    mode = request.param
    ok = mode == "ok"

    def fake_create_catalog(*args, **kwargs):
        if not ok:
            raise RuntimeError("catalog failed")

    monkeypatch.setattr(
        "fontshow.create_catalog.run_create_catalog",
        fake_create_catalog,
    )
