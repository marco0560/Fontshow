"""
Verify the Fontshow package version definition.

Responsibilities
----------------
- Ensure the package exposes a __version__ attribute.
- Validate that the version string follows PEP 440 semantics.

Design principles
----------------
Version tests parse the version string using packaging utilities to
ensure consistent semantic versioning behavior.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
version metadata exposed by the Fontshow package.
"""

from packaging.version import Version

from fontshow import __version__


def test_version_is_defined():
    assert isinstance(__version__, str)

    v = Version(__version__)  # PEP 440 parsing
    assert len(v.release) == 3  # major.minor.patch
