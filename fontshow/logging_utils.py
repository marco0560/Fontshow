from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from typing import Any

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

    # Prevent propagation to root logger
    logger.propagate = False

    # Logger decides WHAT levels are enabled
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        logger.addHandler(handler)
    else:
        handler = logger.handlers[0]

    # Handler must NOT filter by level (or TRACE will be dropped)
    handler.setLevel(logging.NOTSET)

    formatter = logging.Formatter(
        #        "%(levelname)s %(module)s.%(funcName)s: %(message)s"
        "%(levelname)s %(module)s.%(funcName)s: %(message)s | %(extra)s"
    )
    handler.setFormatter(formatter)

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
    """

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
