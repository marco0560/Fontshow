from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fontshow")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
# ---------------------------------------------------------------------------
# CLI command re-exports (compatibility layer)
#
# Historically these modules lived at the top level of the package.
# After the CLI refactor they reside in `fontshow.cli`, but we keep
# these imports so existing code and tests can still do:
#
#   ->  from fontshow import dump_fonts
#   ->  from fontshow import create_catalog
#
# ---------------------------------------------------------------------------

from fontshow.cli import (
    create_catalog as create_catalog,
    dump_fonts as dump_fonts,
    parse_inventory as parse_inventory,
    validate_inventory as validate_inventory,
)
