#!/usr/bin/env python3
"""
Replay LuaLaTeX loadability probing for benchmark measurements.

This helper reads a prepared Fontshow inventory and reruns the
inventory-side LuaLaTeX loadability probe with a selected batch size and
job count. It exists for local benchmark experiments and does not change
the normal ``fontshow dump-fonts`` command surface.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, cast

from fontshow.inventory.loadability import probe_and_persist_lualatex_loadability
from fontshow.inventory.schema_accessors import ensure_v13_lualatex_loadability


def _load_inventory(path: Path) -> dict[str, Any]:
    """
    Load an inventory JSON document.

    Parameters
    ----------
    path : pathlib.Path
        Inventory path to read.

    Returns
    -------
    dict[str, Any]
        Parsed inventory payload.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = "inventory root must be a JSON object"
        raise SystemExit(msg)
    return cast("dict[str, Any]", payload)


def _validation_metadata(inventory: dict[str, Any]) -> MutableMapping[str, Any]:
    """
    Return the mutable LuaLaTeX validation metadata block.

    Parameters
    ----------
    inventory : dict[str, Any]
        Parsed inventory payload.

    Returns
    -------
    dict[str, Any]
        Mutable ``metadata.validation.lualatex`` mapping.

    Raises
    ------
    SystemExit
        Raised when the inventory does not contain the expected metadata
        structure.
    """
    metadata = inventory.get("metadata")
    if not isinstance(metadata, dict):
        msg = "inventory metadata must be an object"
        raise SystemExit(msg)
    validation = metadata.get("validation")
    if not isinstance(validation, dict):
        msg = "inventory metadata.validation must be an object"
        raise SystemExit(msg)
    lualatex = validation.get("lualatex")
    if not isinstance(lualatex, MutableMapping):
        msg = "inventory metadata.validation.lualatex must be an object"
        raise SystemExit(msg)
    return lualatex


def _inventory_fonts(inventory: dict[str, Any]) -> list[MutableMapping[str, Any]]:
    """
    Return the mutable inventory font list.

    Parameters
    ----------
    inventory : dict[str, Any]
        Parsed inventory payload.

    Returns
    -------
    list[dict[str, Any]]
        Mutable font entries.

    Raises
    ------
    SystemExit
        Raised when ``fonts`` is absent or contains non-object entries.
    """
    fonts = inventory.get("fonts")
    if not isinstance(fonts, list) or not all(
        isinstance(font, MutableMapping) for font in fonts
    ):
        msg = "inventory fonts must be a list of objects"
        raise SystemExit(msg)
    return cast("list[MutableMapping[str, Any]]", fonts)


def _reset_lualatex_state(
    fonts: list[MutableMapping[str, Any]],
    validation_metadata: MutableMapping[str, Any],
) -> None:
    """
    Reset persisted loadability fields before a benchmark replay.

    Parameters
    ----------
    fonts : list[dict[str, Any]]
        Mutable inventory font entries.
    validation_metadata : dict[str, Any]
        Mutable inventory-level LuaLaTeX validation metadata.

    Returns
    -------
    None
    """
    validation_metadata["attempted"] = False
    for font in fonts:
        lualatex = ensure_v13_lualatex_loadability(font)
        lualatex.update(
            {
                "attempted": False,
                "loadable": None,
                "reason": None,
                "runtime_fingerprint": None,
                "probe_input": None,
            }
        )


def run_probe(
    inventory_path: Path,
    output_path: Path,
    *,
    batch_size: int,
    jobs: int,
) -> int:
    """
    Execute one loadability probe replay.

    Parameters
    ----------
    inventory_path : pathlib.Path
        Prepared inventory JSON path.
    output_path : pathlib.Path
        Path where the replayed inventory should be written.
    batch_size : int
        Maximum number of fonts per LuaLaTeX batch.
    jobs : int
        Maximum number of candidate chunks to probe concurrently.

    Returns
    -------
    int
        Process-style exit code.
    """
    inventory = _load_inventory(inventory_path)
    fonts = _inventory_fonts(inventory)
    validation_metadata = _validation_metadata(inventory)
    _reset_lualatex_state(fonts, validation_metadata)

    probe_and_persist_lualatex_loadability(
        fonts,
        validation_metadata=validation_metadata,
        batch_size=batch_size,
        jobs=jobs,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Configured parser for the benchmark replay helper.
    """
    parser = argparse.ArgumentParser(
        description="Replay LuaLaTeX loadability probing for benchmarks.",
    )
    parser.add_argument("inventory", type=Path, help="Prepared inventory JSON path")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON path")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Maximum fonts per LuaLaTeX batch",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Maximum candidate chunks to probe concurrently",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Execute the benchmark replay helper.

    Parameters
    ----------
    argv : list[str] or None, optional
        Optional argument vector. ``None`` reads from ``sys.argv``.

    Returns
    -------
    int
        Process exit code.
    """
    args = build_parser().parse_args(argv)
    return run_probe(
        args.inventory,
        args.output,
        batch_size=args.batch_size,
        jobs=args.jobs,
    )


if __name__ == "__main__":
    raise SystemExit(main())
