# fontshow/preflight/__main__.py

"""
Fontshow preflight entry point.

Allows running preflight checks via:

    python -m fontshow.preflight
"""

from __future__ import annotations

import sys

from fontshow.cli_utils import log_err, log_info, log_ok, log_warn
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
    quiet = getattr(args, "quiet", False) if args is not None else False
    verbose = getattr(args, "verbose", False) if args is not None else False

    log_trace_cat(
        log,
        "flow",
        "preflight entrypoint started",
        extra={
            "quiet": bool(quiet),
            "verbose": bool(verbose),
        },
    )

    result = run_preflight_fn()
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

    if not quiet:
        # render_preflight_results() returns list[str]
        rendered_lines = render_preflight_results(
            result.results,
            verbose=verbose,
        )

        for line in rendered_lines:
            # Severity prefix is already embedded in the rendered line
            if line.startswith("[OK"):
                log_ok(line[7:])
            elif line.startswith("[INFO"):
                log_info(line[7:])
            elif line.startswith("[WARN"):
                log_warn(line[7:])
            else:
                # Includes [ERR ] and any unexpected severity
                log_err(line[7:])

        if exit_code == 0:
            log_ok("Preflight passed.")
        else:
            log_err(f"Preflight failed with exit code {exit_code}.")

    return exit_code


def main(args=None) -> int:
    return _run_preflight_cli(args=args)


if __name__ == "__main__":
    sys.exit(main())
