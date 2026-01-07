import importlib
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
