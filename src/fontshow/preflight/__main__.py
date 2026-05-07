"""
Preflight CLI entry point.

This module implements the command-line entry point used to execute the
Fontshow preflight checks.

Responsibilities
----------------
- Run the preflight check pipeline.
- Render a human-readable report describing check results.
- Produce deterministic process exit codes based on check outcomes.

Design principles
-----------------
The entry point performs only CLI orchestration and presentation logic.
Actual check execution is delegated to the preflight runner and check
registry modules.

Architectural role
------------------
This module belongs to the **preflight subsystem** and provides the
standalone CLI interface invoked via `python -m fontshow.preflight`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from fontshow.core.cli_utils import (
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.core.logging_utils import log, log_trace_cat

from .render import preflight_exit_code, render_preflight_results
from .runner import run_preflight

if TYPE_CHECKING:
    import argparse
    from collections.abc import Callable

    from .model import PreflightResult


def run_preflight_cli(
    *,
    args: argparse.Namespace | None = None,
    run_preflight_fn: Callable[[], PreflightResult] = run_preflight,
) -> int:
    """
    Core preflight CLI logic.

    Parameters
    ----------
    args : argparse.Namespace, optional
        Parsed CLI arguments providing optional `verbose` and `output`
        attributes.
    run_preflight_fn : callable, optional
        Injectable runner function used for testing and CLI indirection.

    Returns
    -------
    int
        Exit code derived from preflight execution and report rendering.

    Raises
    ------
    None
        Internal execution and output-writing failures are converted into
        user-facing error messages and non-zero exit codes.

    Notes
    -----
    This function is intentionally side-effect free (no `sys.exit`) so
    it can be tested easily and supports dependency injection.
    """
    quiet = getattr(args, "quiet", False)
    verbose = getattr(args, "verbose", False)
    set_cli_mode(quiet, verbose)

    log_trace_cat(
        log,
        "flow",
        "preflight entrypoint started",
    )

    try:
        result = run_preflight_fn()
    except Exception as exc:  # noqa: BLE001
        log_err(f"Preflight internal error: {exc}")
        return 2

    exit_code = preflight_exit_code(result)

    log_trace_cat(
        log,
        "flow",
        "preflight execution completed",
        extra={
            "exit_code": int(exit_code),
            "checks_run": len(getattr(result, "results", []) or []),
        },
    )

    # render_preflight_results() returns formatted lines
    rendered_lines = render_preflight_results(
        result.results,
        verbose=verbose,
    )

    output_path = getattr(args, "output", None)
    if output_path is not None:
        try:
            text = "\n".join(rendered_lines)
            if text:
                text += "\n"
            Path(output_path).write_text(text, encoding="utf-8")
        except OSError as exc:
            log_err(f"Failed to write preflight report: {exc}")
            return 1

    if verbose:
        for line in rendered_lines:
            if line.startswith("[OK"):
                log_ok(line[7:])
            elif line.startswith("[INFO"):
                log_info(line[7:])
            elif line.startswith("[WARN"):
                log_warn(line[7:])
            else:
                log_err(line[7:])

    if exit_code == 0:
        log_ok("Preflight passed.")
    else:
        log_err(f"Preflight failed with exit code {exit_code}.")

    return exit_code


def main(args: argparse.Namespace | None = None) -> int:
    """
    Execute the preflight CLI entrypoint.

    Parameters
    ----------
    args : argparse.Namespace, optional
        Parsed CLI arguments with optional `quiet` and `verbose`
        attributes.

    Returns
    -------
    int
        Process exit code produced by the preflight CLI workflow.

    Notes
    -----
    Unexpected internal exceptions are converted into exit code ``2``
    after user-facing error reporting.

    CLI quiet/verbose mode is configured before delegating to the core
    runner so report emission follows the shared CLI presentation
    contract.
    """
    try:
        return run_preflight_cli(args=args)
    except Exception as exc:  # noqa: BLE001
        log_err(f"Preflight internal error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
