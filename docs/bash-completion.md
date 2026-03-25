# Bash Completion

Fontshow ships a generated Bash completion script for the dispatcher CLI.

The checked-in artifact lives at:

```bash
scripts/completions/fontshow.bash
```

It is generated from the current `argparse` dispatcher definition, so
the completion surface tracks the registered commands and options.

## Supported completion

The script provides:

- top-level subcommand completion for `fontshow <TAB>`
- per-command flag completion, for example `fontshow parse-inventory <TAB>`
- file path completion for path-like arguments such as:
  - `--output`
  - `--inventory`
  - `--cache-dir`
  - positional inventory file paths

The current script targets Bash only.
Zsh and Fish are intentionally out of scope for this issue.

## Local usage

From the repository root:

```bash
source scripts/completions/fontshow.bash
```

This registers completion for the `fontshow` command in the current shell
session without requiring Fontshow to be installed as a package.

## Optional user install

To enable completion for future Bash sessions, copy or symlink the script
into a completion directory used by your local shell configuration.
Typical setups include:

- sourcing it from `~/.bashrc`
- placing it in a user-level Bash completion directory if your system
  configuration loads one automatically

The repository does not assume a specific system-wide installation path.

## Regeneration

If the CLI surface changes, regenerate the script from the repository
virtual environment:

```bash
source .venv/bin/activate
python scripts/generate_bash_completion.py
```

The generated file should remain identical when no CLI changes were made.

## Related documentation

- [CLI overview](cli.md)
- [Development scripts](scripts.md)
