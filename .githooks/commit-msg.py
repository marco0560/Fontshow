#!python
"""
Git commit-msg hook enforcing Conventional Commit formatting.

This hook validates the first line of the commit message against a
restricted Conventional Commit format and ensures that the optional
scope belongs to a predefined list of allowed scopes.

The expected commit message format is:

    type(scope): summary

where:

- ``type`` must be one of the allowed commit types
- ``scope`` is optional but, if present, must belong to ``ALLOWED_SCOPES``
- the summary must be between 1 and 72 characters

If the message does not comply with the rules, the hook prints an
error message and aborts the commit by exiting with a non-zero status.

Notes
-----
The hook is executed automatically by Git during the ``commit-msg``
hook phase. The path to the temporary commit message file is provided
as the first command-line argument.
"""

import re
import sys
from pathlib import Path

ALLOWED_TYPES = {
    "feat",
    "fix",
    "docs",
    "perf",
    "refactor",
    "test",
    "chore",
    "style",
}
ALLOWED_SCOPES = {
    "build",
    "catalog",
    "ci",
    "cli",
    "config",
    "core",
    "decision",
    "dev",
    "diagnostics",
    "discovery",
    "docs",
    "dump",
    "git",
    "inventory",
    "latex",
    "output",
    "ontology",
    "parser",
    "planning",
    "platform",
    "schema",
    "release",
    "unicode",
    "validation",
}

msg_file = sys.argv[1]

with Path(msg_file).open(encoding="utf-8") as f:
    first_line = f.readline().strip()

pattern = re.compile(
    r"^(?P<type>feat|fix|docs|perf|refactor|test|chore|style)"
    r"(\((?P<scope>[a-z0-9._-]+)\))?"
    r"(?P<breaking>!)?: "
    r".{1,72}$"
)

match = pattern.match(first_line)
if not match:
    print("ERROR: commit message non compliant.")
    print("Expected format:")
    print("  type(scope): summary")
    print("Types admitted:")
    for s in sorted(ALLOWED_TYPES):
        print(f"  - {s}")
    sys.exit(1)

scope = match.group("scope")
if scope and scope not in ALLOWED_SCOPES:
    print(f"ERROR: scope '{scope}' not admitted.")
    print("Scopes admitted:")
    for s in sorted(ALLOWED_SCOPES):
        print(f"  - {s}")
    sys.exit(1)
