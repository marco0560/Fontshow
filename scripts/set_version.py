"""Simple helper to update the `version` field in `pyproject.toml`.

Usage: `python3 scripts/set_version.py 1.2.3`
"""

import sys
from pathlib import Path
from typing import Final


def main() -> None:
    """Entry point: read CLI arg and update `pyproject.toml` in-place."""
    if len(sys.argv) < 2:
        print("Usage: set_version.py <version>")
        sys.exit(2)

    version: Final[str] = sys.argv[1]
    pyproject = Path("pyproject.toml")

    text = pyproject.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    for line in text:
        if line.strip().startswith("version ="):
            out.append(f'version = "{version}"')
        else:
            out.append(line)

    pyproject.write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"Updated pyproject.toml to version {version}")


if __name__ == "__main__":
    main()
