from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


# -----------------------------
# TRACE level (custom)
# -----------------------------

TRACE_LEVEL_NUM = 5  # lower than DEBUG (10)
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")


def _trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(
            TRACE_LEVEL_NUM,
            message,
            args,
            **kwargs,
        )


logging.Logger.trace = _trace  # type: ignore[attr-defined]


# -----------------------------
# Logger initialization
# -----------------------------

# If FONTSHOW_LOG_LEVEL is not set, logging is disabled by design.

_ENV_VAR = "FONTSHOW_LOG_LEVEL"


def _get_log_level_from_env() -> int | None:
    value = os.environ.get(_ENV_VAR)
    if not value:
        return None

    value = value.upper().strip()
    if value == "TRACE":
        return TRACE_LEVEL_NUM

    return logging._nameToLevel.get(value)


def _configure_root_logger() -> logging.Logger | None:
    level = _get_log_level_from_env()
    if level is None:
        return None

    logger = logging.getLogger("fontshow")

    # IMPORTANT:
    # - allow propagation so pytest caplog can capture logs
    logger.setLevel(level)
    logger.propagate = True

    # Install a default handler only if none exists.
    # This makes CLI logging (including TRACE) visible while preserving
    # pytest caplog and allowing external override.
    if not logger.handlers:
        handler = logging.StreamHandler()
        logger.addHandler(handler)

    return logger


_ROOT_LOGGER = _configure_root_logger()


# -----------------------------
# Public logging facade
# -----------------------------
def _prepare_extra(extra: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    Normalize user-provided structured data so it is always available
    as `record.extra` for formatters.
    """
    return {"extra": dict(extra) if extra else {}}


class _LogFacade:
    """
    Minimal logging facade.

    - Disabled by default
    - Preserves caller module and function (via stacklevel)
    - Structured payload via 'extra'

    stacklevel=2 ensures log origin points to caller, not facade

    """

    def isEnabledFor(self, level: int) -> bool:
        """Proxy to underlying stdlib logger."""
        logger = self._logger()
        return bool(logger and logger.isEnabledFor(level))

    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        """
        Proxy to stdlib logger.log().

        Contract:
            - MUST never raise
            - If logging is disabled/uninitialized, MUST be a no-op.

        Note on stacklevel:
            - We accept a `stacklevel` kwarg and increment it by 1 to account
              for this facade frame.
        """
        logger = self._logger()
        if logger is None:
            return

        stacklevel = kwargs.pop("stacklevel", 1)
        logger.log(level, msg, *args, stacklevel=stacklevel + 1, **kwargs)

    def _logger(self) -> logging.Logger | None:
        return _ROOT_LOGGER

    def error(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.error(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def warning(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.warning(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def info(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.info(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def debug(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.debug(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def trace(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger and logger.isEnabledFor(TRACE_LEVEL_NUM):
            logger._log(
                TRACE_LEVEL_NUM,
                message,
                (),
                extra=_prepare_extra(extra),
                stacklevel=2,
            )


log = _LogFacade()

# ============================================================
# TRACE selective architecture (Phase B-DEEP)
# ============================================================

# ------------------------------------------------------------
# TRACE categories (stable identifiers)
# ------------------------------------------------------------

TRACE_CATEGORIES: set[str] = {
    "io",
    "raw",
    "parse",
    "infer",
    "validate",
    "cache",
    "perf",
    "flow",
    "latex",
}

# ------------------------------------------------------------
# Category selector parsing
# ------------------------------------------------------------


@lru_cache(maxsize=1)
def _parse_trace_selector() -> tuple[set[str] | None, set[str] | None]:
    """
    Parse FONTSHOW_TRACE selector.

    Returns:
        (include_set | None, exclude_set | None)

    Rules:
        None include_set → treat as "all"
        Special tokens:
            all
            none
    """
    raw = os.environ.get("FONTSHOW_TRACE")
    if not raw:
        return None, None  # default = all

    raw = raw.strip().lower()

    if raw == "all":
        return None, None

    if raw == "none":
        return set(), None

    include: set[str] = set()
    exclude: set[str] = set()

    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if token.startswith("-"):
            exclude.add(token[1:])
        else:
            include.add(token)

    return include, exclude


def trace_enabled(category: str) -> bool:
    """
    Fast check whether TRACE is enabled for a category.

    Requires global TRACE level already active.
    """
    include, exclude = _parse_trace_selector()

    if include is None:
        # default = all categories allowed
        return not (exclude and category in exclude)

    if not include:
        return False

    if category not in include:
        return False

    return not (exclude and category in exclude)


# ------------------------------------------------------------
# RAW truncation guard
# ------------------------------------------------------------


@lru_cache(maxsize=1)
def _raw_max_len() -> int:
    val = os.environ.get("FONTSHOW_TRACE_RAW_MAXLEN")
    if not val:
        return 4096
    try:
        return max(0, int(val))
    except ValueError:
        return 4096


def _truncate_raw(value: str) -> tuple[str, dict]:
    """
    Truncate raw TRACE payload if needed.

    Returns:
        (possibly_truncated_value, metadata)
    """
    max_len = _raw_max_len()
    if max_len <= 0:
        return "", {"raw_truncated": True, "raw_len": len(value)}

    if len(value) <= max_len:
        return value, {}

    return (
        value[:max_len],
        {"raw_truncated": True, "raw_len": len(value)},
    )


# ------------------------------------------------------------
# TRACE output formatting
# ------------------------------------------------------------


@lru_cache(maxsize=1)
def _trace_format() -> str:
    fmt = os.environ.get("FONTSHOW_TRACE_FORMAT", "json").lower()
    return "human" if fmt == "human" else "json"


def _format_trace_human(msg: str, extra: dict | None) -> str:
    """
    Convert structured TRACE into readable form.
    """
    if not extra:
        return msg

    parts = [msg]

    cat = extra.get("trace_category")
    if cat:
        parts.append(f"[{cat}]")

    for k, v in extra.items():
        if k == "trace_category":
            continue
        parts.append(f"{k}={v}")

    return " | ".join(parts)


# ------------------------------------------------------------
# TRACE entry point
# ------------------------------------------------------------


def log_trace_cat(
    logger,
    category: str,
    message: str,
    *,
    extra: dict | None = None,
    raw: str | None = None,
    **kwargs,
) -> None:
    """
    Emit a TRACE event under a category.

    Conditions:
        - global TRACE level must be active
        - category must be enabled

    Structured field:
        extra["trace_category"] = category
    """

    if not logger.isEnabledFor(TRACE_LEVEL_NUM):
        return

    if category not in TRACE_CATEGORIES:
        return

    if not trace_enabled(category):
        return

    if extra is None:
        extra = {}

    extra = dict(extra)
    extra["trace_category"] = category

    if raw is not None:
        raw_val, meta = _truncate_raw(raw)
        extra["raw"] = raw_val
        extra.update(meta)

    # stacklevel=3 points to the functional emitter (_run_fc_query).
    # This is intentional and part of the TRACE design contract.
    _stacklevel_public = 3

    if _trace_format() == "human":
        # Human TRACE is rendered as a readable, self-contained line.
        # _format_trace_human() already appends:
        #   -> "[<category>]"
        #   - "k=v" pairs for all extra fields (except trace_category)
        message = "[TRACE] " + _format_trace_human(message, extra)
        logger.log(
            TRACE_LEVEL_NUM,
            message,
            stacklevel=_stacklevel_public,
            **kwargs,
        )
    else:
        # JSON TRACE must be recognizable even with a plain StreamHandler
        # (no formatter). Emit structured payload via `extra`, while keeping
        # the raw message in LogRecord.message (required by tests and caller
        # attribution checks).
        import json  # local import: keep module-level imports unchanged

        payload: dict[str, object] = {
            "level": "TRACE",
            "category": category,
            "message": message,
        }
        for k, v in extra.items():
            if k == "trace_category":
                continue
            payload[k] = v

        extra["_trace_json"] = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )

        logger.log(
            TRACE_LEVEL_NUM,
            message,  # ← raw message preserved
            extra=extra,
            stacklevel=_stacklevel_public,
            **kwargs,
        )
