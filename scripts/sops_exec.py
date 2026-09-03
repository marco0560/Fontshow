#!/usr/bin/env python3
"""Run credentialed child commands with scoped SOPS environments.

This module keeps decrypted credentials confined to the specific child process
that needs them. Callers receive command output but never read or inherit a
secret value themselves.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

PERSONAL_SECRETS_DIR = Path.home() / ".config" / "personal-secrets" / "secrets"
GITHUB_SECRET_FILE = PERSONAL_SECRETS_DIR / "github.env"


class SopsExecutionError(RuntimeError):
    """Report an unavailable or invalid scoped SOPS execution request.

    Parameters
    ----------
    message : str
        Human-readable explanation of the invalid request.

    Returns
    -------
    None
    """


def sops_exec_env_argv(secret_file: Path, command: Sequence[str]) -> list[str]:
    """Build a SOPS ``exec-env`` command for one encrypted environment.

    Parameters
    ----------
    secret_file : pathlib.Path
        Encrypted dotenv file located under the personal-secrets directory.
    command : collections.abc.Sequence[str]
        Child command and arguments that require the decrypted environment.

    Returns
    -------
    list[str]
        Argument vector that runs the child through ``sops exec-env``.

    Raises
    ------
    SopsExecutionError
        If SOPS is unavailable, the encrypted file is outside the approved
        directory, or no child command was supplied.
    """
    if not command:
        message = "SOPS execution requires a child command."
        raise SopsExecutionError(message)

    if shutil.which("sops") is None:
        message = "Required executable not found in PATH: sops"
        raise SopsExecutionError(message)

    approved_dir = PERSONAL_SECRETS_DIR.resolve()
    resolved_file = secret_file.expanduser().resolve()
    if resolved_file.parent != approved_dir:
        message = f"Secret file must be located under {approved_dir}: {resolved_file}"
        raise SopsExecutionError(message)
    if not resolved_file.is_file():
        message = f"Encrypted secret file not found: {resolved_file}"
        raise SopsExecutionError(message)

    return ["sops", "exec-env", str(resolved_file), shlex.join(command)]


def run_with_github_secret(
    command: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = False,
    text: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one GitHub-credentialed child command through SOPS.

    Parameters
    ----------
    command : collections.abc.Sequence[str]
        Command that requires ``GH_TOKEN`` from the GitHub secret environment.
    check : bool, optional
        Whether a non-zero child exit status raises an exception.
    capture_output : bool, optional
        Whether to capture child standard output and standard error.
    text : bool, optional
        Whether captured output is decoded as text.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed SOPS-wrapped child-process result.

    Raises
    ------
    SopsExecutionError
        If the local SOPS setup cannot safely launch the child command.
    subprocess.CalledProcessError
        If ``check`` is true and the child exits unsuccessfully.
    """
    return subprocess.run(
        sops_exec_env_argv(GITHUB_SECRET_FILE, command),
        check=check,
        capture_output=capture_output,
        text=text,
    )
