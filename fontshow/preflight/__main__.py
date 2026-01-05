"""
Fontshow preflight entry point.

Allows running preflight checks via:

    python -m fontshow.preflight
"""

import sys

from .render import render_preflight_result
from .runner import run_preflight


def main() -> None:
    result = run_preflight()
    render_preflight_result(result)
    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
