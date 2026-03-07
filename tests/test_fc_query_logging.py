import importlib
import logging
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch

import fontshow.platform.fontconfig as fontconfig


def test_fc_query_extract_emits_basic_logs(
    enable_fontshow_logging,
    capture_fontshow_logs,
):
    # reload consumer after logging is enabled
    importlib.reload(fontconfig)

    def fake_run_command(cmd):
        return SimpleNamespace(
            stdout="lang: en\n",
            stderr="",
            returncode=0,
        )

    mp = MonkeyPatch()
    mp.setattr(
        "fontshow.platform.fontconfig.run_command",
        fake_run_command,
    )

    with capture_fontshow_logs.at_level(logging.DEBUG, logger="fontshow"):
        fontconfig.fc_query_extract(Path("/fake/font.ttf"))

    messages = [rec.getMessage() for rec in capture_fontshow_logs.records]

    assert "fc-query invocation prepared" in messages
    assert "fontconfig output parsed" in messages


def test_fc_query_extract_logs_warning_on_failure(
    enable_fontshow_logging,
    capture_fontshow_logs,
):
    importlib.reload(fontconfig)

    def fake_run_command(cmd):
        return SimpleNamespace(
            stdout="",
            stderr="fc-query failed",
            returncode=1,
        )

    mp = MonkeyPatch()
    mp.setattr(
        "fontshow.platform.fontconfig.run_command",
        fake_run_command,
    )

    with capture_fontshow_logs.at_level(logging.WARNING, logger="fontshow"):
        fontconfig.fc_query_extract(Path("/fake/font.ttf"))

    assert any(
        rec.levelname == "WARNING" and "fc-query execution failed" in rec.message
        for rec in capture_fontshow_logs.records
    )
