"""
Verify the root CLI version command.

This module tests the behavior of the `fontshow --version` command,
ensuring that the application reports its version correctly.

Responsibilities
----------------
- Verify that the root CLI command exposes the package version.
- Ensure that version output is printed to standard output.

Design principles
-----------------
Version tests must isolate the CLI entry point and capture output
streams so the reported version can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and validates
the version-reporting behavior of the Fontshow command-line interface.
"""

import pytest


def test_fontshow_root_version(capsys, monkeypatch):
    """
    Verify that the root CLI version flag exits cleanly and prints a version.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Capture fixture used to inspect version output.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to override ``sys.argv`` for the CLI entry point.

    Returns
    -------
    None
    """
    from fontshow.__main__ import main

    monkeypatch.setattr("sys.argv", ["fontshow", "-V"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert out.startswith("fontshow ")
    assert "development" not in out


def test_fontshow_preflight_version(capsys, monkeypatch):
    """
    Verify that the preflight subcommand exposes its own version output.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Capture fixture used to inspect version output.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to override ``sys.argv`` for the CLI entry point.

    Returns
    -------
    None
    """
    from fontshow.__main__ import main

    monkeypatch.setattr("sys.argv", ["fontshow", "preflight", "-V"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert out.startswith("fontshow preflight ")
