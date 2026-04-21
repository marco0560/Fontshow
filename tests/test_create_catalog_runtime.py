"""
Exercise create-catalog runtime branches.

Responsibilities
----------------
- Cover test-output generation and write failures.
- Verify main() propagates exit codes and crash-barrier behavior.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from fontshow.catalog.loadability import LoadabilityExclusion, LoadabilityFilterResult
from fontshow.cli import create_catalog


def test_generate_test_output_filters_limits_and_logs_error(monkeypatch, tmp_path):
    """
    Ensure diagnostic output honors filtering/limits and reports filename failures.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace catalog helpers and logging.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage output files.

    Returns
    -------
    None

    Raises
    ------
    OSError
        Raised by the nested write stub and handled by the runtime wrapper.
    """
    out_file = tmp_path / "report.txt"
    monkeypatch.setattr(create_catalog, "TEST_FONTS", {"Beta"})
    monkeypatch.setattr(
        create_catalog, "platform", SimpleNamespace(system=lambda: "TestOS")
    )
    monkeypatch.setattr(create_catalog, "DATE_STR", "2099-01-01")
    monkeypatch.setattr(
        create_catalog, "get_unique_filename", lambda base, ext: str(out_file)
    )

    create_catalog._generate_test_output(
        [
            {"family": "Alpha", "path": "/fonts/a.ttf"},
            {"family": "Beta", "path": "/fonts/b.ttf"},
            {"family": "Beta", "path": "/fonts/c.ttf"},
        ],
        limit=-1,
        filter_test=True,
    )

    content = out_file.read_text(encoding="utf-8")
    assert "Raw line: Beta" in content
    assert "/fonts/b.ttf" in content
    assert "/fonts/c.ttf" in content
    assert "Alpha" not in content

    errors: list[str] = []
    monkeypatch.setattr(
        create_catalog,
        "get_unique_filename",
        lambda base, ext: (_ for _ in ()).throw(ValueError("boom")),
    )
    monkeypatch.setattr(create_catalog, "log_err", errors.append)

    create_catalog._generate_test_output([], None, False)
    assert errors == ["Error generating test file: boom"]


def test_generate_test_output_treats_limit_zero_as_no_limit(monkeypatch, tmp_path):
    """
    Ensure the current ``limit=0`` behavior is pinned explicitly.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace catalog helpers.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the output file.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        Raised by the nested crash stub and normalized by the public entrypoint.
    """
    out_file = tmp_path / "report.txt"
    monkeypatch.setattr(
        create_catalog, "platform", SimpleNamespace(system=lambda: "TestOS")
    )
    monkeypatch.setattr(create_catalog, "DATE_STR", "2099-01-01")
    monkeypatch.setattr(
        create_catalog, "get_unique_filename", lambda base, ext: str(out_file)
    )

    create_catalog._generate_test_output(
        [
            {"family": "Alpha", "path": "/fonts/a.ttf"},
            {"family": "Beta", "path": "/fonts/b.ttf"},
        ],
        limit=0,
        filter_test=False,
    )

    content = out_file.read_text(encoding="utf-8")
    assert "Raw line: Alpha" in content
    assert "Raw line: Beta" in content


def test_resolve_inventory_path_prefers_explicit_paths_and_defaults_from_cwd(tmp_path):
    """
    Ensure inventory resolution honors explicit paths and the cwd default file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the default inventory.

    Returns
    -------
    None
    """
    default_inventory = tmp_path / create_catalog.DEFAULT_INVENTORY
    default_inventory.write_text("{}", encoding="utf-8")

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        assert create_catalog._resolve_inventory_path(
            SimpleNamespace(inventory=None)
        ) == Path(create_catalog.DEFAULT_INVENTORY)
        assert create_catalog._resolve_inventory_path(
            SimpleNamespace(inventory="subdir/inventory.json")
        ) == Path("subdir/inventory.json")
        assert create_catalog._resolve_inventory_path(
            SimpleNamespace(inventory="/mnt/c/tmp/inventory.json")
        ) == Path("/mnt/c/tmp/inventory.json")
    finally:
        os.chdir(old_cwd)


def test_run_create_catalog_handles_list_mode_invalid_fonts_and_write_failures(
    monkeypatch, tmp_path
):
    """
    Ensure runtime flow covers list mode, invariant failure, and output write errors.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace runtime helpers and logging.
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the inventory file.

    Returns
    -------
    None

    Raises
    ------
    OSError
        Raised by the nested write stub and handled by the runtime wrapper.
    """
    inv = tmp_path / "inventory.json"
    inv.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(create_catalog, "_configure_test_fonts", lambda args: {"Alpha"})
    monkeypatch.setattr(
        create_catalog, "_prepare_output_filename", lambda: (0, "out.tex")
    )
    monkeypatch.setattr(create_catalog, "_resolve_inventory_path", lambda args: inv)
    monkeypatch.setattr(
        create_catalog,
        "_load_inventory",
        lambda path, **_kwargs: (0, [{"family": "Alpha"}], {}),
    )
    diagnostics_calls: list[list[dict]] = []
    monkeypatch.setattr(
        create_catalog,
        "_run_inventory_diagnostics",
        lambda fonts: diagnostics_calls.append(list(fonts)),
    )

    list_calls: list[tuple[set[str], list[dict]]] = []
    monkeypatch.setattr(
        create_catalog,
        "_handle_list_test_fonts",
        lambda test_fonts, fonts: list_calls.append((test_fonts, fonts)) or 9,
    )

    args = SimpleNamespace(
        output=None,
        inventory=str(inv),
        test=False,
        list_test_fonts=True,
        number=None,
        quiet=False,
        verbose=False,
        test_font=None,
        catalog_detail="compact",
        indexed_navigation=False,
        appendix_descriptions=False,
        language=None,
        script=None,
        sort_by=None,
    )
    assert create_catalog.run_create_catalog(args) == 9
    assert list_calls == [({"Alpha"}, [{"family": "Alpha"}])]

    errors: list[str] = []
    monkeypatch.setattr(create_catalog, "log_err", errors.append)
    monkeypatch.setattr(
        create_catalog, "_handle_list_test_fonts", lambda test_fonts, fonts: 0
    )
    monkeypatch.setattr(
        create_catalog,
        "_filter_and_prepare_fonts",
        lambda fonts, args, test_fonts: ["bad"],
    )
    args.list_test_fonts = False
    assert create_catalog.run_create_catalog(args) == 1
    assert errors[-1] == "Internal error: invalid font descriptor list after filtering."

    monkeypatch.setattr(
        create_catalog,
        "_filter_and_prepare_fonts",
        lambda fonts, args, test_fonts: [{"family": "Alpha"}],
    )
    loadability_calls: list[list[dict]] = []
    monkeypatch.setattr(
        create_catalog,
        "filter_loadable_catalog_fonts_with_report",
        lambda fonts, **_kwargs: (
            loadability_calls.append(list(fonts))
            or LoadabilityFilterResult(
                kept=list(fonts),
                excluded=[
                    LoadabilityExclusion(
                        identity="bad-1",
                        family="Broken",
                        path="/fonts/broken.ttf",
                        detail="subset-empty",
                    )
                ],
            )
        ),
    )
    latex_calls: list[
        tuple[
            list[dict],
            list[LoadabilityExclusion],
            object,
            dict[str, str],
        ]
    ] = []
    monkeypatch.setattr(
        create_catalog,
        "generate_latex_with_report",
        lambda fonts, *, excluded_fonts, render_options, generation_metadata: (
            latex_calls.append(
                (
                    list(fonts),
                    list(excluded_fonts),
                    render_options,
                    dict(generation_metadata),
                )
            )
            or "LATEX"
        ),
    )
    monkeypatch.setattr(
        create_catalog,
        "_build_generation_metadata",
        lambda _args: {
            "generation_timestamp": "April 02, 2026 18:15:13 CEST",
            "command_line": "fontshow create-catalog --inventory inv.json",
            "system_name": "Linux",
            "hostname": "atlas",
        },
    )

    def _boom(_path, _content):
        """
        Raise a deterministic output write failure.

        Parameters
        ----------
        _path : object
            Output path accepted for interface compatibility.
        _content : object
            Rendered content accepted for interface compatibility.

        Returns
        -------
        None

        Raises
        ------
        OSError
            Always raised with a fixed message.
        """
        msg = "disk full"
        raise OSError(msg)

    monkeypatch.setattr(create_catalog, "_write_latex_output", _boom)
    assert create_catalog.run_create_catalog(args) == 1
    assert diagnostics_calls == [[{"family": "Alpha"}]]
    assert loadability_calls == [[{"family": "Alpha"}]]
    assert latex_calls[0][0] == [{"family": "Alpha"}]
    assert latex_calls[0][3]["hostname"] == "atlas"
    assert latex_calls[0][1] == [
        LoadabilityExclusion(
            identity="bad-1",
            family="Broken",
            path="/fonts/broken.ttf",
            detail="subset-empty",
        )
    ]
    assert latex_calls[0][2].catalog_detail == "compact"
    assert latex_calls[0][2].indexed_navigation is False
    assert latex_calls[0][2].appendix_descriptions is False
    assert errors[-1] == "Failed to write output file: disk full"


def test_main_logs_success_failure_and_exception(monkeypatch):
    """
    Ensure main() preserves exit codes and converts unexpected exceptions to rc=2.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace runtime and logging helpers.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        Raised by the nested crash stub and normalized by the public entrypoint.
    """
    oks: list[str] = []
    errs: list[str] = []
    trace: list[dict[str, object]] = []

    monkeypatch.setattr(
        create_catalog,
        "log_ok",
        lambda message, **kwargs: oks.append(message),
    )
    monkeypatch.setattr(create_catalog, "log_err", errs.append)
    monkeypatch.setattr(
        create_catalog,
        "log_trace_cat",
        lambda _log, _cat, _msg, extra: trace.append(extra),
    )

    args = SimpleNamespace(quiet=False, verbose=False)

    monkeypatch.setattr(create_catalog, "_run_create_catalog", lambda args: 0)
    assert create_catalog.main(args) == 0
    assert oks[-1] == "Done"
    assert trace[-1] == {"exit_code": 0}

    monkeypatch.setattr(create_catalog, "_run_create_catalog", lambda args: 5)
    assert create_catalog.main(args) == 5
    assert errs[-1] == "create-catalog failed with exit code 5"
    assert trace[-1] == {"exit_code": 5}

    def _crash(_args):
        """
        Raise a deterministic internal failure for the runtime wrapper test.

        Parameters
        ----------
        _args : object
            Parsed CLI arguments accepted for interface compatibility.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Always raised with a fixed message.
        """
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(create_catalog, "_run_create_catalog", _crash)
    assert create_catalog.main(args) == 2
    assert errs[-1] == "create-catalog failed: boom"
    assert trace[-1] == {"exit_code": 2, "exception": True}
