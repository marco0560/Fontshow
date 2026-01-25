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
