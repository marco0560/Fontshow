"""
Exercise persisted loadability behavior in dump-fonts.

Responsibilities
----------------
- Verify default loadability probing persists per-font state.
- Verify batch subdivision attributes failed fonts stably.
- Verify parse-inventory preserves attempted loadability metadata.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING

from fontshow.cli import parse_inventory
from fontshow.cli.dump_fonts import run_dump_fonts
from fontshow.core.types import ScriptISO
from fontshow.inventory import loadability
from tests.helpers import create_fake_font_file, simulate_dump_discovery

if TYPE_CHECKING:
    from pathlib import Path


def _candidate_descriptor(path: Path, family: str) -> dict[str, object]:
    """
    Build a minimal mutable descriptor suitable for loadability tests.

    Parameters
    ----------
    path : pathlib.Path
        Existing fake font path.
    family : str
        Family name stored in the descriptor.

    Returns
    -------
    dict[str, object]
        Minimal schema-compatible font descriptor.
    """
    return {
        "path": str(path),
        "family": family,
        "subfamily": "Regular",
        "typographic_subfamily": "Regular",
        "full_name": f"{family} Regular",
        "postscript_name": f"{family}-Regular",
        "version_string": "1.0",
        "unique_font_id": family.lower(),
        "metrics": {
            "units_per_em": 1000,
            "ascent": 800,
            "descent": -200,
            "weight_class": 400,
            "width_class": 5,
            "italic_angle": 0.0,
            "is_fixed_pitch": False,
            "glyph_count": 1,
        },
        "coverage": {"unicode_blocks": {}, "scripts": [], "languages": []},
        "inference": {},
        "charset": {"fc_charset": None},
        "typography": {
            "sample_text": {"source": "font", "text": family[0]},
            "specimen_text": family[0],
            "specimen_strategy": "cmap",
            "specimen_glyph_count": 1,
            "specimen_rejection_reason": None,
            "primary_script": None,
            "script_display_name": None,
            "render_policy": {
                "polyglossia_language": None,
                "fontspec_opts": None,
            },
            "script_source": None,
            "opentype_features": [],
        },
        "loadability": {
            "lualatex": {
                "attempted": False,
                "loadable": None,
                "reason": None,
                "runtime_fingerprint": None,
                "probe_input": None,
                "render_variants": [],
            }
        },
        "warnings": [],
    }


def test_dump_fonts_runs_loadability_by_default(tmp_path, monkeypatch):
    """
    Ensure dump-fonts persists loadability results by default.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for fake fonts and output.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace discovery and probing helpers.

    Returns
    -------
    None
    """
    font_path = create_fake_font_file(tmp_path, "Alpha.ttf")
    output = tmp_path / "inventory.json"
    simulate_dump_discovery(monkeypatch, [font_path], skipped_legacy=0)
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.fonttools_extract_all",
        lambda _path, **_kwargs: [{"ok": True, "ttc_index": None}],
    )
    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.build_font_descriptor",
        lambda _ctx: _candidate_descriptor(font_path, "Alpha"),
    )

    def _persist(fonts, *, validation_metadata, jobs):
        assert jobs == 4
        validation_metadata["attempted"] = True
        for font in fonts:
            font["loadability"]["lualatex"].update(
                {
                    "attempted": True,
                    "loadable": True,
                    "reason": None,
                    "runtime_fingerprint": validation_metadata["runtime_fingerprint"],
                    "probe_input": "U+0041",
                }
            )

    monkeypatch.setattr(
        "fontshow.cli.dump_fonts.probe_and_persist_lualatex_loadability",
        _persist,
    )

    rc = run_dump_fonts(
        SimpleNamespace(
            output=output,
            cache_dir=tmp_path,
            include_fc_charset=False,
            no_cache=True,
            loadability_jobs=4,
            verbose=False,
        )
    )

    assert rc == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["metadata"]["validation"]["lualatex"]["attempted"] is True
    assert data["fonts"][0]["loadability"]["lualatex"]["loadable"] is True


def test_probe_and_persist_lualatex_loadability_recurses_on_batch_failure(
    tmp_path, monkeypatch
):
    """
    Ensure failed batches are recursively split until attribution is stable.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for fake fonts.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace batch execution.

    Returns
    -------
    None

    Raises
    ------
    AssertionError
        Raised by the fake batch runner if recursion probes an unexpected
        candidate split.
    """
    alpha_path = create_fake_font_file(tmp_path, "Alpha.ttf")
    beta_path = create_fake_font_file(tmp_path, "Beta.ttf")
    gamma_path = create_fake_font_file(tmp_path, "Gamma.ttf")

    fonts: list[dict[str, object]] = [
        _candidate_descriptor(alpha_path, "Alpha"),
        _candidate_descriptor(beta_path, "Beta"),
        _candidate_descriptor(gamma_path, "Gamma"),
    ]
    metadata = {
        "attempted": False,
        "engine": "lualatex",
        "engine_version": "1.18.0",
        "luaotfload_version": "3.28",
        "fontspec_version": "2.9g",
        "polyglossia_version": "1.60.0",
        "runtime_fingerprint": "fp-1",
        "render_policy_version": "policy-v1",
    }

    def _fake_run(candidates, *, lualatex_bin):
        ids = [candidate.font_index for candidate in candidates]
        if ids == [0, 1, 2]:
            return 1, 'FONTSHOW_LOAD_OK:0\n! Font \\"Beta\\" cannot be found.\n'
        if ids == [0]:
            return 0, "FONTSHOW_LOAD_OK:0\n"
        if ids == [1, 2]:
            return 1, '! Font \\"Beta\\" cannot be found.\n'
        if ids == [1]:
            return 1, '! Font \\"Beta\\" cannot be found.\n'
        if ids == [2]:
            return 0, "FONTSHOW_LOAD_OK:2\n"
        raise AssertionError(ids)

    monkeypatch.setattr(loadability.shutil, "which", lambda _name: "/usr/bin/lualatex")
    monkeypatch.setattr(loadability, "_run_lualatex_batch", _fake_run)

    loadability.probe_and_persist_lualatex_loadability(
        fonts,
        validation_metadata=metadata,
        batch_size=3,
    )

    assert metadata["attempted"] is True
    assert fonts[0]["loadability"]["lualatex"]["loadable"] is True
    assert fonts[1]["loadability"]["lualatex"]["loadable"] is False
    assert fonts[1]["loadability"]["lualatex"]["reason"] == (
        '! Font \\"Beta\\" cannot be found.'
    )
    assert fonts[2]["loadability"]["lualatex"]["loadable"] is True


def test_resolve_batch_results_rejects_failed_single_candidate_with_ok_marker(
    tmp_path, monkeypatch
):
    """
    Ensure deferred LuaLaTeX failures override emitted OK markers.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for a fake font path.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace batch execution.

    Returns
    -------
    None
    """
    candidate = loadability._ProbeCandidate(
        candidate_index=7,
        font_index=0,
        path=create_fake_font_file(tmp_path, "DeferredFail.ttf"),
        probe_text="ქ",
        probe_input="U+10E5",
        fontspec_opts="Script=Georgian",
        script="GEOR",
        specimen_text="ქართული",
        specimen_glyph_count=7,
        specimen_strategy="script",
    )

    def _fake_run(candidates, *, lualatex_bin):
        ids = [item.candidate_index for item in candidates]
        assert ids == [7]
        return (
            1,
            "FONTSHOW_LOAD_OK:7\n! I can't find file `DeferredFail.ttf.fontspec'.\n",
        )

    monkeypatch.setattr(loadability, "_run_lualatex_batch", _fake_run)

    result = loadability._resolve_batch_results(
        [candidate],
        lualatex_bin="/usr/bin/lualatex",
    )

    assert result[7]["attempted"] is True
    assert result[7]["loadable"] is False
    assert result[7]["reason"] == "! I can't find file `DeferredFail.ttf.fontspec'."
    assert result[7]["probe_input"] == "U+10E5"


def test_render_probe_snippet_escapes_path_directory_and_probe_text(tmp_path):
    r"""
    Ensure generated LuaLaTeX probes cannot be broken by TeX syntax in data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to create an adversarial font path.

    Returns
    -------
    None
    """
    font_dir = tmp_path / "a}b"
    font_dir.mkdir()
    font_path = font_dir / "Probe.ttf"
    font_path.write_text("", encoding="utf-8")
    candidate = loadability._ProbeCandidate(
        candidate_index=9,
        font_index=0,
        path=font_path,
        probe_text=r"\input{/etc/passwd}",
        probe_input="U+005C",
        fontspec_opts=None,
    )

    snippet = loadability._render_probe_snippet(candidate)

    expected_dir = str(font_dir).replace("}", r"\}") + "/"
    assert "Path=\\detokenize{" + expected_dir + "}" in snippet
    assert r"\textbackslash{}input\{/etc/passwd\}" in snippet
    assert r"\input{/etc/passwd}" not in snippet


def test_probe_and_persist_lualatex_loadability_accepts_parallel_jobs(
    tmp_path, monkeypatch
):
    """
    Ensure bounded parallel probing preserves per-font loadability results.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for fake fonts.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace LuaLaTeX discovery and batch execution.

    Returns
    -------
    None
    """
    fonts: list[dict[str, object]] = [
        _candidate_descriptor(
            create_fake_font_file(tmp_path, f"Font{index}.ttf"), family
        )
        for index, family in enumerate(("Alpha", "Beta", "Gamma", "Delta"))
    ]
    metadata = {
        "attempted": False,
        "engine": "lualatex",
        "engine_version": "1.18.0",
        "luaotfload_version": "3.28",
        "fontspec_version": "2.9g",
        "polyglossia_version": "1.60.0",
        "runtime_fingerprint": "fp-1",
        "render_policy_version": "policy-v1",
    }
    calls: list[tuple[int, ...]] = []

    def _fake_run(candidates, *, lualatex_bin):
        ids = tuple(candidate.candidate_index for candidate in candidates)
        calls.append(ids)
        output = "\n".join(f"FONTSHOW_LOAD_OK:{candidate_id}" for candidate_id in ids)
        return 0, output

    monkeypatch.setattr(loadability.shutil, "which", lambda _name: "/usr/bin/lualatex")
    monkeypatch.setattr(loadability, "_run_lualatex_batch", _fake_run)

    loadability.probe_and_persist_lualatex_loadability(
        fonts,
        validation_metadata=metadata,
        batch_size=1,
        jobs=2,
    )

    assert sorted(calls) == [(0,), (1,), (2,), (3,)]
    assert metadata["attempted"] is True
    assert [font["loadability"]["lualatex"]["loadable"] for font in fonts] == [
        True,
        True,
        True,
        True,
    ]


def test_parse_inventory_refreshes_lualatex_validation_and_probes_variants(monkeypatch):
    """
    Ensure parse-inventory refreshes validation metadata and probes variants.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace platform metadata helpers.

    Returns
    -------
    None
    """
    data = {
        "metadata": {
            "schema_version": "1.5",
            "run_environment": {
                "os": "x",
                "machine": "y",
                "execution_context": "native",
            },
            "validation": {
                "lualatex": {
                    "attempted": True,
                    "engine": "lualatex",
                    "engine_version": "1.18.0",
                    "luaotfload_version": "3.28",
                    "fontspec_version": "2.9g",
                    "polyglossia_version": "1.60.0",
                    "runtime_fingerprint": "fp-1",
                    "render_policy_version": "policy-v1",
                }
            },
        },
        "fonts": [],
    }
    monkeypatch.setattr(parse_inventory, "collect_platform_metadata", dict)
    probe_calls: list[tuple[list[dict[str, object]], dict[str, object], int]] = []
    monkeypatch.setattr(
        parse_inventory,
        "collect_latex_validation_metadata",
        lambda: {"attempted": False, "runtime_fingerprint": "fp-2"},
    )
    monkeypatch.setattr(
        parse_inventory,
        "probe_and_persist_lualatex_render_variants",
        lambda fonts, *, validation_metadata, jobs: probe_calls.append(
            (list(fonts), validation_metadata, jobs)
        ),
    )

    result = parse_inventory.parse_inventory(data, level="medium", loadability_jobs=6)

    assert result["metadata"]["validation"]["lualatex"]["attempted"] is False
    assert result["metadata"]["validation"]["lualatex"]["runtime_fingerprint"] == "fp-2"
    assert probe_calls == [([], result["metadata"]["validation"]["lualatex"], 6)]


def test_parse_inventory_rejects_incomplete_lualatex_loadability(tmp_path, monkeypatch):
    """
    Ensure parse-inventory fails when loadability remains incomplete.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for the candidate font path.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace runtime metadata and probing helpers.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        Raised by parse-inventory when the candidate has no completed
        persisted LuaLaTeX loadability state.
    """
    font_path = create_fake_font_file(tmp_path, "Alpha.ttf")
    data = {
        "metadata": {
            "schema_version": "1.5",
            "run_environment": {
                "os": "x",
                "machine": "y",
                "execution_context": "native",
            },
            "validation": {},
        },
        "fonts": [_candidate_descriptor(font_path, "Alpha")],
    }
    monkeypatch.setattr(parse_inventory, "collect_platform_metadata", dict)
    monkeypatch.setattr(
        parse_inventory,
        "collect_latex_validation_metadata",
        lambda: {"attempted": False, "runtime_fingerprint": "fp-2"},
    )
    monkeypatch.setattr(
        parse_inventory,
        "probe_and_persist_lualatex_render_variants",
        lambda fonts, *, validation_metadata, jobs: None,
    )

    try:
        parse_inventory.parse_inventory(data, level="medium")
    except ValueError as exc:
        assert "LuaLaTeX loadability incomplete" in str(exc)
    else:
        msg = "parse_inventory did not reject incomplete loadability"
        raise AssertionError(msg)


def test_render_variant_specimen_falls_back_to_script_scoped_cmap(monkeypatch):
    """
    Ensure render-variant probing can fall back to script-scoped cmap text.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace curated specimens and cmap extraction.

    Returns
    -------
    None
    """
    font = {
        "path": "/tmp/Alpha.ttf",
        "typography": {
            "primary_script": "LATN",
            "specimen_text": "The quick brown fox jumps over the lazy dog",
        },
    }
    arabic_letters = [0x0627 + index for index in range(20)]
    monkeypatch.setitem(
        loadability.SCRIPT_INFO,
        ScriptISO("ARAB"),
        {
            "specimen": "صِفْ خَلْقَ خَوْدٍ",
            "unicode_max_ranges": [(0x0600, 0x06FF)],
        },
    )
    monkeypatch.setattr(
        loadability,
        "_specimen_collect_cmap",
        lambda _path, _ttc_index: set(arabic_letters) | {ord("A"), ord("B")},
    )

    specimen = loadability._render_variant_specimen(font, ScriptISO("ARAB"))

    assert specimen
    assert len(specimen) == loadability.MIN_SAMPLE_GLYPHS
    assert all(0x0600 <= ord(ch) <= 0x06FF for ch in specimen)


def test_probe_and_persist_lualatex_render_variants_persists_specimen_data(
    tmp_path, monkeypatch
):
    """
    Ensure render-variant persistence stores the validated specimen payload.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used for fake fonts.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace probing helpers.

    Returns
    -------
    None
    """
    font_path = create_fake_font_file(tmp_path, "Alpha.ttf")
    font = _candidate_descriptor(font_path, "Alpha")
    font["typography"]["primary_script"] = "LATN"
    font["typography"]["specimen_text"] = "The quick brown fox"
    font["coverage"]["scripts"] = ["LATN", "ARAB"]
    font["inference"] = {"scripts": ["LATN", "ARAB"]}
    metadata = {"attempted": False, "runtime_fingerprint": "fp-1"}

    monkeypatch.setattr(loadability.shutil, "which", lambda _name: "/usr/bin/lualatex")
    monkeypatch.setattr(
        loadability,
        "_ordered_render_variant_scripts",
        lambda _font: [ScriptISO("LATN"), ScriptISO("ARAB")],
    )
    monkeypatch.setattr(
        loadability,
        "_render_variant_specimen_details",
        lambda _font, script, **_kwargs: (
            ("The quick brown fox", 16, "script")
            if str(script) == "LATN"
            else ("ابتثجحخدذرزسشصض", 16, "script-cmap")
        ),
    )
    monkeypatch.setattr(
        loadability,
        "_get_render_policy",
        lambda script: ("", None if str(script) == "LATN" else "Script=Arabic"),
    )
    resolve_calls: list[int] = []

    def _fake_resolve(chunks, *, lualatex_bin, jobs):
        resolve_calls.append(jobs)
        return {
            candidate.candidate_index: {
                "attempted": True,
                "loadable": True,
                "reason": None,
                "probe_input": candidate.probe_input,
            }
            for chunk in chunks
            for candidate in chunk
        }

    monkeypatch.setattr(loadability, "_resolve_candidate_chunks", _fake_resolve)

    loadability.probe_and_persist_lualatex_render_variants(
        [font], validation_metadata=metadata, jobs=3
    )

    variants = font["loadability"]["lualatex"]["render_variants"]
    assert resolve_calls == [3]
    assert variants[0]["specimen_text"] == "The quick brown fox"
    assert variants[0]["specimen_glyph_count"] == 16
    assert variants[0]["specimen_strategy"] == "script"
    assert variants[1]["specimen_text"] == "ابتثجحخدذرزسشصض"
    assert variants[1]["specimen_glyph_count"] == 16
    assert variants[1]["specimen_strategy"] == "script-cmap"
