#!/usr/bin/env python3
"""Parse `fc-list -f '%{file}:%{family}\n'` and print the first N file→family pairs.

Usage:
    python3 scripts/parse_fc_list.py [N]

If N is omitted, prints 10 pairs.
"""

import subprocess
import sys


def parse_fc_list(limit: int = 10) -> int:
    """Parse `fc-list` and print the first `limit` file→family pairs.

    Returns 0 on success, non-zero on error. Useful as a quick parser test
    when tuning the main `crea_catalogo` parser.
    """
    cmd: list[str] = ["fc-list", "-f", "%{file}:%{family}\n"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("Error: 'fc-list' not found. Install fontconfig (package `fontconfig`).")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"Error running fc-list: {e}")
        return 1

    lines = proc.stdout.splitlines()
    count = 0
    for line in lines:
        if ":" not in line:
            continue
        file_part, family_part = line.split(":", 1)
        file_part = file_part.strip()
        # family_part can contain comma-separated family names; take the first
        first_family = family_part.split(",")[0].strip()
        print(f"{count+1}. file={file_part}\n   family={first_family}\n")
        count += 1
        if count >= limit:
            break
    return 0


if __name__ == "__main__":
    n = 10
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            print("Invalid number, using default 10.")
    sys.exit(parse_fc_list(n))
