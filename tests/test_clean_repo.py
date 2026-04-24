"""Verify repository artifact cleanup discovery."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "clean_repo.py"
_SPEC = importlib.util.spec_from_file_location("clean_repo", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
clean_repo = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = clean_repo
_SPEC.loader.exec_module(clean_repo)


def test_cleanup_paths_include_known_pytest_artifacts(monkeypatch, tmp_path) -> None:
    """
    Ensure known pytest artifact directories do not depend on Git traversal.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace ignored-path discovery.
    tmp_path : pathlib.Path
        Temporary repository root for the test.

    Returns
    -------
    None
    """
    for name in (
        ".pytest_tmp",
        ".pytest-basetemp",
        ".tmp",
        "pytest-cache-files-alpha",
        "pytest-runtime",
    ):
        (tmp_path / name).mkdir()

    monkeypatch.setattr(clean_repo, "git_ignored_paths", lambda: iter(()))

    paths = clean_repo.cleanup_paths(tmp_path)

    assert Path(".pytest_tmp") in paths
    assert Path(".pytest-basetemp") in paths
    assert Path(".tmp") in paths
    assert Path("pytest-cache-files-alpha") in paths
    assert Path("pytest-runtime") in paths


def test_cleanup_paths_exclude_protected_and_missing_paths(
    monkeypatch, tmp_path
) -> None:
    """
    Ensure cleanup discovery preserves protected developer paths.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace ignored-path discovery.
    tmp_path : pathlib.Path
        Temporary repository root for the test.

    Returns
    -------
    None
    """
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".codira").mkdir()
    (tmp_path / ".pytest_cache").mkdir()

    monkeypatch.setattr(
        clean_repo,
        "git_ignored_paths",
        lambda: iter(
            (
                Path(".venv"),
                Path(".codira"),
                Path(".pytest_cache"),
                Path("missing-artifact"),
            )
        ),
    )

    paths = clean_repo.cleanup_paths(tmp_path)

    assert Path(".pytest_cache") in paths
    assert Path(".venv") not in paths
    assert Path(".codira") not in paths
    assert Path("missing-artifact") not in paths


def test_remove_path_reports_failure_without_stopping(monkeypatch, tmp_path) -> None:
    """
    Ensure cleanup can continue after an undeletable directory.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to emulate a removal failure.
    tmp_path : pathlib.Path
        Temporary repository root for the test.

    Returns
    -------
    None
    """
    target = tmp_path / "locked"
    target.mkdir()

    def fail_rmtree(_path: Path) -> None:
        """
        Raise a deterministic filesystem failure.

        Parameters
        ----------
        _path : pathlib.Path
            Directory path accepted for interface compatibility.

        Returns
        -------
        None

        Raises
        ------
        OSError
            Always raised to emulate a locked directory.
        """
        msg = "denied"
        raise OSError(msg)

    monkeypatch.setattr(clean_repo.shutil, "rmtree", fail_rmtree)

    assert not clean_repo.remove_path(target, dry_run=False)
    assert target.exists()
