"""
Preflight subsystem package.

This package implements the preflight checking system used to verify
that the execution environment satisfies the requirements for running
Fontshow.

Responsibilities
----------------
- Execute registered environment checks.
- Provide CLI integration for the `fontshow preflight` command.
- Render human-readable reports describing check results.

Design principles
-----------------
Preflight checks are implemented as modular components that can be
registered and executed by the runner. The subsystem separates check
implementation, execution, and CLI presentation.

Architectural role
------------------
This package belongs to the **preflight subsystem** and provides the
environment validation stage used before running inventory or catalog
pipelines.
"""

from .runner import run_preflight

__all__ = [
    "run",
    "run_preflight",
]


def run(args):
    """
    CLI entrypoint for `fontshow preflight`.

    Called by argparse via:
        parser.set_defaults(func=run)

    Behavior:
    - runs the preflight checks
    - renders a human-readable report unless --quiet is set
    - returns an int exit code (0 on success)
    """
    # Reuse the preflight CLI renderer used by `python -m fontshow.preflight`
    from .__main__ import _run_preflight_cli

    return _run_preflight_cli(args=args, run_preflight_fn=run_preflight)


def register_cli(parser):
    parser.set_defaults(command="preflight", func=run)
