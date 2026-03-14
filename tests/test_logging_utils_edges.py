"""
Exercise logging utility environment and formatting edges.
"""

from __future__ import annotations

import importlib

import fontshow.core.logging_utils as logging_utils


def test_log_level_and_trace_selector_env_parsing(monkeypatch):
    """
    Ensure invalid or special env values fall back deterministically.
    """
    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", "trace")
    assert logging_utils._get_log_level_from_env() == logging_utils.TRACE_LEVEL_NUM

    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", "invalid")
    assert logging_utils._get_log_level_from_env() is None

    monkeypatch.delenv("FONTSHOW_TRACE", raising=False)
    logging_utils._parse_trace_selector.cache_clear()
    assert logging_utils._parse_trace_selector() == (None, None)

    monkeypatch.setenv("FONTSHOW_TRACE", "none")
    logging_utils._parse_trace_selector.cache_clear()
    assert logging_utils._parse_trace_selector() == (set(), None)

    monkeypatch.setenv("FONTSHOW_TRACE", "io,-raw")
    logging_utils._parse_trace_selector.cache_clear()
    assert logging_utils._parse_trace_selector() == ({"io"}, {"raw"})


def test_raw_truncation_and_human_format(monkeypatch):
    """
    Ensure raw truncation and human formatting hit their boundary paths.
    """
    monkeypatch.setenv("FONTSHOW_TRACE_RAW_MAXLEN", "0")
    logging_utils._raw_max_len.cache_clear()
    assert logging_utils._truncate_raw("abcdef") == (
        "",
        {"raw_truncated": True, "raw_len": 6},
    )

    monkeypatch.setenv("FONTSHOW_TRACE_RAW_MAXLEN", "bad")
    logging_utils._raw_max_len.cache_clear()
    assert logging_utils._raw_max_len() == 4096

    assert logging_utils._format_trace_human("msg", None) == "msg"
    assert (
        logging_utils._format_trace_human("msg", {"trace_category": "io", "x": 1})
        == "msg | [io] | x=1"
    )


def test_configure_root_logger_disabled_and_trace_entrypoint_boundaries(monkeypatch):
    """
    Ensure disabled logging and invalid categories are harmless no-ops.
    """
    monkeypatch.delenv("FONTSHOW_LOG_LEVEL", raising=False)
    importlib.reload(logging_utils)
    assert logging_utils._configure_root_logger() is None

    records: list[tuple[int, str]] = []

    class FakeLogger:
        def isEnabledFor(self, level: int) -> bool:
            return True

        def log(self, level: int, message: str, **kwargs) -> None:
            records.append((level, message))

    logging_utils.log_trace_cat(FakeLogger(), "not-a-category", "ignored")
    assert records == []

    monkeypatch.setenv("FONTSHOW_TRACE_FORMAT", "human")
    logging_utils._trace_format.cache_clear()
    logging_utils.log_trace_cat(FakeLogger(), "io", "event", extra={"a": 1}, raw="xyz")
    assert records[-1][1].startswith("[TRACE] event | [io]")
