"""
Fontshow preflight entry point.

Allows running preflight checks via:

    python -m fontshow.preflight
"""

import sys

from .render import preflight_exit_code, render_preflight_results
from .runner import run_preflight


def main() -> None:
    result = run_preflight()
    render_preflight_results(result.results)
    sys.exit(preflight_exit_code(result))


if __name__ == "__main__":
    main()
