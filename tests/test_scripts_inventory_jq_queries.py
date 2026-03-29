"""
Exercise the saved inventory jq query helper script.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "inventory_jq_queries.py"
)
_SPEC = importlib.util.spec_from_file_location("inventory_jq_queries", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
inventory_jq_queries = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = inventory_jq_queries
_SPEC.loader.exec_module(inventory_jq_queries)


def test_render_query_listing_includes_expected_saved_queries():
    """
    Ensure the script advertises the saved inventory inspection queries.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    listing = inventory_jq_queries.render_query_listing()

    assert "schema-v1-3" in listing
    assert "loadability-summary" in listing
    assert "unresolved-loadability" in listing
    assert "fontfile-specimens" in listing
    assert "embedded-sample-text" in listing


def test_render_query_details_mentions_internal_specimen_semantics():
    """
    Ensure the fontfile specimen query documents its interpretation clearly.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    spec = inventory_jq_queries.QUERY_BY_NAME["fontfile-specimens"]

    details = inventory_jq_queries.render_query_details(spec)

    assert 'specimen_strategy == "internal"' in details
    assert '.value.typography.specimen_strategy == "internal"' in details


def test_render_query_details_mentions_embedded_sample_text_semantics():
    """
    Ensure the embedded sample text query documents raw sample-text semantics.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    spec = inventory_jq_queries.QUERY_BY_NAME["embedded-sample-text"]

    details = inventory_jq_queries.render_query_details(spec)

    assert "typography.sample_text.text" in details
    assert "`specimen_strategy` may still be `deferred`" in details


def test_run_saved_query_invokes_jq_with_selected_program(tmp_path, monkeypatch):
    """
    Ensure `run` forwards the saved `jq` program and selected file path.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage a fake inventory file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace `jq` discovery and subprocess execution.

    Returns
    -------
    None
    """
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}", encoding="utf-8")
    calls: list[list[str]] = []

    class _Result:
        """
        Minimal subprocess result stub with a configurable return code.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        returncode = 0

    monkeypatch.setattr(
        inventory_jq_queries.shutil, "which", lambda name: "/usr/bin/jq"
    )

    def _fake_run(argv, check):
        calls.append(list(argv))
        assert check is False
        return _Result()

    monkeypatch.setattr(inventory_jq_queries.subprocess, "run", _fake_run)

    rc = inventory_jq_queries.run_saved_query(
        inventory_jq_queries.QUERY_BY_NAME["loadability-summary"],
        inventory,
    )

    assert rc == 0
    assert calls == [
        [
            "jq",
            inventory_jq_queries.QUERY_BY_NAME["loadability-summary"].query,
            str(inventory),
        ]
    ]


def test_run_saved_query_rejects_missing_inventory(monkeypatch):
    """
    Ensure execution fails clearly when the inventory file is absent.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace `jq` discovery.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        inventory_jq_queries.shutil, "which", lambda name: "/usr/bin/jq"
    )

    with pytest.raises(SystemExit) as excinfo:
        inventory_jq_queries.run_saved_query(
            inventory_jq_queries.QUERY_BY_NAME["schema-v1-3"],
            Path("/definitely/missing.json"),
        )

    assert excinfo.value.code == 1


def test_main_show_emits_query_and_interpretation(capsys):
    """
    Ensure the `show` command prints the saved filter and its guidance.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Fixture used to capture standard output.

    Returns
    -------
    None
    """
    rc = inventory_jq_queries.main(["show", "schema-v1-3"])

    captured = capsys.readouterr()

    assert rc == 0
    assert "Query: schema-v1-3" in captured.out
    assert "Interpretation:" in captured.out
    assert "all_ok=true" in captured.out
