"""
Exercise catalog loadability validation helpers.

Responsibilities
----------------
- Verify candidate selection only validates real supported font files.
- Ensure LuaLaTeX validation failures are summarized deterministically.
- Ensure catalog filtering skips unloadable fonts without aborting.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

from fontshow.catalog import loadability


def test_is_validation_candidate_requires_existing_supported_font_file(tmp_path):
    """
    Ensure validation only targets existing supported font files.
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")

    assert loadability._is_validation_candidate({"path": str(font_path)}) is True
    assert (
        loadability._is_validation_candidate({"path": str(tmp_path / "Missing.ttf")})
        is False
    )
    assert (
        loadability._is_validation_candidate({"path": str(tmp_path / "Alpha.txt")})
        is False
    )


def test_validate_font_loadability_returns_subset_failure(monkeypatch, tmp_path):
    """
    Ensure subset-empty diagnostics produce a deterministic failure detail.
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")

    monkeypatch.setattr(
        loadability.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout="warning: no glyphs in subset"
        ),
    )

    ok, detail = loadability.validate_font_loadability({"path": str(font_path)})

    assert ok is False
    assert detail == "no glyphs in subset"


def test_validation_probe_text_prefers_specimen_then_sample_text():
    """
    Ensure loadability probes use the font's own specimen data first.
    """
    assert (
        loadability._validation_probe_text(
            {
                "specimen_text": "  ابج",
                "sample_text": {"text": "XYZ"},
            }
        )
        == "ا"
    )
    assert (
        loadability._validation_probe_text(
            {
                "specimen_text": "   ",
                "sample_text": {"text": "  กข"},
            }
        )
        == "ก"
    )
    assert loadability._validation_probe_text({"specimen_text": "   "}) == "X"


def test_build_validation_tex_uses_specimen_probe_glyph(tmp_path):
    """
    Ensure the generated probe document does not hard-code Latin `X`.
    """
    font_path = tmp_path / "Arabic.ttf"
    font_path.write_bytes(b"")

    tex = loadability._build_validation_tex(
        {
            "path": str(font_path),
            "specimen_text": "ابج",
            "sample_text": {"text": "XYZ"},
        }
    )

    assert "}ا\n\\end{document}\n" in tex
    assert "}X\n\\end{document}\n" not in tex


def test_build_validation_tex_reuses_render_policy_script_option(monkeypatch, tmp_path):
    """
    Ensure loadability validation uses the same script option as rendering.
    """
    font_path = tmp_path / "Georgian.ttf"
    font_path.write_bytes(b"")

    monkeypatch.setattr(loadability, "primary_script", lambda _font: "geor")
    monkeypatch.setattr(
        loadability, "_get_render_policy", lambda _script: ("", "Script=Georgian")
    )

    tex = loadability._build_validation_tex(
        {
            "path": str(font_path),
            "specimen_text": "ქართული",
        }
    )

    assert "[Renderer=Harfbuzz,Path=\\detokenize{" in tex
    assert ",Script=Georgian]" in tex


def test_validate_font_loadability_returns_first_relevant_error_line(
    monkeypatch, tmp_path
):
    """
    Ensure non-zero LuaLaTeX runs return a compact error summary.
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")

    monkeypatch.setattr(
        loadability.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout='preamble\n! Font \\"Alpha\\" cannot be found.\ntrailer\n',
        ),
    )

    ok, detail = loadability.validate_font_loadability({"path": str(font_path)})

    assert ok is False
    assert detail == '! Font \\"Alpha\\" cannot be found.'


def test_validate_font_loadability_handles_timeout(monkeypatch, tmp_path):
    """
    Ensure subprocess timeouts become deterministic validation failures.
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["lualatex"], timeout=1)

    monkeypatch.setattr(loadability.subprocess, "run", _timeout)

    ok, detail = loadability.validate_font_loadability({"path": str(font_path)})

    assert ok is False
    assert detail == "LuaLaTeX validation timed out"


def test_filter_loadable_catalog_fonts_warns_and_keeps_fonts_without_lualatex(
    monkeypatch, tmp_path
):
    """
    Ensure missing LuaLaTeX does not change the input font set.
    """
    font_path = tmp_path / "Alpha.ttf"
    font_path.write_bytes(b"")
    warnings: list[str] = []

    monkeypatch.setattr(loadability.shutil, "which", lambda _name: None)
    monkeypatch.setattr(loadability, "log_warn", warnings.append)

    fonts = [{"path": str(font_path), "family": "Alpha"}]

    assert loadability.filter_loadable_catalog_fonts(fonts) == fonts
    assert warnings == ["lualatex not available; skipping font loadability validation"]


def test_filter_loadable_catalog_fonts_skips_only_failed_candidates(
    monkeypatch, tmp_path
):
    """
    Ensure unloadable fonts are removed while non-candidates are preserved.
    """
    good_path = tmp_path / "Alpha.ttf"
    bad_path = tmp_path / "Broken.ttf"
    good_path.write_bytes(b"")
    bad_path.write_bytes(b"")
    warnings: list[str] = []

    monkeypatch.setattr(loadability.shutil, "which", lambda _name: "/usr/bin/lualatex")
    monkeypatch.setattr(loadability, "log_warn", warnings.append)

    def _validate(font):
        return (False, "broken cmap") if "Broken" in str(font["path"]) else (True, None)

    monkeypatch.setattr(loadability, "validate_font_loadability", _validate)

    fonts = [
        {
            "path": str(good_path),
            "family": "Alpha",
            "unique_font_id": "good-1",
        },
        {
            "path": str(bad_path),
            "family": "Broken",
            "unique_font_id": "bad-1",
        },
        {
            "path": str(tmp_path / "missing.ttf"),
            "family": "Missing",
            "unique_font_id": "missing-1",
        },
    ]

    kept = loadability.filter_loadable_catalog_fonts(fonts)

    assert kept == [fonts[0], fonts[2]]
    assert warnings == [
        "Font skipped: bad-1",
        "Reason: LuaLaTeX load failure",
        "Detail: broken cmap",
    ]
