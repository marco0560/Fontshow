#!/usr/bin/env python3
"""
Render a compact human-readable coverage summary.

Parameters
----------
None

Returns
-------
int
    Process exit status compatible with CI enforcement.
"""

from __future__ import annotations

import json
from pathlib import Path

REPORT_PATH = Path(".coverage-report.json")
FAIL_UNDER = 70.0
WORST_COUNT = 5


def main() -> int:
    """
    Render compact coverage diagnostics.

    Parameters
    ----------
    None

    Returns
    -------
    int
        ``0`` when coverage satisfies the configured threshold,
        otherwise ``1``.
    """
    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    files = payload["files"]
    totals = payload["totals"]

    rows: list[tuple[str, int, int, float]] = []

    for name, data in files.items():
        summary = data["summary"]

        rows.append(
            (
                name,
                int(summary["num_statements"]),
                int(summary["missing_lines"]),
                float(summary["percent_covered"]),
            )
        )

    rows.sort(key=lambda item: (item[3], item[0]))

    selected = rows[:WORST_COUNT]

    name_width = max(
        len("Name (worst coverage files)"),
        *(len(name) for name, _, _, _ in selected),
        len("TOTAL"),
    )

    print(
        f"{'Name (worst coverage files)':<{name_width}}  "
        f"{'Stmts':>7}  {'Miss':>5}  {'Cover':>5}"
    )

    print("-" * (name_width + 23))

    for name, stmts, miss, cover in selected:
        print(f"{name:<{name_width}}  {stmts:>7}  {miss:>5}  {cover:>4.0f}%")

    print("-" * (name_width + 23))

    print(
        f"{'TOTAL':<{name_width}}  "
        f"{int(totals['num_statements']):>7}  "
        f"{int(totals['missing_lines']):>5}  "
        f"{float(totals['percent_covered']):>4.0f}%"
    )

    return 0 if float(totals["percent_covered"]) >= FAIL_UNDER else 1


if __name__ == "__main__":
    raise SystemExit(main())
