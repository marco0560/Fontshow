# fontshow/preflight/__main__.py

"""
Fontshow preflight entry point.

Allows running preflight checks via:

    python -m fontshow.preflight
"""

from __future__ import annotations

import sys
from pathlib import Path

from fontshow.cli_utils import (
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.logging_utils import log, log_trace_cat

from .render import preflight_exit_code, render_preflight_results
from .runner import run_preflight


def _run_preflight_cli(
    *,
    args=None,
    run_preflight_fn=run_preflight,
) -> int:
    """
    Core preflight CLI logic.

    This function is intentionally side-effect free (no sys.exit)
    so it can be tested easily and supports dependency injection.
    """
    _ = args  # Placeholder for potential future use
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
        verbose=getattr(args, "verbose", False),
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


def main(args=None) -> int:

    set_cli_mode(getattr(args, "quiet", False), getattr(args, "verbose", False))
    try:
        return _run_preflight_cli(args=args)
    except Exception as exc:  # noqa: BLE001
        log_err(f"Preflight internal error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
