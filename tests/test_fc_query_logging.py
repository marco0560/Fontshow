"""
Verify logging behavior during Fontconfig queries.

Responsibilities
----------------
- Ensure fc-query extraction emits expected diagnostic logs.
- Validate integration between Fontconfig querying and the logging
  infrastructure.

Design principles
----------------
Logging tests enable the Fontshow logging system and capture emitted
messages so logging behavior can be validated deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
logging instrumentation for Fontconfig query operations.
"""

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
    """
    Verify that a successful Fontconfig query emits expected debug logs.

    Parameters
    ----------
    enable_fontshow_logging : object
        Fixture that enables the Fontshow logging subsystem for the test.
    capture_fontshow_logs : object
        Fixture used to capture emitted log records from the ``fontshow`` logger.

    Returns
    -------
    None
    """
    # reload consumer after logging is enabled
    importlib.reload(fontconfig)

    def fake_run_command(cmd):
        """
        Emulate a successful `fc-query` subprocess invocation.

        Parameters
        ----------
        cmd : list[str]
            Command arguments passed to the subprocess wrapper.

        Returns
        -------
        types.SimpleNamespace
            Fake completed-process object with successful output.
        """
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
    """
    Verify that a failing Fontconfig query emits a warning log record.

    Parameters
    ----------
    enable_fontshow_logging : object
        Fixture that enables the Fontshow logging subsystem for the test.
    capture_fontshow_logs : object
        Fixture used to capture emitted log records from the ``fontshow`` logger.

    Returns
    -------
    None
    """
    importlib.reload(fontconfig)

    def fake_run_command(cmd):
        """
        Emulate a failing `fc-query` subprocess invocation.

        Parameters
        ----------
        cmd : list[str]
            Command arguments passed to the subprocess wrapper.

        Returns
        -------
        types.SimpleNamespace
            Fake completed-process object with failing status and stderr.
        """
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
