"""
Verify Bash completion generation.

This module tests the developer-facing Bash completion tooling to keep
the checked-in completion script synchronized with the current argparse
dispatcher.

Responsibilities
----------------
- Verify command coverage for the dispatcher completion spec.
- Verify option coverage for each registered subcommand.
- Verify file-path completion metadata for path-like arguments.
- Ensure the checked-in Bash script matches the generated output.

Design principles
-----------------
The tests validate generated metadata and rendered artifacts without
executing an interactive shell, keeping the suite deterministic and
environment-independent.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and protects
developer tooling derived from the CLI contract.
"""

import argparse
from pathlib import Path

from fontshow.cli.bash_completion import build_completion_spec, render_bash_completion
from scripts.generate_bash_completion import (
    build_parser,
    main as generate_bash_completion_main,
)


def test_completion_spec_exposes_registered_commands() -> None:
    """
    Verify that the completion spec covers all dispatcher subcommands.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    spec = build_completion_spec()

    assert spec["commands"] == [
        "create-catalog",
        "dump-fonts",
        "parse-inventory",
        "preflight",
        "validate-inventory",
    ]


def test_completion_spec_tracks_command_options() -> None:
    """
    Verify per-command option coverage in the completion spec.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    spec = build_completion_spec()

    assert spec["command_specs"]["preflight"]["options"] == [
        "--help",
        "--output",
        "--quiet",
        "--verbose",
        "--version",
        "-V",
        "-h",
        "-o",
        "-q",
        "-v",
    ]
    assert spec["command_specs"]["dump-fonts"]["options"] == [
        "--cache-dir",
        "--help",
        "--include-fc-charset",
        "--no-cache",
        "--no-loadability",
        "--output",
        "--quiet",
        "--verbose",
        "--version",
        "-V",
        "-c",
        "-h",
        "-i",
        "-n",
        "-o",
        "-q",
        "-v",
    ]
    assert spec["command_specs"]["parse-inventory"]["options"] == [
        "--help",
        "--infer-level",
        "--list-missing-language-coverage",
        "--output",
        "--quiet",
        "--strict-bcp47",
        "--validate-inventory",
        "--verbose",
        "--version",
        "-I",
        "-V",
        "-h",
        "-i",
        "-o",
        "-q",
        "-s",
        "-v",
    ]
    assert spec["command_specs"]["validate-inventory"]["options"] == [
        "--help",
        "--quiet",
        "--verbose",
        "--version",
        "-V",
        "-h",
        "-q",
        "-v",
    ]
    assert spec["command_specs"]["create-catalog"]["options"] == [
        "--catalog-detail",
        "--help",
        "--inventory",
        "--list-test-fonts",
        "--number",
        "--output",
        "--quiet",
        "--test",
        "--test-font",
        "--verbose",
        "--version",
        "-T",
        "-V",
        "-h",
        "-i",
        "-l",
        "-n",
        "-o",
        "-q",
        "-t",
        "-v",
    ]


def test_completion_spec_marks_path_arguments() -> None:
    """
    Verify that path-oriented arguments are marked for file completion.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    spec = build_completion_spec()

    assert spec["command_specs"]["preflight"]["path_options"] == ["--output", "-o"]
    assert spec["command_specs"]["preflight"]["positional_paths"] is False

    assert spec["command_specs"]["dump-fonts"]["path_options"] == [
        "--cache-dir",
        "--output",
        "-c",
        "-o",
    ]
    assert spec["command_specs"]["dump-fonts"]["positional_paths"] is False

    assert spec["command_specs"]["parse-inventory"]["path_options"] == [
        "--output",
        "-o",
    ]
    assert spec["command_specs"]["parse-inventory"]["positional_paths"] is True

    assert spec["command_specs"]["validate-inventory"]["path_options"] == []
    assert spec["command_specs"]["validate-inventory"]["positional_paths"] is True

    assert spec["command_specs"]["create-catalog"]["path_options"] == [
        "--inventory",
        "--output",
        "-i",
        "-o",
    ]
    assert spec["command_specs"]["create-catalog"]["positional_paths"] is False


def test_checked_in_completion_script_matches_generated_output() -> None:
    """
    Verify that the checked-in Bash script matches the generator output.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected = render_bash_completion()
    actual = Path("scripts/completions/fontshow.bash").read_text(encoding="utf-8")

    assert actual == expected


def test_generate_bash_completion_help_is_explicit(capsys) -> None:
    """
    Verify that the completion generator exposes a readable help screen.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Fixture used to capture argparse help output.

    Returns
    -------
    None
    """
    try:
        generate_bash_completion_main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        msg = "--help must exit through argparse"
        raise AssertionError(msg)

    captured = capsys.readouterr()
    assert "Generate the Fontshow Bash completion script." in captured.out
    assert "--stdout" in captured.out
    assert "--output" in captured.out
    assert "Examples:" in captured.out


def test_generate_bash_completion_script_has_python_shebang() -> None:
    """
    Verify that the generator script is directly executable as Python.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    first_line = (
        Path("scripts/generate_bash_completion.py")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert first_line == "#!/usr/bin/env python3"


def test_generate_bash_completion_parser_uses_script_prog_name() -> None:
    """
    Verify that the completion generator advertises its own script name.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    parser = build_parser()

    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "generate_bash_completion.py"
