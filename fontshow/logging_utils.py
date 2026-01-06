# fontshow/logging_utils.py

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
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


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
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(levelname)s %(module)s.%(funcName)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


_ROOT_LOGGER = _configure_root_logger()


# -----------------------------
# Public logging facade
# -----------------------------


class _LogFacade:
    """
    Minimal logging facade.

    - Disabled by default
    - Preserves caller module and function
    - Structured payload via 'extra'
    """

    def _logger(self) -> logging.Logger | None:
        return _ROOT_LOGGER

    def error(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.error(message, extra={"extra": extra} if extra else None)

    def warning(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.warning(message, extra={"extra": extra} if extra else None)

    def info(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.info(message, extra={"extra": extra} if extra else None)

    def debug(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.debug(message, extra={"extra": extra} if extra else None)

    def trace(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        logger = self._logger()
        if logger:
            logger.trace(message, extra={"extra": extra} if extra else None)


log = _LogFacade()
