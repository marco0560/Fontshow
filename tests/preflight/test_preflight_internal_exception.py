"""
Verify internal exception handling in the preflight CLI.

This module tests the behavior of the preflight command-line interface
when a check raises an unexpected exception.

Responsibilities
----------------
- Ensure infrastructure failures produce exit code 2.
- Verify unexpected exceptions are surfaced deterministically.

Design principles
-----------------
Failure-path tests validate CLI robustness and guarantee that
unexpected exceptions are reported as infrastructure failures rather
than silently ignored.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
error-handling guarantees of the preflight CLI entry point.
"""

from argparse import Namespace

from fontshow.preflight.__main__ import _run_preflight_cli


def test_preflight_internal_exception_returns_exit_2():
    """
    If a check raises an unexpected exception, preflight must
    signal infrastructure failure (exit code 2).
    """

    def failing_run_preflight():
        msg = "internal failure"
        raise RuntimeError(msg)

    args = Namespace(output=None, quiet=True, verbose=False)

    code = _run_preflight_cli(
        args=args,
        run_preflight_fn=failing_run_preflight,
    )

    assert code == 2
