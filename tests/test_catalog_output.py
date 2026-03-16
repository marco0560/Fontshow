"""
Verify catalog output filename and write behavior.

Responsibilities
----------------
- Cover filename collision handling and exhaustion behavior.
- Ensure output preparation converts filename failures into exit codes.
- Verify LaTeX output writing emits the expected user-facing messages.
"""

from __future__ import annotations

import os
from pathlib import Path

from fontshow.catalog import output


def test_get_unique_filename_skips_existing_candidates(tmp_path):
    """
    Ensure the helper advances past an occupied suffix before returning.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage existing files.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        Raised by the helper under test when every candidate filename is occupied.
    """
    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / "catalog_000.tex").write_text("", encoding="utf-8")

        assert output.get_unique_filename("catalog", "tex") == "catalog_001.tex"
    finally:
        os.chdir(old_cwd)


def test_get_unique_filename_raises_after_exhausting_counter_space(monkeypatch):
    """
    Ensure the 000-999 search space raises once fully occupied.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to force every candidate filename to appear occupied.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        Raised by the nested filename allocator stub and handled by the wrapper.
    """
    monkeypatch.setattr(output.Path, "exists", lambda self: True)

    try:
        output.get_unique_filename("catalog", "tex")
    except ValueError as exc:
        assert "dopo 1000 tentativi" in str(exc)
    else:
        msg = "expected ValueError when all candidate filenames exist"
        raise AssertionError(msg)


def test_prepare_output_filename_logs_and_returns_error_on_collision_exhaustion(
    monkeypatch,
):
    """
    Ensure output preparation converts filename allocation failures into rc=1.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace platform and filename helpers.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        Raised by the nested filename allocator stub and handled by the wrapper.
    """
    errors: list[str] = []

    monkeypatch.setattr(output.platform, "system", lambda: "TestOS")
    monkeypatch.setattr(output, "DATE_STR", "2099-12-31")

    def _boom(_base_name: str, _extension: str) -> str:
        """
        Raise a deterministic filename allocation failure.

        Parameters
        ----------
        _base_name : str
            Base filename stem accepted for interface compatibility.
        _extension : str
            Requested filename extension accepted for interface compatibility.

        Returns
        -------
        str
            This function never returns successfully.

        Raises
        ------
        ValueError
            Always raised with a fixed message.
        """
        msg = "no available filename"
        raise ValueError(msg)

    monkeypatch.setattr(output, "get_unique_filename", _boom)
    monkeypatch.setattr(output, "log_err", errors.append)

    rc, filename = output._prepare_output_filename()

    assert rc == 1
    assert filename is None
    assert errors == ["Error: no available filename"]


def test_write_latex_output_writes_file_and_logs_messages(tmp_path, monkeypatch):
    """
    Ensure the write helper persists content and emits completion messages.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the output file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace logging helpers.

    Returns
    -------
    None
    """
    infos: list[str] = []
    oks: list[str] = []
    target = tmp_path / "catalog.tex"

    monkeypatch.setattr(output, "log_info", infos.append)
    monkeypatch.setattr(output, "log_ok", oks.append)

    output._write_latex_output(str(target), "Hello, catalog\n")

    assert target.read_text(encoding="utf-8") == "Hello, catalog\n"
    assert infos == [f"Writing file {target}..."]
    assert oks == [
        "Done! LaTeX file generated successfully.",
        "Ready for compilation.",
        f"  Execute: lualatex -interaction=nonstopmode {target} | texlogsieve (twice)",
    ]
