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
