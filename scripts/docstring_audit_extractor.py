#!/usr/bin/env python3
"""
Docstring audit extractor.

This tool extracts Python functions and classes from a file or directory
and emits them in deterministic batches suitable for documentation audits.

Objects can be filtered according to docstring conditions:

    --missing       objects without docstring
    --nonstandard   objects with non-NumPy style docstrings
                    or missing exception documentation
    --all           all objects

Nested functions, async functions, and classes are included.

The output contains exact source fragments and an automatically generated
OLD patch block to simplify docstring patch creation.

The script is designed for deterministic behavior and reproducible output
to support repository-wide documentation audits.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

type TargetNode = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
type SelectableNode = ast.Module | TargetNode

BATCH_SIZE = 8

NUMPY_SECTIONS = {
    "Parameters",
    "Returns",
    "Yields",
    "Raises",
    "Notes",
    "Examples",
    "Attributes",
}

IGNORED_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
}


def is_numpy_style(doc: str | None) -> bool:
    """
    Determine whether a docstring resembles NumPy style.

    Parameters
    ----------
    doc : str or None
        Docstring content.

    Returns
    -------
    bool
        True if a NumPy-style section header is detected.
    """
    if not doc:
        return False

    lines = doc.splitlines()

    for i, line in enumerate(lines[:-1]):
        if line.strip() in NUMPY_SECTIONS:
            underline = lines[i + 1].strip()
            if re.fullmatch(r"-{3,}", underline):
                return True

    return False


def has_raises_section(doc: str | None) -> bool:
    """
    Check whether a docstring contains a Raises section.

    Parameters
    ----------
    doc : str or None

    Returns
    -------
    bool
    """
    if not doc:
        return False

    return "Raises" in doc


def function_raises_exception(node: ast.AST) -> bool:
    """
    Detect whether a function contains a raise statement.

    Parameters
    ----------
    node : ast.AST

    Returns
    -------
    bool
    """
    return any(isinstance(sub, ast.Raise) for sub in ast.walk(node))


def build_parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    """
    Build a mapping from AST node identifiers to their parent nodes.

    Parameters
    ----------
    tree : ast.AST
        Root of the abstract syntax tree to traverse.

    Returns
    -------
    dict[int, ast.AST]
        Mapping from ``id(child_node)`` to its corresponding parent node.
    """
    parents: dict[int, ast.AST] = {}

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    return parents


def build_qualname(node: TargetNode, parents: dict[int, ast.AST]) -> str:
    """
    Construct the qualified name of a function or class node.

    The qualified name is built by walking up the AST parent chain and
    collecting enclosing class and function names.

    Parameters
    ----------
    node : ast.AST
        AST node representing a function or class definition.
    parents : dict[int, ast.AST]
        Mapping of node identifiers to their parent nodes.

    Returns
    -------
    str
        Fully qualified name using ``"."`` as the separator.
    """
    parts: list[str] = [node.name]

    current: ast.AST = node

    while id(current) in parents:
        current = parents[id(current)]

        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            parts.append(current.name)

    parts.reverse()

    return ".".join(parts)


def iter_targets(tree: ast.AST) -> Iterator[TargetNode]:
    """
    Yield function and class definition nodes in deterministic order.

    Parameters
    ----------
    tree : ast.AST
        Root of the abstract syntax tree to inspect.

    Yields
    ------
    ast.AST
        Function or class definition nodes sorted by source location.
    """
    nodes: list[TargetNode] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes.append(node)

    nodes.sort(key=lambda n: (n.lineno, getattr(n, "col_offset", 0)))

    yield from nodes


def should_select(
    node: SelectableNode, doc: str | None, args: argparse.Namespace
) -> bool:
    """
    Determine whether a node should be selected for docstring auditing.

    The selection logic depends on the command-line flags provided:

    * ``--all`` selects every node.
    * ``--missing`` selects nodes whose docstring is missing.
    * ``--nonstandard`` selects nodes whose docstring is present but does not
      follow NumPy style, or functions that raise exceptions but do not
      document them in a ``Raises`` section.

    NumPy-style validation is applied only to functions, asynchronous
    functions, and classes. Module docstrings are excluded from this
    validation because module documentation typically follows narrative
    documentation conventions rather than NumPy-style API documentation.

    Parameters
    ----------
    node : ast.AST
        AST node representing a module, function, asynchronous function,
        or class definition.
    doc : str or None
        Extracted docstring for the node, if present.
    args : argparse.Namespace
        Parsed command-line arguments controlling selection behavior.

    Returns
    -------
    bool
        ``True`` if the node should be included in the audit output,
        otherwise ``False``.
    """
    if args.all:
        return True

    if args.missing and not doc:
        return True

    if args.nonstandard:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if doc and not is_numpy_style(doc):
                return True

            return (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and function_raises_exception(node)
                and not has_raises_section(doc)
            )

        return False

    return False


def extract_targets(path: Path, args: argparse.Namespace) -> Iterator[dict]:
    """
    Extract audit targets from a Python source file.

    The function parses the file into an abstract syntax tree and yields
    objects that match the audit selection criteria. Targets may include
    the module itself, functions, asynchronous functions, and classes.

    Module-level targets are emitted using the synthetic qualified name
    ``"<module>"``.

    Parameters
    ----------
    path : pathlib.Path
        Path to the Python source file to analyze.
    args : argparse.Namespace
        Parsed command-line arguments controlling selection criteria.

    Yields
    ------
    dict
        Dictionaries describing selected objects. Each dictionary contains:

        - ``file``: source file path
        - ``qualname``: qualified name of the object (``"<module>"`` for modules)
        - ``lineno`` / ``end_lineno``: source line span
        - ``docstring``: extracted docstring or ``None``
        - ``code``: source code fragment corresponding to the object.
    """
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    tree = ast.parse(source)
    parents = build_parent_map(tree)

    # --- module docstring audit ---
    module_doc = ast.get_docstring(tree)

    if should_select(tree, module_doc, args):
        yield {
            "file": str(path),
            "qualname": "<module>",
            "lineno": 1,
            "end_lineno": len(lines),
            "docstring": module_doc,
            "code": source,
        }

    for node in iter_targets(tree):
        doc = ast.get_docstring(node)

        if not should_select(node, doc, args):
            continue

        assert node.end_lineno is not None
        start = node.lineno - 1
        end = node.end_lineno

        qualname = build_qualname(node, parents)

        code = "\n".join(lines[start:end])

        yield {
            "file": str(path),
            "qualname": qualname,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "docstring": doc,
            "code": code,
        }


def iter_python_files(target: str) -> Iterator[Path]:
    """
    Yield Python source files from the given target path.

    If the target is a file, that file is yielded directly. If it is a
    directory, Python files are discovered recursively while skipping
    directories listed in ``IGNORED_DIRS``.

    Parameters
    ----------
    target : str
        Path to a Python file or directory containing Python sources.

    Yields
    ------
    pathlib.Path
        Python source files in deterministic sorted order.
    """
    p = Path(target)

    if p.is_file():
        yield p
        return

    files = []

    for path in p.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)

    yield from sorted(files)


def emit_batches(path: str, args: argparse.Namespace) -> None:
    """
    Emit extracted audit targets in fixed-size batches.

    This function scans Python files under the provided path, extracts
    functions and classes matching the selection criteria, and prints
    them in formatted batches suitable for external docstring audit tools.

    Parameters
    ----------
    path : str
        Path to a Python file or directory to analyze.
    args : argparse.Namespace
        Parsed command-line arguments controlling selection behavior.

    Returns
    -------
    None
    """
    batch: list[str] = []
    list_entries: list[str] = []

    for file in iter_python_files(path):
        for item in extract_targets(file, args):
            if args.list:
                if item["qualname"] == "<module>":
                    entry = item["file"]
                else:
                    entry = f"{item['file']}::{item['qualname']}"

                list_entries.append(entry)
                continue

            entry = (
                f"FILE: {item['file']}\n"
                f"TARGET: {item['qualname']}\n"
                f"LINES: {item['lineno']}-{item['end_lineno']}\n\n"
                f"CODE:\n{item['code']}\n\n"
                f"OLD:\n```python\n{item['code']}\n```"
            )

            batch.append(entry)

            if len(batch) == BATCH_SIZE:
                print("\n===== BATCH =====\n")
                print("\n\n---\n\n".join(batch))
                batch = []

    if args.list:
        for entry in sorted(list_entries):
            print(entry)
        return

    if batch:
        print("\n===== BATCH =====\n")
        print("\n\n---\n\n".join(batch))


def main() -> None:
    """
    Run the command-line interface for the docstring audit extractor.

    This entry point parses command-line arguments, determines the
    selection criteria for objects to audit, and emits the extracted
    targets in batches.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Raised by argument parsing on invalid CLI usage.
    """
    parser = argparse.ArgumentParser(
        description="Extract functions/classes for docstring audit."
    )

    parser.add_argument("path", help="File or directory to analyze")

    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--nonstandard", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List matching objects without emitting code batches",
    )
    args = parser.parse_args()

    if not (args.missing or args.nonstandard or args.all):
        args.all = True

    emit_batches(args.path, args)


if __name__ == "__main__":
    main()
