"""
Exercise inventory loadability metadata and accessor helpers.

Responsibilities
----------------
- Verify deterministic LuaLaTeX runtime fingerprint generation.
- Verify inventory metadata collection populates the fingerprint.
- Verify v1.4 LuaLaTeX loadability accessors and mutators.
"""

from __future__ import annotations

from fontshow.inventory import latex_validation_metadata, schema_accessors


def test_build_latex_runtime_fingerprint_requires_engine():
    """
    Ensure fingerprints are absent when no engine is available.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert (
        latex_validation_metadata.build_latex_runtime_fingerprint(
            {
                "engine": None,
                "engine_version": "1.18.0",
                "luaotfload_version": "3.28",
                "fontspec_version": "2.9g",
                "polyglossia_version": "1.60.0",
                "render_policy_version": "policy-v1",
            }
        )
        is None
    )


def test_build_latex_runtime_fingerprint_is_deterministic():
    """
    Ensure fingerprint generation depends only on the recorded runtime.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    metadata = {
        "engine": "lualatex",
        "engine_version": "1.18.0",
        "luaotfload_version": "3.28",
        "fontspec_version": "2.9g",
        "polyglossia_version": "1.60.0",
        "render_policy_version": "policy-v1",
    }

    first = latex_validation_metadata.build_latex_runtime_fingerprint(metadata)
    second = latex_validation_metadata.build_latex_runtime_fingerprint(dict(metadata))

    assert isinstance(first, str)
    assert len(first) == 64
    assert first == second


def test_attach_latex_runtime_fingerprint_preserves_other_fields():
    """
    Ensure metadata enrichment only adds the derived fingerprint value.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    metadata = {
        "attempted": False,
        "engine": "lualatex",
        "engine_version": "1.18.0",
        "luaotfload_version": "3.28",
        "fontspec_version": "2.9g",
        "polyglossia_version": "1.60.0",
        "runtime_fingerprint": None,
        "render_policy_version": "policy-v1",
    }

    enriched = latex_validation_metadata.attach_latex_runtime_fingerprint(metadata)

    assert enriched["engine"] == "lualatex"
    assert enriched["attempted"] is False
    assert isinstance(enriched["runtime_fingerprint"], str)
    assert metadata["runtime_fingerprint"] is None


def test_collect_latex_validation_metadata_populates_runtime_fingerprint(monkeypatch):
    """
    Ensure collected metadata includes the derived runtime fingerprint.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace runtime discovery helpers.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        latex_validation_metadata.shutil, "which", lambda name: f"/usr/bin/{name}"
    )
    monkeypatch.setattr(
        latex_validation_metadata,
        "_read_command_stdout",
        lambda *_argv: "This is LuaHBTeX, Version 1.18.0",
    )
    monkeypatch.setattr(
        latex_validation_metadata,
        "_extract_package_version",
        lambda package: {
            "luaotfload": "3.28",
            "fontspec": "2.9g",
            "polyglossia": "1.60.0",
        }[package],
    )
    monkeypatch.setattr(
        latex_validation_metadata,
        "get_render_policy_version",
        lambda: "policy-v1",
    )

    metadata = latex_validation_metadata.collect_latex_validation_metadata()

    assert metadata["engine"] == "lualatex"
    assert metadata["engine_version"] == "1.18.0"
    assert isinstance(metadata["runtime_fingerprint"], str)
    assert len(metadata["runtime_fingerprint"]) == 64


def test_get_font_lualatex_loadability_returns_nested_mapping():
    """
    Ensure the accessor returns the nested v1.4 LuaLaTeX loadability block.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    font = {
        "loadability": {
            "lualatex": {
                "attempted": True,
                "loadable": False,
                "reason": "subset-empty",
                "runtime_fingerprint": "abc",
                "probe_input": "U+0041",
                "render_variants": [],
            }
        }
    }

    assert schema_accessors.get_font_lualatex_loadability(font)["reason"] == (
        "subset-empty"
    )


def test_set_lualatex_loadability_fields_creates_nested_v13_structure():
    """
    Ensure the mutator creates and populates the nested loadability structure.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    font: dict[str, object] = {}

    schema_accessors.set_lualatex_loadability_fields(
        font,
        state={
            "attempted": True,
            "loadable": False,
            "reason": "timeout",
            "runtime_fingerprint": "fp-1",
            "probe_input": "U+0E01",
        },
    )

    lualatex = schema_accessors.get_font_lualatex_loadability(font)
    assert lualatex == {
        "attempted": True,
        "loadable": False,
        "reason": "timeout",
        "runtime_fingerprint": "fp-1",
        "probe_input": "U+0E01",
        "render_variants": [],
    }


def test_set_lualatex_render_variants_persists_ordered_records():
    """
    Ensure render-variant validation records persist deterministically.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    font: dict[str, object] = {}

    schema_accessors.set_lualatex_render_variants(
        font,
        states=[
            {
                "script": "JPAN",
                "fontspec_opts": "Script=Kana",
                "attempted": True,
                "loadable": True,
                "reason": None,
                "runtime_fingerprint": "fp-2",
                "probe_input": "U+8000",
            },
            {
                "script": "BOPO",
                "fontspec_opts": "Script=Bopomofo",
                "attempted": True,
                "loadable": False,
                "reason": "fontspec error",
                "runtime_fingerprint": "fp-2",
                "probe_input": "U+3105",
            },
        ],
    )

    assert schema_accessors.get_font_lualatex_render_variants(font) == (
        {
            "script": "JPAN",
            "fontspec_opts": "Script=Kana",
            "attempted": True,
            "loadable": True,
            "reason": None,
            "runtime_fingerprint": "fp-2",
            "probe_input": "U+8000",
        },
        {
            "script": "BOPO",
            "fontspec_opts": "Script=Bopomofo",
            "attempted": True,
            "loadable": False,
            "reason": "fontspec error",
            "runtime_fingerprint": "fp-2",
            "probe_input": "U+3105",
        },
    )
