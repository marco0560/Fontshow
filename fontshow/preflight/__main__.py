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


def main(args=None) -> int:
    result = run_preflight()
    exit_code = preflight_exit_code(result)

    quiet = getattr(args, "quiet", False) if args is not None else False
    verbose = getattr(args, "verbose", False) if args is not None else False

    if not quiet:
        lines = render_preflight_results(result.results, verbose=verbose)
        for line in lines:
            print(line)
        print("Preflight passed." if exit_code == 0 else "Preflight failed.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
