import importlib
import logging
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Common fixtures
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


@pytest.fixture
def stub_preflight_ok(monkeypatch):
    """
    Stub preflight execution so CLI tests are environment-independent.
    """

    # Fake preflight result object
    class _Result:
        results = []
        overall_severity = type("S", (), {"name": "OK"})()

    # Stub run_preflight
    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda *args, **kwargs: _Result(),
    )

    # Stub rendering
    monkeypatch.setattr(
        "fontshow.__main__.render_preflight_results",
        lambda *args, **kwargs: (0, "Preflight passed.\n"),
    )


@pytest.fixture
def stub_preflight_fail(monkeypatch):
    """
    Stub preflight execution to simulate a FAILED preflight.
    """

    class _Result:
        results = []
        overall_severity = type("S", (), {"name": "ERROR"})()

    monkeypatch.setattr(
        "fontshow.__main__.run_preflight",
        lambda *args, **kwargs: _Result(),
    )

    monkeypatch.setattr(
        "fontshow.__main__.render_preflight_results",
        lambda *args, **kwargs: (1, "Preflight failed.\n"),
    )


@pytest.fixture
def cli_runner():
    """
    Standard CLI runner for Fontshow commands.

    Returns a callable:
        run(args: list[str]) -> (exit_code: int, output: str)
    """
    from fontshow.__main__ import main
    from tests.helpers import run_cli

    def _run(args):
        return run_cli(main, args)

    return _run
