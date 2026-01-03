import argparse
import sys

from fontshow.cli_utils import add_common_arguments
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
    add_common_arguments(parser)

    args = parser.parse_args()

    result = run_preflight()
    lines = render_preflight_results(result.results, verbose=args.verbose)

    if not args.quiet:
        for line in lines:
            print(line)

    return preflight_exit_code(result)


if __name__ == "__main__":
    sys.exit(main())
