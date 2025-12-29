from packaging.version import Version

from fontshow import __version__


def test_version_is_defined():
    assert isinstance(__version__, str)

    v = Version(__version__)  # PEP 440 parsing
    assert len(v.release) == 3  # major.minor.patch
