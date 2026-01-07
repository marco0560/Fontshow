import importlib
import logging
from pathlib import Path
from types import SimpleNamespace

import fontshow.dump_fonts


def test_fc_query_extract_emits_basic_logs(enable_fontshow_logging, caplog):
    # reload del consumer dopo aver abilitato il logging
    importlib.reload(fontshow.dump_fonts)

    def fake_run_command(cmd):
        return SimpleNamespace(
            stdout="lang: en\n",
            stderr="",
            returncode=0,
        )

    from pytest import MonkeyPatch

    mp = MonkeyPatch()
    mp.setattr(
        "fontshow.dump_fonts.run_command",
        fake_run_command,
    )

    with caplog.at_level(logging.DEBUG):
        fontshow.dump_fonts.fc_query_extract(Path("/fake/font.ttf"))

    messages = [rec.message for rec in caplog.records]
    assert "fc-query invocation prepared" in messages


def test_fc_query_extract_logs_warning_on_failure(
    enable_fontshow_logging, monkeypatch, caplog
):
    # Reload del modulo consumer dopo aver abilitato il logging
    importlib.reload(fontshow.dump_fonts)

    def fake_run_command(cmd):
        return SimpleNamespace(
            stdout="",
            stderr="fc-query failed",
            returncode=1,
        )

    monkeypatch.setattr(
        "fontshow.dump_fonts.run_command",
        fake_run_command,
    )

    with caplog.at_level(logging.WARNING):
        fontshow.dump_fonts.fc_query_extract(Path("/fake/font.ttf"))

    assert any(
        rec.levelname == "WARNING" and "fc-query execution failed" in rec.message
        for rec in caplog.records
    )
