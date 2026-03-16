"""
CLI utility helpers.

This module provides shared utilities used by Fontshow command-line
modules to implement consistent argument handling and terminal output.

Responsibilities
----------------
- Manage CLI presentation modes (quiet / verbose).
- Provide standardized logging helpers for CLI output.
- Register common CLI arguments shared across commands.
- Route messages according to severity levels.

Design principles
-----------------
CLI presentation concerns are centralized here so that command modules
remain focused on workflow orchestration. All user-visible terminal
messages should pass through these helpers to ensure deterministic and
consistent output formatting.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and provides
CLI-facing utilities used by command modules in the `fontshow.cli`
package.
"""

import argparse
import sys
from argparse import _ActionsContainer
from pathlib import Path

from fontshow import __version__
from fontshow.core.types import Severity

# ------------------------------------------------------------
# Centralized CLI presentation state
# ------------------------------------------------------------

_QUIET: bool = False
_VERBOSE: bool = False


def set_cli_mode(quiet: bool, verbose: bool) -> None:
    """
    Set global CLI presentation mode.

    Parameters
    ----------
    quiet : bool
        If True, suppress INFO and OK messages.
    verbose : bool
        If True, enable verbose message variants. Ignored if
        `quiet` is True.

    Returns
    -------
    None
    """
    global _QUIET, _VERBOSE
    _QUIET = bool(quiet)
    _VERBOSE = bool(verbose) and not _QUIET


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def _format_extra(extra: dict | None) -> str:
    """
    Deterministically format extra key/value pairs for CLI output.

    For small payloads a single-line format is used:

        | key=value | key=value

    For larger payloads a multi-line aligned block is produced
    to improve CLI readability.

    Keys are always sorted to preserve deterministic output.

    Parameters
    ----------
    extra : dict | None
        Optional mapping of extra key/value pairs attached to a CLI
        log event.

    Returns
    -------
    str
        Formatted suffix for CLI output. Returns an empty string when
        no extra fields are present.
    """
    if not extra:
        return ""

    keys = sorted(extra)

    # Small payload → keep original compact format
    if len(keys) <= 5:
        return " | " + " | ".join(f"{k}={extra[k]}" for k in keys)

    # Larger payload → aligned multi-line block
    width = max(len(k) for k in keys)
    lines = [f"\n       {k:<{width}} = {extra[k]}" for k in keys]

    return "".join(lines)


def _select_message(default: str, verbose: str | None) -> str:
    """
    Select message according to CLI mode.

    Parameters
    ----------
    default : str
        Message used in normal (non-verbose) mode.
    verbose : str | None
        Alternate message used when verbose mode is active.
        If None, the default message is used.

    Returns
    -------
    str
        Message selected according to the current CLI verbosity mode.
        If verbose mode is enabled and `verbose` is not None, the
        verbose message is returned; otherwise the default message
        is returned.
    """
    if _VERBOSE and verbose:
        return verbose
    return default


# ------------------------------------------------------------
# CLI presentation API
# ------------------------------------------------------------


def log_info(
    default: str, verbose: str | None = None, *, extra: dict | None = None
) -> None:
    """
    Emit a CLI INFO message.

    Parameters
    ----------
    default : str
        Default message used when verbose mode is not active.
    verbose : str | None, optional
        Alternate message used when verbose mode is active.
        If None, the default message is used.
    extra : dict | None, optional
        Optional key/value pairs appended to the message using
        deterministic formatting.

    Returns
    -------
    None

    Notes
    -----
    - Suppressed in quiet mode.
    - Verbose message is used when verbose mode is active.
    - Extra fields are formatted deterministically.
    """
    if _QUIET:
        return

    message = _select_message(default, verbose)
    message += _format_extra(extra)

    print(f"[INFO] {message}")


def log_ok(
    default: str, verbose: str | None = None, *, extra: dict | None = None
) -> None:
    """
    Emit a CLI OK message.

    Parameters
    ----------
    default : str
        Default message used when verbose mode is not active.
    verbose : str | None, optional
        Alternate message used when verbose mode is active.
        If None, the default message is used.
    extra : dict | None, optional
        Optional key/value pairs appended to the message using
        deterministic formatting.

    Returns
    -------
    None

    Notes
    -----
    Same behavior as `log_info`.
    Suppressed in quiet mode.
    """
    if _QUIET:
        return

    message = _select_message(default, verbose)
    message += _format_extra(extra)

    print(f"[OK  ] {message}")


def log_warn(message: str) -> None:
    """
    Emit a CLI WARNING message.

    Parameters
    ----------
    message : str
        Warning message to display.

    Returns
    -------
    None

    Notes
    -----
    This message is always shown and is written to stderr.
    """
    print(f"[WARN] {message}", file=sys.stderr)


def log_err(message: str) -> None:
    """
    Emit a CLI ERROR message.

    Parameters
    ----------
    message : str
        Error message to display.

    Returns
    -------
    None

    Notes
    -----
    This message is always shown and is written to stderr.
    """
    print(f"[ERR ] {message}", file=sys.stderr)


def _log_by_severity(severity: Severity | None, message: str) -> None:
    """
    Route a log message according to severity.

    Parameters
    ----------
    severity : Severity | None
        Severity level used to determine routing. If None or not an
        instance of `Severity`, it is treated as `Severity.INFO`.
    message : str
        Message to emit.

    Returns
    -------
    None

    Notes
    -----
    - Severity is normalized to the `Severity` enum.
    - CLI output remains string-based.
    """
    # --- Normalize severity to enum (Enum-only contract) ---
    sev_enum = severity if isinstance(severity, Severity) else Severity.INFO

    # --- Route log ---
    if sev_enum is Severity.WARN:
        log_warn(message)
    elif sev_enum is Severity.ERROR:
        log_err(message)
    elif sev_enum is Severity.OK:
        log_ok(message)
    else:
        log_info(message)


def _add_version_argument(parser: argparse.ArgumentParser) -> None:
    """
    Add the standard Fontshow version flag to a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Argument parser to extend with the version action.

    Returns
    -------
    None
    """
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )


def _add_verbose_argument(parser: _ActionsContainer) -> None:
    """
    Add the standard verbose-mode flag to a parser or argument group.

    Parameters
    ----------
    parser : _ActionsContainer
        Parser-like action container to extend.

    Returns
    -------
    None
    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose mode",
    )


def _add_quiet_argument(parser: _ActionsContainer) -> None:
    """
    Add the standard quiet-mode flag to a parser or argument group.

    Parameters
    ----------
    parser : _ActionsContainer
        Parser-like action container to extend.

    Returns
    -------
    None
    """
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Enable quiet mode",
    )


def add_common_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_output: bool = False,
    output_default: Path | None = None,
    output_help: str = "Output file",
) -> None:
    """
    Add CLI arguments common to all Fontshow commands.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Argument parser to which common CLI options are added.
    include_output : bool
        If True, also add `-o/--output`.
    output_default : Path | None
        Default output path used when `include_output` is True.
    output_help : str
        Help string for the `-o/--output` argument.

    Returns
    -------
    None

    Notes
    -----
    Adds:
    - `--version`
    - `--verbose`
    - `--quiet`
    - `--output` (optional)

    Raises
    ------
    argparse.ArgumentError
        May be raised by argparse if conflicting options are added to
        a parser that already defines the same flags.
    """
    if include_output:
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=output_default,
            help=output_help,
        )

    _add_version_argument(parser)

    group = parser.add_mutually_exclusive_group()

    _add_verbose_argument(group)
    _add_quiet_argument(group)
