"""
Fontshow command-line entry point.

This module implements the command-line interface entry point used when
executing Fontshow as a Python module.

Responsibilities
----------------
- Parse command-line arguments for the Fontshow CLI.
- Dispatch CLI commands to the corresponding handler functions.
- Provide consistent exit codes and error reporting for CLI operations.

Design principles
-----------------
The entry point should remain thin and deterministic: argument parsing,
command dispatch, and high-level error handling occur here, while the
actual command implementations live in the ``fontshow.cli`` package.

Architectural role
------------------
This module belongs to the **CLI interface layer** and serves as the
runtime entry point when Fontshow is executed as a module
(``python -m fontshow``).
"""

import argparse
import importlib
import pkgutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType
from typing import Any, cast

from fontshow.core.cli_utils import log_err

try:
    import fontshow.cli
    import fontshow.preflight
    from fontshow.core.logging_utils import log, log_trace_cat
except ModuleNotFoundError as e:
    missing = e.name or "<unknown>"
    log_err(f"Required import '{missing}' not available")
    sys.exit(1)

from fontshow.core.cli_utils import add_common_arguments

_CLI_HELP_TEXT = {
    "dump-fonts": "Extract raw font inventory",
    "parse-inventory": "Enrich and validate a font inventory",
    "validate-inventory": "Validate a Fontshow inventory file against the JSON schema",
    "create-catalog": "Generate output artifacts from an inventory",
}
_CLI_ORDER = {
    "dump-fonts": 0,
    "parse-inventory": 1,
    "validate-inventory": 2,
    "create-catalog": 3,
}


@dataclass(frozen=True)
class _CliCommandSpec:
    """
    Deterministic metadata for one auto-discovered CLI subcommand.

    Parameters
    ----------
    command_name : str
        Hyphenated dispatcher subcommand name derived from the module name.
    help_text : str
        Short help text rendered in the top-level dispatcher help output.
    register : Callable[[argparse.ArgumentParser], None]
        Callable that configures the subparser in place.

    Returns
    -------
    None
    """

    command_name: str
    help_text: str
    register: Callable[[argparse.ArgumentParser], None]


def _derive_command_help(command_name: str, module: ModuleType) -> str:
    """
    Resolve deterministic help text for one CLI command module.

    Parameters
    ----------
    command_name : str
        Hyphenated dispatcher subcommand name.
    module : types.ModuleType
        Imported CLI module associated with ``command_name``.

    Returns
    -------
    str
        Help text used when registering the command parser.
    """
    if command_name in _CLI_HELP_TEXT:
        return _CLI_HELP_TEXT[command_name]

    parser = argparse.ArgumentParser(add_help=False)
    build_parser = getattr(module, "build_parser", None)
    if callable(build_parser):
        build_parser(parser)
        if parser.description:
            return str(parser.description).strip()

    return command_name.replace("-", " ")


def _build_register_callback(
    module: ModuleType,
) -> Callable[[argparse.ArgumentParser], None]:
    """
    Build the parser-registration callback for one CLI module.

    Parameters
    ----------
    module : types.ModuleType
        Imported CLI module from ``fontshow.cli``.

    Returns
    -------
    Callable[[argparse.ArgumentParser], None]
        Callback that configures the command parser in place.

    Raises
    ------
    TypeError
        Raised when the module does not expose a supported CLI registration
        interface.
    """
    register_cli = getattr(module, "register_cli", None)
    if callable(register_cli):
        return cast("Callable[[argparse.ArgumentParser], None]", register_cli)

    build_parser = getattr(module, "build_parser", None)
    main = getattr(module, "main", None)
    run = getattr(module, "run", None)
    handler = main if callable(main) else run if callable(run) else None
    if not callable(build_parser) or not callable(handler):
        msg = (
            f"CLI module '{module.__name__}' must expose either register_cli(parser) "
            "or build_parser(parser) plus main(args)/run(args)"
        )
        raise TypeError(msg)

    def _register(parser: argparse.ArgumentParser) -> None:
        """
        Configure a dispatcher subparser from a discovered CLI module.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            Subparser instance to configure in place.

        Returns
        -------
        None
        """
        build_parser(parser)
        parser.set_defaults(func=handler)

    return _register


def _iter_cli_command_specs() -> list[_CliCommandSpec]:
    """
    Discover dispatcher commands exposed by the ``fontshow.cli`` package.

    Parameters
    ----------
    None

    Returns
    -------
    list[_CliCommandSpec]
        Deterministically ordered command specifications.
    """
    command_specs: list[_CliCommandSpec] = []

    for module_info in pkgutil.iter_modules(fontshow.cli.__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"fontshow.cli.{module_info.name}")
        command_name = module_info.name.replace("_", "-")
        try:
            register = _build_register_callback(module)
        except TypeError:
            continue
        help_text = _derive_command_help(command_name, module)
        command_specs.append(
            _CliCommandSpec(
                command_name=command_name,
                help_text=help_text,
                register=register,
            )
        )

    return sorted(
        command_specs,
        key=lambda spec: (_CLI_ORDER.get(spec.command_name, 999), spec.command_name),
    )


def build_parser() -> argparse.ArgumentParser:
    """
    Build the top-level Fontshow argument parser.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Parser configured with the full dispatcher command surface and
        shared global options.

    Notes
    -----
    Subcommand registration is performed eagerly so the generated help
    output reflects the complete CLI surface available in the current
    installation.
    """
    try:
        fontshow_version = version("fontshow")
    except PackageNotFoundError:
        fontshow_version = "development"

    parser = argparse.ArgumentParser(
        prog="fontshow",
        description=(
            "Fontshow – font analysis and catalog generation toolkit\n\n"
            "Typical pipeline:\n"
            "  fontshow preflight\n"
            "  fontshow dump-fonts\n"
            "  fontshow parse-inventory\n"
            "  fontshow validate-inventory\n"
            "  fontshow create-catalog"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"fontshow {fontshow_version}",
    )

    subparsers = parser.add_subparsers(
        title="Available commands",
    )

    # ------------------------------------------------------------------
    # preflight
    preflight_parser = subparsers.add_parser(
        "preflight",
        help="Run environment and dependency checks",
    )
    add_common_arguments(
        preflight_parser,
        include_output=True,
        output_default=None,
        output_help="Write preflight report to file (in addition to console output)",
    )
    fontshow.preflight.register_cli(preflight_parser)

    for command_spec in _iter_cli_command_specs():
        command_parser = subparsers.add_parser(
            command_spec.command_name,
            help=command_spec.help_text,
        )
        command_spec.register(command_parser)

    return parser


def dispatch_command(args: argparse.Namespace) -> int:
    """
    Dispatch a parsed CLI command.

    Invokes the command handler stored in ``args.func`` and converts its
    result into a deterministic process exit code. TRACE "flow" events are
    emitted for start, completion, and crash conditions.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments. Must provide a callable ``func`` attribute
        accepting ``args`` and returning either an integer-like exit code
        or ``None``.

    Returns
    -------
    int
        Process exit code:
        - 0 when the handler returns ``None`` or raises ``SystemExit(None)``,
        - ``int(result)`` when the handler returns a non-None value,
        - ``int(e.code)`` when the handler raises ``SystemExit(code)``,
        - 2 for any other unhandled exception.

    Notes
    -----
    Unexpected exceptions are intentionally converted into exit code
    ``2`` after TRACE crash logging rather than being re-raised.
    """
    log_trace_cat(
        log,
        "flow",
        "cli dispatch started",
        extra={"cmd": getattr(args, "command", None)},
    )

    try:
        result: Any = args.func(args)
        exit_code: int = int(result) if result is not None else 0

        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={"exit_code": exit_code},
        )

    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 0

        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={"exit_code": exit_code},
        )

    except Exception:  # noqa: BLE001
        log_trace_cat(
            log,
            "flow",
            "cli dispatch crashed",
            extra={},
        )
        exit_code = 2

    return exit_code


def main() -> int:
    """
    Build the top-level CLI parser, register subcommands, and run dispatch.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process exit code. Returns 0 after printing help when no subcommand
        is selected; otherwise returns the exit code produced by
        ``dispatch_command``.

    Notes
    -----
    Logging configuration is intentionally not performed here. Logging is
    handled centrally by the shared logging utilities and by test harnesses.
    The package version is resolved from installed metadata and falls back
    to ``"development"`` when the package is not installed.

    Subcommand registration is performed eagerly so the generated help
    output reflects the full CLI surface available in the current
    installation.
    """
    parser = build_parser()
    args = parser.parse_args()

    if not getattr(args, "func", None):
        parser.print_help()
        return 0

    return dispatch_command(args)


if __name__ == "__main__":
    sys.exit(main())
