"""
Verify automatic dispatcher command discovery.

This module tests the top-level Fontshow dispatcher auto-discovery logic
so command registration stays aligned with modules under
``fontshow.cli`` without regressing CLI stability.

Responsibilities
----------------
- Verify the dispatcher preserves the established command order.
- Verify non-command helper modules under ``fontshow.cli`` are ignored.
- Verify newly discovered command modules are registered automatically.

Design principles
-----------------
The tests patch the discovery helpers directly so command enumeration can
be validated deterministically without touching the real package layout.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and protects
the command-discovery contract of the top-level CLI dispatcher.
"""

from __future__ import annotations

import argparse
from types import ModuleType, SimpleNamespace

import fontshow.__main__ as fontshow_main


def _find_subparsers_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction[argparse.ArgumentParser]:
    """
    Locate the dispatcher subparser action.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Top-level parser built by the Fontshow dispatcher.

    Returns
    -------
    argparse._SubParsersAction[argparse.ArgumentParser]
        Subparser action exposing the registered command parsers.

    Raises
    ------
    AssertionError
        Raised when the parser does not expose a subparser action.
    """
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    msg = "dispatcher parser must expose subcommands"
    raise AssertionError(msg)


def test_build_parser_preserves_existing_command_order() -> None:
    """
    Verify the dispatcher keeps the established visible command order.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    parser = fontshow_main.build_parser()
    subparsers_action = _find_subparsers_action(parser)

    assert list(subparsers_action.choices) == [
        "preflight",
        "dump-fonts",
        "parse-inventory",
        "validate-inventory",
        "create-catalog",
    ]


def test_iter_cli_command_specs_ignores_non_command_modules(monkeypatch) -> None:
    """
    Verify helper modules without CLI entrypoints are not registered.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace package discovery and module imports.

    Returns
    -------
    None
    """
    helper_module = ModuleType("fontshow.cli.helper")
    helper_module.VALUE = "ignored"

    valid_module = ModuleType("fontshow.cli.alpha_command")

    def build_parser(parser: argparse.ArgumentParser) -> None:
        """
        Configure the synthetic command parser used by this test.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            Parser instance configured in place.

        Returns
        -------
        None
        """
        parser.description = "Alpha command"

    def main(_args: argparse.Namespace) -> int:
        """
        Synthetic command handler used by this test.

        Parameters
        ----------
        _args : argparse.Namespace
            Parsed arguments accepted for interface compatibility.

        Returns
        -------
        int
            Stubbed success exit code.
        """
        return 0

    valid_module.build_parser = build_parser
    valid_module.main = main

    monkeypatch.setattr(
        fontshow_main.pkgutil,
        "iter_modules",
        lambda _paths: [
            SimpleNamespace(name="helper"),
            SimpleNamespace(name="alpha_command"),
        ],
    )

    def import_module(name: str) -> ModuleType:
        """
        Resolve one synthetic module by import name.

        Parameters
        ----------
        name : str
            Fully qualified module name.

        Returns
        -------
        ModuleType
            Synthetic module used by this test.
        """
        if name.endswith(".helper"):
            return helper_module
        if name.endswith(".alpha_command"):
            return valid_module
        msg = f"unexpected import: {name}"
        raise AssertionError(msg)

    monkeypatch.setattr(fontshow_main.importlib, "import_module", import_module)

    specs = fontshow_main._iter_cli_command_specs()

    assert [spec.command_name for spec in specs] == ["alpha-command"]
    assert specs[0].help_text == "Alpha command"


def test_build_parser_registers_new_discovered_command(monkeypatch) -> None:
    """
    Verify a newly discovered CLI module becomes a dispatcher subcommand.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace command discovery with a controlled result.

    Returns
    -------
    None
    """

    def register(parser: argparse.ArgumentParser) -> None:
        """
        Configure the synthetic discovered subparser.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            Parser instance configured in place.

        Returns
        -------
        None
        """
        parser.add_argument("--flag", action="store_true")
        parser.set_defaults(func=lambda _args: 0)

    monkeypatch.setattr(
        fontshow_main,
        "_iter_cli_command_specs",
        lambda: [
            fontshow_main._CliCommandSpec(
                command_name="dump-fonts",
                help_text="Extract raw font inventory",
                register=lambda parser: parser.set_defaults(func=lambda _args: 0),
            ),
            fontshow_main._CliCommandSpec(
                command_name="new-command",
                help_text="New command",
                register=register,
            ),
        ],
    )

    parser = fontshow_main.build_parser()
    subparsers_action = _find_subparsers_action(parser)

    assert "new-command" in subparsers_action.choices
    args = parser.parse_args(["new-command", "--flag"])
    assert args.flag is True
