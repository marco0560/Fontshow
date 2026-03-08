"""
Verify TRACE-level logging behavior.

Responsibilities
----------------
- Ensure TRACE-level logging emits additional diagnostics.
- Validate behavior differences between DEBUG and TRACE levels.

Design principles
----------------
Logging tests control the logging configuration so that emitted
messages can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
TRACE-level logging support in the Fontshow logging subsystem.
"""

import importlib
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import fontshow.core.logging_utils
import fontshow.platform.fontconfig as fontconfig
from fontshow.core.logging_utils import TRACE_LEVEL_NUM


@pytest.mark.parametrize(
    "log_level, expect_trace",
    [
        ("DEBUG", False),
        ("TRACE", True),
    ],
)
def test_debug_vs_trace_logging(
    monkeypatch,
    caplog,
    log_level,
    expect_trace,
):
    """
    Verify that:
    - DEBUG level emits DEBUG logs but not TRACE logs
    - TRACE level emits both DEBUG and TRACE logs
    - TRACE logs report the real caller (not logging_utils internals)
    """

    # 1. Enable requested log level BEFORE importing consumers
    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", log_level)

    importlib.reload(fontshow.core.logging_utils)
    importlib.reload(fontconfig)

    # 2. Fake fc-query execution
    def fake_run_command(cmd):
        return SimpleNamespace(
            stdout="lang: en\n",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(
        "fontshow.platform.fontconfig.run_command",
        fake_run_command,
    )

    # 3. Attach caplog handler to non-propagating logger
    logger = logging.getLogger("fontshow")
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.NOTSET)

    try:
        with caplog.at_level(
            TRACE_LEVEL_NUM if log_level == "TRACE" else logging.DEBUG,
            logger="fontshow",
        ):
            fontconfig.fc_query_extract(Path("/fake/font.ttf"))
    finally:
        logger.removeHandler(caplog.handler)

    # 4. Separate records by level
    debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
    trace_records = [r for r in caplog.records if r.levelname == "TRACE"]

    # Sanity: DEBUG must always be present
    assert debug_records, "No DEBUG records emitted"

    if expect_trace:
        assert trace_records, "TRACE records expected but not emitted"

        callers = {(r.module, r.funcName) for r in trace_records}

        # TRACE must originate from the dump_fonts module, but may come
        # from either the public API (fc_query_extract) or a functional
        # helper (_run_fc_query). The important contract is that TRACE
        # reports a real execution layer, not logging_utils internals.
        assert any(
            mod == "fontconfig" and fn in {"fc_query_extract", "_run_fc_query"}
            for mod, fn in callers
        )
    else:
        assert not trace_records, "TRACE records emitted at DEBUG level"


def test_trace_logging_emitted_with_correct_caller(
    monkeypatch,
    caplog,
):
    """
    TRACE logs must be emitted when FONTSHOW_LOG_LEVEL=TRACE
    and must report the *real* caller (not logging_utils internals).
    """

    # 1. Enable TRACE before importing consumers
    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", "TRACE")

    importlib.reload(fontshow.core.logging_utils)
    importlib.reload(fontconfig)

    # 2. Fake fc-query execution
    def fake_run_command(cmd):
        return SimpleNamespace(
            stdout="lang: en\n",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(
        "fontshow.platform.fontconfig.run_command",
        fake_run_command,
    )

    # 3. Attach caplog handler to non-propagating logger
    logger = logging.getLogger("fontshow")
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.NOTSET)

    try:
        with caplog.at_level(logging.NOTSET):
            fontconfig.fc_query_extract(Path("/fake/font.ttf"))
    finally:
        logger.removeHandler(caplog.handler)

    # 4. Extract TRACE records
    trace_records = [rec for rec in caplog.records if rec.levelname == "TRACE"]

    assert trace_records, "No TRACE records emitted"

    messages = [rec.message for rec in trace_records]
    assert "fc-query executed" in messages
    assert "fc-query raw output received" in messages

    callers = {(r.module, r.funcName) for r in trace_records}

    # TRACE must originate from the dump_fonts module, but may come
    # from either the public API (fc_query_extract) or a functional
    # helper (_run_fc_query). The important contract is that TRACE
    # reports a real execution layer, not logging_utils internals.
    assert any(
        mod == "fontconfig" and fn in {"fc_query_extract", "_run_fc_query"}
        for mod, fn in callers
    )
