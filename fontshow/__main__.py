import argparse
import sys

from fontshow.preflight.render import (
    preflight_exit_code,
    render_preflight_results,
)
from fontshow.preflight.runner import run_preflight


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="fontshow",
        description="Fontshow preflight checks",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed preflight output",
    )

    args = parser.parse_args()

    result = run_preflight()
    lines = render_preflight_results(result.results, verbose=args.verbose)

    for line in lines:
        print(line)

    return preflight_exit_code(result)


if __name__ == "__main__":
    sys.exit(main())
