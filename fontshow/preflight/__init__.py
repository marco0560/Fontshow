from .runner import run_preflight

__all__ = [
    "run",
    "run_preflight",
]


def run(args):
    """
    CLI entrypoint for `fontshow preflight`.

    This function is called by argparse via:
        parser.set_defaults(func=run)

    It must:
    - return an int exit code
    - NOT print directly
    - rely on logging for messages
    """
    return run_preflight(args)


def register_cli(parser):
    parser.set_defaults(command="preflight", func=run)
