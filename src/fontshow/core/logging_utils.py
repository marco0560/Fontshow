"""
Structured logging subsystem.

This module implements the centralized logging infrastructure used
throughout Fontshow.

Responsibilities
----------------
- Provide a lightweight logging facade wrapping the Python stdlib
  logging system.
- Define and manage the custom TRACE logging level.
- Implement structured logging helpers for deterministic diagnostics.
- Support category-based TRACE filtering.

Design principles
-----------------
Logging must never interfere with program execution. When disabled,
logging calls must behave as no-ops with minimal overhead. Structured
logging output must remain deterministic and machine-readable.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and provides
the logging framework used across all Fontshow subsystems.


ARCHITECTURAL NOTES:
====================

This module provides the centralized logging infrastructure used across
Fontshow, including:

- A minimal logging facade (`log`) wrapping the stdlib logger.
- A custom TRACE level (numeric level 5) below DEBUG.
- Structured logging with deterministic payload handling.
- Category-based selective TRACE architecture.
- Environment-driven configuration.

Logging activation
------------------
Logging is **disabled by default**.

To enable logging, set:

    FONTSHOW_LOG_LEVEL = TRACE | DEBUG | INFO | WARNING | ERROR | CRITICAL

If the variable is unset, all logging calls become no-ops.

TRACE subsystem
--------------
TRACE is a fine-grained, high-frequency diagnostic channel designed for:

- pipeline tracing
- performance instrumentation
- I/O inspection
- parser and inference diagnostics
- cache and flow observation

TRACE is controlled by:

    FONTSHOW_TRACE
        Category selector (comma-separated).
        Example selectors include:
            all
            none
            io,parse,perf
            all,-raw
            infer,-perf

    FONTSHOW_TRACE_FORMAT
        "json" (default) or "human"

    FONTSHOW_TRACE_RAW_MAXLEN
        Maximum RAW payload size (default: 4096)

Design invariants
-----------------
- Logging must NEVER raise exceptions.
- Logging must be safe when disabled (no-op).
- Caller attribution must be preserved (stacklevel handling).
- Structured data must remain machine-readable.
- TRACE must be deterministic and filterable by category.
- Module must be side-effect safe except for logger initialization.

Architecture
------------
1. Root logger configured lazily from environment.
2. Public facade (`log`) wraps stdlib logging.
3. TRACE category selector filters high-volume events.
4. RAW payload guard prevents unbounded logs.
5. Optional human-readable TRACE formatting.

Notes
-----
- TRACE level numeric value = 5 (below DEBUG).
- Logger name: "fontshow".
- Propagation enabled to support pytest caplog and external handlers.
- Default StreamHandler installed only if no handlers exist.
- Structured TRACE JSON payload is stored in LogRecord.extra["_trace_json"].
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping

    from fontshow.core.types import JSONDict

# -----------------------------
# TRACE level (custom)
# -----------------------------

TRACE_LEVEL_NUM = 5  # lower than DEBUG (10)
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")


class SupportsLog(Protocol):
    """
    Minimal logging protocol required by TRACE helpers.
    """

    def isEnabledFor(self, level: int) -> bool:
        """
        Report whether logging is enabled for a level.

        Parameters
        ----------
        level : int
            Logging level to check.

        Returns
        -------
        bool
            ``True`` when records at ``level`` should be emitted.
        """
        ...

    def log(
        self,
        level: int,
        msg: str,
        *args: object,
        **kwargs: Any,
    ) -> None:
        """
        Emit a log record with stdlib-compatible arguments.

        Parameters
        ----------
        level : int
            Logging level attached to the record.
        msg : str
            Log message template.
        *args : object
            Positional formatting arguments passed to the logger.
        **kwargs : typing.Any
            Keyword arguments forwarded to the logger implementation.

        Returns
        -------
        None
        """
        ...


def _trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    """
    Emit a TRACE-level log record using the stdlib logger.

    Parameters
    ----------
    self : logging.Logger
        Logger instance receiving the TRACE call.
    message : str
        Log message.
    *args : Any
        Positional arguments passed to the logging formatter.
    **kwargs : Any
        Keyword arguments forwarded to Logger._log().

    Returns
    -------
    None

    Notes
    -----
    - TRACE level is custom (numeric level 5).
    - Only emits if TRACE level is enabled on the logger.
    - Installed dynamically as `logging.Logger.trace`.
    - Low-level helper; not intended for direct external use.
    """
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
    """
    Resolve logging level from environment variable.

    Parameters
    ----------
    None

    Returns
    -------
    int | None
        Numeric logging level derived from `FONTSHOW_LOG_LEVEL`,
        or None if logging is disabled or variable is unset/invalid.

    Notes
    -----
    - Special value "TRACE" maps to custom TRACE level.
    - Standard logging names (DEBUG, INFO, WARNING, ERROR, CRITICAL) are supported.
    - If the environment variable is absent, logging is disabled by design.
    """
    value = os.environ.get(_ENV_VAR)
    if not value:
        return None

    value = value.upper().strip()
    if value == "TRACE":
        return TRACE_LEVEL_NUM

    return logging._nameToLevel.get(value)


def _configure_root_logger() -> logging.Logger | None:
    """
    Configure and return the root Fontshow logger.

    Parameters
    ----------
    None

    Returns
    -------
    logging.Logger | None
        Configured logger instance if logging is enabled,
        otherwise None.

    Notes
    -----
    - Logging is enabled only when `FONTSHOW_LOG_LEVEL` is set.
    - Logger name: "fontshow".
    - Propagation is enabled so pytest caplog and external handlers can capture logs.
    - Installs a default StreamHandler only if no handlers exist.
    - Designed to be idempotent and safe across repeated imports.
    """
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
    Normalize structured logging payload.

    Parameters
    ----------
    extra : Mapping[str, Any] | None
        User-provided structured logging data.

    Returns
    -------
    dict[str, Any]
        Mapping wrapped under the key `"extra"` suitable for LogRecord.

    Notes
    -----
    - Guarantees `record.extra` exists for formatters.
    - Ensures a shallow copy to avoid mutation of caller data.
    - Returns empty structure when `extra` is None.
    """
    return {"extra": dict(extra) if extra else {}}


class _LogFacade:
    """
    Minimal logging facade used by the rest of the codebase.

    Responsibilities
    ----------------
    - Provide a narrow wrapper around the configured stdlib logger.
    - Expose convenience methods for the standard levels plus TRACE.
    - Preserve caller attribution by adjusting ``stacklevel``.
    - Normalize structured payloads passed through ``extra``.

    Design principles
    -----------------
    The facade must be safe to call when logging is disabled and must
    never force callers to guard logging statements themselves. All
    methods act as thin wrappers so logging behavior remains predictable
    and close to the stdlib implementation.

    Notes
    -----
    - Disabled by default.
    - Preserves caller module and function via ``stacklevel`` handling.
    - Structured payloads are routed through the ``extra`` field.
    - ``stacklevel=2`` ensures log origin points to the caller, not the
      facade.
    """

    def isEnabledFor(self, level: int) -> bool:
        """
        Check whether logging is enabled for a given level.

        Parameters
        ----------
        level : int
            Numeric logging level.

        Returns
        -------
        bool
            True if underlying logger exists and level is enabled,
            otherwise False.

        Notes
        -----
        - Safe when logging is disabled (returns False).
        - Thin proxy to underlying stdlib logger.
        """
        logger = self._logger()
        return bool(logger and logger.isEnabledFor(level))

    def log(self, level: int, msg: str, *args: object, **kwargs: Any) -> None:
        """
        Emit a log record at arbitrary level.

        Parameters
        ----------
        level : int
            Logging level.
        msg : str
            Log message.
        *args : Any
            Positional arguments forwarded to the logger.
        **kwargs : Any
            Keyword arguments forwarded to the logger.

        Returns
        -------
        None

        Notes
        -----
        Contract:
        - MUST never raise exceptions.
        - MUST be a no-op if logging is disabled.

        Behavior:
        - Accepts `stacklevel` and increments it by 1 to preserve caller origin.
        - Delegates to stdlib `logger.log()`.
        """
        logger = self._logger()
        if logger is None:
            return

        stacklevel = kwargs.pop("stacklevel", 1)
        logger.log(level, msg, *args, stacklevel=stacklevel + 1, **kwargs)

    def _logger(self) -> logging.Logger | None:
        """
        Return the current root logger wrapper target.

        Parameters
        ----------
        None

        Returns
        -------
        logging.Logger | None
            Active configured logger, or None when logging is disabled.
        """
        return _ROOT_LOGGER

    def error(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        """
        Emit an ERROR-level log record.

        Parameters
        ----------
        message : str
            Log message.
        extra : Mapping[str, Any] | None
            Structured payload.

        Returns
        -------
        None

        Notes
        -----
        - No-op when logging disabled.
        - Preserves caller stack frame using stacklevel=2.
        - Structured data normalized via `_prepare_extra()`.
        """
        logger = self._logger()
        if logger:
            logger.error(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def warning(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        """
        Emit a WARNING-level log record.

        Parameters
        ----------
        message : str
            Log message.
        extra : Mapping[str, Any] | None
            Structured payload.

        Returns
        -------
        None

        Notes
        -----
        - No-op when logging disabled.
        - Preserves caller stack frame using stacklevel=2.
        - Structured data normalized via `_prepare_extra()`.
        """
        logger = self._logger()
        if logger:
            logger.warning(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def info(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        """
        Emit an INFO-level log record.

        Parameters
        ----------
        message : str
            Log message.
        extra : Mapping[str, Any] | None
            Structured payload.

        Returns
        -------
        None

        Notes
        -----
        - No-op when logging disabled.
        - Preserves caller stack frame using stacklevel=2.
        - Structured data normalized via `_prepare_extra()`.
        """
        logger = self._logger()
        if logger:
            logger.info(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def debug(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        """
        Emit a DEBUG-level log record.

        Parameters
        ----------
        message : str
            Log message.
        extra : Mapping[str, Any] | None
            Structured payload.

        Returns
        -------
        None

        Notes
        -----
        - No-op when logging disabled.
        - Preserves caller stack frame using stacklevel=2.
        - Structured data normalized via `_prepare_extra()`.
        """
        logger = self._logger()
        if logger:
            logger.debug(
                message,
                extra=_prepare_extra(extra),
                stacklevel=2,
            )

    def trace(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        """
        Emit a TRACE-level log record.

        Parameters
        ----------
        message : str
            Log message.
        extra : Mapping[str, Any] | None
            Structured payload.

        Returns
        -------
        None

        Notes
        -----
        - No-op when logging disabled.
        - Only emits if TRACE level is enabled on the logger.
        - Preserves caller stack frame using stacklevel=2.
        - Structured data normalized via `_prepare_extra()`.
        """
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
    Parse TRACE category selector from environment.

    Parameters
    ----------
    None

    Returns
    -------
    tuple[set[str] | None, set[str] | None]
        (include_set, exclude_set)

    Notes
    -----
    Semantics:
    - include_set is None → all categories allowed.
    - Special values:
        "all"  → enable all categories.
        "none" → disable all categories.
    - Tokens starting with '-' indicate exclusion.
    - Cached for performance.
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
    Check whether TRACE is enabled for a category.

    Parameters
    ----------
    category : str
        TRACE category identifier.

    Returns
    -------
    bool
        True if TRACE logging is enabled for the category.

    Notes
    -----
    - Requires global TRACE level already active.
    - Uses selector parsed from `FONTSHOW_TRACE`.
    - Fast path designed for high-frequency TRACE calls.
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
    """
    Resolve maximum RAW TRACE payload length from environment.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Maximum number of characters allowed in RAW payload.

    Notes
    -----
    - Controlled by `FONTSHOW_TRACE_RAW_MAXLEN`.
    - Default: 4096.
    - Invalid values fall back to default.
    - Cached for performance.
    """
    val = os.environ.get("FONTSHOW_TRACE_RAW_MAXLEN")
    if not val:
        return 4096
    try:
        return max(0, int(val))
    except ValueError:
        return 4096


def _truncate_raw(value: str) -> tuple[str, JSONDict]:
    """
    Truncate RAW TRACE payload if exceeding configured limit.

    Parameters
    ----------
    value : str
        Raw TRACE payload.

    Returns
    -------
    tuple[str, JSONDict]
        (possibly_truncated_value, metadata)

    Notes
    -----
    - Metadata may include:
        raw_truncated : bool
        raw_len : int
    - When max length is 0, payload is fully suppressed.
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
    """
    Resolve TRACE output format from environment.

    Parameters
    ----------
    None

    Returns
    -------
    str
        Either "json" or "human".

    Notes
    -----
    - Controlled by `FONTSHOW_TRACE_FORMAT`.
    - Default: "json".
    - Cached for performance.
    """
    fmt = os.environ.get("FONTSHOW_TRACE_FORMAT", "json").lower()
    return "human" if fmt == "human" else "json"


def _format_trace_human(msg: str, extra: JSONDict | None) -> str:
    """
    Render structured TRACE event into human-readable format.

    Parameters
    ----------
    msg : str
        Base TRACE message.
    extra : JSONDict | None
        Structured TRACE payload.

    Returns
    -------
    str
        Human-readable TRACE line.

    Notes
    -----
    - Appends category and key=value pairs.
    - Used only when TRACE format = "human".
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
    logger: SupportsLog,
    category: str,
    message: str,
    *,
    extra: JSONDict | None = None,
    raw: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Emit a categorized TRACE log event.

    Parameters
    ----------
    logger : SupportsLog
        Logger instance used for emission.
    category : str
        TRACE category identifier.
    message : str
        TRACE message.
    extra : JSONDict | None
        Structured payload.
    raw : str | None
        Optional raw data payload subject to truncation.
    **kwargs : object
        Additional logging parameters.

    Returns
    -------
    None

    Notes
    -----
    Contract:
    - Emits only if TRACE level enabled and category allowed.
    - Must never raise exceptions.
    - Adds `extra["trace_category"]`.

    Behavior:
    - RAW payload truncated via `_truncate_raw()`.
    - Supports two output formats:
        - JSON structured TRACE (default)
        - Human-readable TRACE
    - Maintains caller attribution using stacklevel=3.
    - JSON TRACE embeds structured payload into `_trace_json`.

    TRACE architecture:
    - Category-based selective tracing.
    - Environment-controlled filtering.
    - Deterministic, machine-readable output.
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
            "event": message,
        }
        for k, v in extra.items():
            if k == "trace_category":
                continue
            payload[k] = v

        extra["_trace_json"] = json.dumps(
            payload,
            default=str,
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
