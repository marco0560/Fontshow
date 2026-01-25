# fontshow/preflight/__main__.py

"""
Fontshow preflight entry point.

Allows running preflight checks via:

    python -m fontshow.preflight
"""

from __future__ import annotations

import sys

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
    result = run_preflight_fn()
    exit_code = preflight_exit_code(result)

    quiet = getattr(args, "quiet", False) if args is not None else False
    verbose = getattr(args, "verbose", False) if args is not None else False

    if not quiet:
        lines = render_preflight_results(result.results, verbose=verbose)
        for line in lines:
            print(line)

    if not quiet:
        if exit_code == 0:
            print("Preflight passed.")
        else:
            print(f"Preflight failed with exit code {exit_code}.", file=sys.stderr)

    return exit_code


def main(args=None) -> int:
    return _run_preflight_cli(args=args)


if __name__ == "__main__":
    sys.exit(main())
