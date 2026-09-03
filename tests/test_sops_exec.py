"""Verify SOPS command scoping for credentialed maintenance children."""

from __future__ import annotations

import importlib.util
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sops_exec.py"
_SPEC = importlib.util.spec_from_file_location("sops_exec", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
sops_exec = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = sops_exec
_SPEC.loader.exec_module(sops_exec)


def test_sops_exec_env_argv_scopes_only_an_approved_secret_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Build a SOPS command only for a file in the configured secret directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory used as the approved encrypted-secret location.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the SOPS executable lookup.

    Returns
    -------
    None
    """
    secret_file = tmp_path / "github.env"
    secret_file.touch()
    monkeypatch.setattr(sops_exec, "PERSONAL_SECRETS_DIR", tmp_path)
    monkeypatch.setattr(sops_exec.shutil, "which", lambda _name: "/usr/bin/sops")

    argv = sops_exec.sops_exec_env_argv(
        secret_file,
        ["gh", "api", "graphql", "-f", "query={ viewer { login } }"],
    )

    assert argv[:3] == ["sops", "exec-env", str(secret_file)]
    assert shlex.split(argv[3]) == [
        "gh",
        "api",
        "graphql",
        "-f",
        "query={ viewer { login } }",
    ]


def test_sops_exec_env_argv_rejects_files_outside_secret_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject arbitrary files before SOPS is asked to decrypt them.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory used to separate approved and rejected paths.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the SOPS executable lookup.

    Returns
    -------
    None
    """
    secret_dir = tmp_path / "secrets"
    secret_dir.mkdir()
    outside_file = tmp_path / "outside.env"
    outside_file.touch()
    monkeypatch.setattr(sops_exec, "PERSONAL_SECRETS_DIR", secret_dir)
    monkeypatch.setattr(sops_exec.shutil, "which", lambda _name: "/usr/bin/sops")

    with pytest.raises(sops_exec.SopsExecutionError, match="must be located"):
        sops_exec.sops_exec_env_argv(outside_file, ["gh", "api", "user"])


def test_run_with_github_secret_does_not_pass_a_parent_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the credentialed command without an inherited environment override.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory used as the approved encrypted-secret location.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace SOPS command construction and subprocess use.

    Returns
    -------
    None
    """
    secret_file = tmp_path / "github.env"
    secret_file.touch()
    monkeypatch.setattr(sops_exec, "PERSONAL_SECRETS_DIR", tmp_path)
    monkeypatch.setattr(sops_exec, "GITHUB_SECRET_FILE", secret_file)
    monkeypatch.setattr(sops_exec.shutil, "which", lambda _name: "/usr/bin/sops")
    observed: dict[str, object] = {}

    def _fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["args"] = args
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="{}")

    monkeypatch.setattr(sops_exec.subprocess, "run", _fake_run)

    sops_exec.run_with_github_secret(
        ["gh", "api", "user"], capture_output=True, text=True
    )

    assert observed["args"] == (["sops", "exec-env", str(secret_file), "gh api user"],)
    assert "env" not in observed["kwargs"]
