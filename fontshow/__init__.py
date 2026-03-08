"""
Fontshow package initialization and compatibility exports.

Responsibilities
----------------
- Expose the package version through the ``__version__`` attribute.
- Provide backward-compatible re-exports for CLI command modules that
  historically lived at the top level of the package.
- Allow external code and tests to import CLI entrypoints from the
  package root.

Design principles
-----------------
The package initializer should remain minimal and avoid importing heavy
subsystems at import time. Only lightweight compatibility exports and
metadata retrieval are performed here.

Architectural role
------------------
This module belongs to the **package infrastructure layer** and provides
version metadata and compatibility imports for the Fontshow CLI modules.
"""

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
