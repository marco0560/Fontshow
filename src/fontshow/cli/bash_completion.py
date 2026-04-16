"""
Bash completion generation for the Fontshow dispatcher.

This module derives a Bash completion script from the current argparse
dispatcher definition so completion data remains synchronized with the
CLI surface.

Responsibilities
----------------
- Inspect the top-level Fontshow argparse parser.
- Extract subcommands and option strings deterministically.
- Mark arguments that should use file path completion.
- Render a static Bash completion script from the extracted metadata.

Design principles
-----------------
The generated script is deterministic and dependency-free at runtime.
Fontshow itself does not depend on shell-completion libraries; instead,
developer tooling materializes a checked-in script from parser metadata.

Architectural role
------------------
This module belongs to the **CLI interface layer** and supports
developer-facing completion tooling derived from the dispatcher
contract.
"""

from __future__ import annotations

import argparse
from typing import TypedDict

from fontshow.__main__ import build_parser

PATH_DESTINATIONS = frozenset(
    {
        "cache_dir",
        "input",
        "inventory",
        "output",
        "path",
        "paths",
    }
)
_MISSING_SUBPARSERS_MESSAGE = "Fontshow dispatcher parser does not define subcommands"


class CompletionCommandSpec(TypedDict):
    """
    Structured completion metadata for a single CLI command.

    Attributes
    ----------
    options : list[str]
        Sorted option strings exposed by the command parser.
    path_options : list[str]
        Subset of ``options`` whose values should complete as file
        system paths.
    positional_paths : bool
        Whether the command accepts a positional path argument.
    """

    options: list[str]
    path_options: list[str]
    positional_paths: bool


class CompletionSpec(TypedDict):
    """
    Structured completion metadata for the full Fontshow dispatcher.

    Attributes
    ----------
    commands : list[str]
        Sorted registered dispatcher subcommands.
    global_options : list[str]
        Sorted top-level dispatcher options available before a
        subcommand is selected.
    command_specs : dict[str, CompletionCommandSpec]
        Per-command completion metadata keyed by subcommand name.
    """

    commands: list[str]
    global_options: list[str]
    command_specs: dict[str, CompletionCommandSpec]


def _find_subparsers_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction[argparse.ArgumentParser]:
    """
    Locate the argparse subparser action from the dispatcher parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Top-level Fontshow dispatcher parser.

    Returns
    -------
    argparse._SubParsersAction[argparse.ArgumentParser]
        Subparser action exposing the registered command parsers.

    Raises
    ------
    RuntimeError
        Raised when the parser does not expose a subparser action.
    """
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    message = _MISSING_SUBPARSERS_MESSAGE
    raise RuntimeError(message)


def _collect_option_strings(parser: argparse.ArgumentParser) -> list[str]:
    """
    Collect parser option strings in deterministic order.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser whose optional arguments should be enumerated.

    Returns
    -------
    list[str]
        Sorted unique option strings, for example ``['--help', '-h']``.
    """
    options = {
        option
        for action in parser._actions
        for option in action.option_strings
        if option.startswith("-")
    }
    return sorted(options)


def _collect_path_options(parser: argparse.ArgumentParser) -> list[str]:
    """
    Collect option strings that should trigger file path completion.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser whose path-like option arguments should be enumerated.

    Returns
    -------
    list[str]
        Sorted unique option strings that accept filesystem paths.

    Notes
    -----
    The dispatcher currently exposes one path-like option
    (``--inventory``) whose argparse type is ``str`` rather than
    ``pathlib.Path``. The destination-name allowlist preserves correct
    completion semantics without changing CLI behavior.
    """
    options = {
        option
        for action in parser._actions
        if action.dest in PATH_DESTINATIONS
        for option in action.option_strings
        if option.startswith("-")
    }
    return sorted(options)


def _has_positional_path_argument(parser: argparse.ArgumentParser) -> bool:
    """
    Determine whether a parser accepts a positional file path argument.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser to inspect.

    Returns
    -------
    bool
        ``True`` when the parser exposes a positional path-like
        argument, otherwise ``False``.
    """
    return any(
        not action.option_strings and action.dest in PATH_DESTINATIONS
        for action in parser._actions
    )


def build_completion_spec() -> CompletionSpec:
    """
    Build the Bash completion metadata for the dispatcher.

    Parameters
    ----------
    None

    Returns
    -------
    CompletionSpec
        Deterministic description of commands, global options, and
        per-command completion requirements.
    """
    parser = build_parser()
    subparsers_action = _find_subparsers_action(parser)

    command_specs: dict[str, CompletionCommandSpec] = {}
    commands = sorted(subparsers_action.choices)

    for command in commands:
        command_parser = subparsers_action.choices[command]
        command_specs[command] = {
            "options": _collect_option_strings(command_parser),
            "path_options": _collect_path_options(command_parser),
            "positional_paths": _has_positional_path_argument(command_parser),
        }

    return {
        "commands": commands,
        "global_options": _collect_option_strings(parser),
        "command_specs": command_specs,
    }


def _render_shell_list(values: list[str]) -> str:
    """
    Render a deterministic space-separated shell token list.

    Parameters
    ----------
    values : list[str]
        Tokens to include in the shell list.

    Returns
    -------
    str
        Single string suitable for use inside a double-quoted shell
        variable assignment.
    """
    return " ".join(values)


def render_bash_completion(spec: CompletionSpec | None = None) -> str:
    """
    Render the Fontshow Bash completion script.

    Parameters
    ----------
    spec : CompletionSpec | None, optional
        Precomputed completion metadata. When omitted, the spec is
        derived from the current dispatcher definition.

    Returns
    -------
    str
        Full Bash completion script content.
    """
    if spec is None:
        spec = build_completion_spec()

    lines = [
        "# shellcheck shell=bash",
        "# Generated by scripts/generate_bash_completion.py. Do not edit manually.",
        "",
        f'_FONTSHOW_COMMANDS="{_render_shell_list(spec["commands"])}"',
        f'_FONTSHOW_GLOBAL_OPTIONS="{_render_shell_list(spec["global_options"])}"',
        "",
    ]

    for command in spec["commands"]:
        command_key = command.upper().replace("-", "_")
        command_spec = spec["command_specs"][command]
        lines.extend(
            [
                f'_FONTSHOW_OPTIONS_{command_key}="'
                f'{_render_shell_list(command_spec["options"])}"',
                f'_FONTSHOW_PATH_OPTIONS_{command_key}="'
                f'{_render_shell_list(command_spec["path_options"])}"',
                f"_FONTSHOW_POSITIONAL_PATH_{command_key}="
                f'{"1" if command_spec["positional_paths"] else "0"}',
                "",
            ]
        )

    lines.extend(
        [
            "_fontshow_contains_word() {",
            '    local needle="$1"',
            "    shift",
            "    local item",
            '    for item in "$@"; do',
            '        if [[ "$item" == "$needle" ]]; then',
            "            return 0",
            "        fi",
            "    done",
            "    return 1",
            "}",
            "",
            "_fontshow_complete_files() {",
            '    COMPREPLY=( $(compgen -f -- "$1") )',
            "}",
            "",
            "_fontshow_complete() {",
            "    local cur prev command command_key options path_options positional_paths",
            '    cur="${COMP_WORDS[COMP_CWORD]}"',
            '    prev="${COMP_WORDS[COMP_CWORD-1]}"',
            '    command="${COMP_WORDS[1]}"',
            "",
            "    if (( COMP_CWORD == 1 )); then",
            '        COMPREPLY=( $(compgen -W "${_FONTSHOW_COMMANDS} ${_FONTSHOW_GLOBAL_OPTIONS}" -- "$cur") )',
            "        return 0",
            "    fi",
            "",
            '    if [[ -z "$command" ]]; then',
            "        return 0",
            "    fi",
            "",
            '    command_key="${command^^}"',
            '    command_key="${command_key//-/_}"',
            '    eval "options=\\${_FONTSHOW_OPTIONS_${command_key}}"',
            '    eval "path_options=\\${_FONTSHOW_PATH_OPTIONS_${command_key}}"',
            '    eval "positional_paths=\\${_FONTSHOW_POSITIONAL_PATH_${command_key}}"',
            "",
            '    if _fontshow_contains_word "$prev" $path_options; then',
            '        _fontshow_complete_files "$cur"',
            "        return 0",
            "    fi",
            "",
            '    if [[ "$cur" == -* ]]; then',
            '        COMPREPLY=( $(compgen -W "${options} ${_FONTSHOW_GLOBAL_OPTIONS}" -- "$cur") )',
            "        return 0",
            "    fi",
            "",
            '    if [[ "$positional_paths" == "1" ]]; then',
            '        _fontshow_complete_files "$cur"',
            "        return 0",
            "    fi",
            "",
            "    COMPREPLY=()",
            "}",
            "",
            "complete -F _fontshow_complete fontshow",
            "",
        ]
    )

    return "\n".join(lines)
