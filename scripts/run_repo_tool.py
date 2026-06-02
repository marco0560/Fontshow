#!/usr/bin/env python3
"""Run repository tools with non-repository cache and temp state.

Responsibilities
----------------
- Route sanctioned local tooling through one deterministic environment.
- Keep tool-created cache and temporary directories outside the repository.
- Fail before execution if the chosen tool-state root resolves inside the
  checkout.

Design principles
-----------------
Tool state is disposable and belongs under the current user's native temporary
directory, not under the repository cleanup surface.

Architectural role
------------------
This module belongs to the **developer tooling layer** shared by Git hooks,
bootstrap validation, and repo-local aliases.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
GIT_EXE = shutil.which("git")
SUPPORTED_TOOLS: dict[str, str | None] = {
    "coverage": "coverage",
    "mypy": "mypy",
    "pre-commit": "pre_commit",
    "pre-commit-noncode": "pre_commit",
    "pytest": "pytest",
    "python": None,
    "ruff": "ruff",
}


class ToolStateInsideRepositoryError(RuntimeError):
    """Raised when the selected tool-state root would live inside the repo."""

    def __init__(self, path: Path) -> None:
        """
        Initialize the error.

        Parameters
        ----------
        path : pathlib.Path
            Resolved tool-state path that would be created inside the
            repository.

        Returns
        -------
        None
        """

        super().__init__(f"Refusing to create tool state inside repository: {path}")


class UnsupportedToolError(ValueError):
    """Raised when a tool is not supported by the repository wrapper."""

    def __init__(self, tool: str, supported_tools: tuple[str, ...]) -> None:
        """
        Initialize the error.

        Parameters
        ----------
        tool : str
            Unsupported tool name.
        supported_tools : tuple[str, ...]
            Supported tool names.

        Returns
        -------
        None
        """

        supported = ", ".join(supported_tools)
        super().__init__(f"Unsupported tool {tool!r}. Supported tools: {supported}")


def path_is_inside(path: Path, parent: Path) -> bool:
    """
    Return whether ``path`` resolves inside ``parent``.

    Parameters
    ----------
    path : pathlib.Path
        Candidate path to test.
    parent : pathlib.Path
        Parent directory that must not contain the candidate.

    Returns
    -------
    bool
        ``True`` when the resolved candidate is equal to or below the resolved
        parent path.
    """

    resolved_path = path.resolve()
    resolved_parent = parent.resolve()
    return resolved_path == resolved_parent or resolved_parent in resolved_path.parents


def tool_state_root(repo_root: Path, *, temp_root: Path | None = None) -> Path:
    """
    Return the per-checkout tool-state root under the current user temp dir.

    Parameters
    ----------
    repo_root : pathlib.Path
        Repository root for the current checkout.
    temp_root : pathlib.Path | None, optional
        Override for tests. When omitted, ``tempfile.gettempdir()`` is used.

    Returns
    -------
    pathlib.Path
        Tool-state root outside ``repo_root``.

    Raises
    ------
    RuntimeError
        If the native temporary directory resolves inside the repository.
    """

    root = Path(temp_root) if temp_root is not None else Path(tempfile.gettempdir())
    if path_is_inside(root, repo_root):
        raise ToolStateInsideRepositoryError(root.resolve())

    normalized = str(repo_root.resolve())
    if os.name == "nt":
        normalized = normalized.lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return root / "fontshow-tool-state" / f"{repo_root.name}-{digest}"


def tool_environment(
    base_env: Mapping[str, str], *, state_root: Path
) -> dict[str, str]:
    """
    Build an environment that redirects tool state outside the repository.

    Parameters
    ----------
    base_env : collections.abc.Mapping[str, str]
        Baseline process environment.
    state_root : pathlib.Path
        Non-repository root for cache and temporary state.

    Returns
    -------
    dict[str, str]
        Environment variables for the child tool process.
    """

    tmp_root = state_root / "tmp"
    env = dict(base_env)
    env["FONTSHOW_TOOL_STATE_ROOT"] = str(state_root)
    env["COVERAGE_FILE"] = str(state_root / "coverage" / ".coverage")
    env["MYPY_CACHE_DIR"] = str(state_root / "mypy")
    env["PRE_COMMIT_HOME"] = str(state_root / "pre-commit")
    env["RUFF_CACHE_DIR"] = str(state_root / "ruff")
    env["TEMP"] = str(tmp_root)
    env["TMP"] = str(tmp_root)
    env["TMPDIR"] = str(tmp_root)
    return env


def create_pytest_basetemp(state_root: Path) -> Path:
    """
    Reserve a unique pytest base temporary directory path.

    Parameters
    ----------
    state_root : pathlib.Path
        Non-repository root for cache and temporary state.

    Returns
    -------
    pathlib.Path
        Unique non-existing pytest base temporary directory path below
        ``state_root / "tmp"``.

    Notes
    -----
    Pytest removes ``--basetemp`` at session start. Reusing one stable path can
    make future validation runs fail on Windows when an earlier session leaves
    a locked directory behind. Returning a path that does not exist yet also
    avoids forcing pytest to delete a directory created by this wrapper.
    """

    tmp_root = state_root / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    while True:
        candidate = tmp_root / f"pytest-{uuid.uuid4().hex}"
        if not candidate.exists():
            return candidate


def resolve_python_sibling_executable(name: str, *, python: str) -> str:
    """
    Resolve a console-script executable next to the selected Python interpreter.

    Parameters
    ----------
    name : str
        Console-script executable name to resolve.
    python : str
        Python interpreter whose environment should own the executable.

    Returns
    -------
    str
        Resolved executable path, preferring the interpreter sibling and
        falling back to ``PATH`` lookup or the raw name.
    """

    python_path = Path(python)
    sibling_candidates = (
        python_path.with_name(name),
        python_path.with_name(f"{name}.exe"),
    )
    for candidate in sibling_candidates:
        if candidate.is_file():
            return str(candidate)
    resolved = shutil.which(name)
    if resolved is not None:
        return resolved
    return name


def build_tool_argv(
    tool: str,
    tool_args: Sequence[str],
    *,
    state_root: Path,
    python: str,
    pytest_basetemp: Path | None = None,
) -> tuple[str, ...]:
    """
    Build the tool command line with explicit non-repository state arguments.

    Parameters
    ----------
    tool : str
        Supported tool name.
    tool_args : collections.abc.Sequence[str]
        Arguments to pass to the selected tool.
    state_root : pathlib.Path
        Non-repository root for cache and temporary state.
    python : str
        Python executable used to invoke module-backed tools.
    pytest_basetemp : pathlib.Path | None, optional
        Explicit pytest base temporary directory. When omitted for pytest, a
        unique directory is created under ``state_root / "tmp"``.

    Returns
    -------
    tuple[str, ...]
        Complete subprocess argument vector.

    Raises
    ------
    ValueError
        If ``tool`` is not supported.
    """

    if tool not in SUPPORTED_TOOLS:
        raise UnsupportedToolError(tool, tuple(sorted(SUPPORTED_TOOLS)))

    module = SUPPORTED_TOOLS[tool]

    argv: tuple[str, ...]

    if tool == "python":
        argv = (python,)
    else:
        if module is None:
            raise UnsupportedToolError(tool, tuple(sorted(SUPPORTED_TOOLS)))
        argv = (python, "-m", module)

    if tool == "pytest":
        selected_basetemp = (
            create_pytest_basetemp(state_root)
            if pytest_basetemp is None
            else pytest_basetemp
        )
        return (
            *argv,
            "-o",
            f"cache_dir={state_root / 'pytest-cache'}",
            "--basetemp",
            str(selected_basetemp),
            *tool_args,
        )
    if tool == "ruff" and tool_args and tool_args[0] in {"check", "format"}:
        return (
            *argv,
            tool_args[0],
            "--cache-dir",
            str(state_root / "ruff"),
            *tool_args[1:],
        )
    return (*argv, *tool_args)


def replay_completed_output(completed: subprocess.CompletedProcess[str]) -> None:
    """
    Replay captured child process output from the wrapper process.

    Parameters
    ----------
    completed : subprocess.CompletedProcess[str]
        Completed child process with text stdout and stderr.

    Returns
    -------
    None
        Captured output is written to the wrapper's standard streams.
    """

    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Run a repository tool with cache/temp state outside the repo."
    )
    parser.add_argument("tool", choices=sorted(SUPPORTED_TOOLS))
    parser.add_argument("tool_args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    """
    Execute the requested repository tool.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Child process exit code.
    """

    args = parse_args()
    state_root = tool_state_root(REPO_ROOT)
    (state_root / "tmp").mkdir(parents=True, exist_ok=True)
    (state_root / "coverage").mkdir(parents=True, exist_ok=True)
    env = tool_environment(os.environ, state_root=state_root)
    if args.tool == "pre-commit-noncode":
        env["SKIP"] = "ruff,ruff-format,mypy"
    argv = build_tool_argv(
        args.tool,
        args.tool_args,
        state_root=state_root,
        python=sys.executable,
    )
    completed = subprocess.run(argv, cwd=REPO_ROOT, env=env, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
