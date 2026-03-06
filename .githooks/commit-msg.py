#!python
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
