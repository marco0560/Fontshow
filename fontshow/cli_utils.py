import argparse

from fontshow import __version__


def add_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
