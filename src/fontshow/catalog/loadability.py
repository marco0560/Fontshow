"""
LuaLaTeX font loadability validation helpers.

This module provides best-effort runtime validation for catalog font
entries before LaTeX output is generated.

Responsibilities
----------------
- Detect whether a font entry should be checked for LuaLaTeX loadability.
- Compile a minimal temporary LuaLaTeX document for a single font.
- Filter catalog inputs so unloadable fonts are skipped deterministically.

Design principles
-----------------
Validation is conservative and best-effort:
- only existing local font files are validated;
- inventories with synthetic or missing paths keep current behavior;
- validation failures skip the offending font rather than aborting the
  catalog generation workflow.

Architectural role
------------------
This module belongs to the **catalog pipeline infrastructure layer** and
supports `create-catalog` robustness without changing the inventory
schema or the final rendering contract.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fontshow.catalog.labels import primary_script
from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.core.cli_utils import log_warn
from fontshow.core.types import ScriptISO
from fontshow.inventory.latex_validation_metadata import (
    collect_latex_validation_metadata,
)
from fontshow.inventory.schema_accessors import (
    get_font_lualatex_loadability,
    get_sample_text_value,
    get_specimen_text,
)
from fontshow.latex.policy import _get_render_policy
from fontshow.latex.render import (
    _latex_detokenize_safe,
    _renderer_option_prefix,
    _strip_ascii_control_chars,
)

if TYPE_CHECKING:
    from fontshow.core.types import CatalogFontEntryV12

_SUPPORTED_LOADABILITY_EXTENSIONS = {".ttf", ".otf", ".ttc"}


@dataclass(frozen=True)
class LoadabilityExclusion:
    """
    Structured unloadable-font record produced by catalog filtering.

    Parameters
    ----------
    identity : str
        Stable identity string used for logging.
    family : str
        Human-readable family name when available.
    path : str
        Font path associated with the skipped entry.
    detail : str | None
        Deterministic reason detail when available.
    """

    identity: str
    family: str
    path: str
    detail: str | None


@dataclass(frozen=True)
class LoadabilityFilterResult:
    """
    Result of filtering catalog fonts by LuaLaTeX loadability.

    Parameters
    ----------
    kept : list[CatalogFontEntryV12]
        Font entries retained for rendering.
    excluded : list[LoadabilityExclusion]
        Structured records for skipped unloadable fonts.
    """

    kept: list[CatalogFontEntryV12]
    excluded: list[LoadabilityExclusion]


def _is_validation_candidate(font: CatalogFontEntryV12) -> bool:
    """
    Return whether the font should be checked via LuaLaTeX.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font descriptor under consideration.

    Returns
    -------
    bool
        True when the entry points to an existing supported font file.

    Notes
    -----
    Validation is intentionally restricted to real on-disk font files so
    test inventories and inventories with missing paths keep their
    current behavior.
    """
    path = Path(str(font.get("path", "")).strip())
    return path.suffix.lower() in _SUPPORTED_LOADABILITY_EXTENSIONS and path.exists()


def _normalize_path_for_fontspec(path: Path) -> tuple[str, str]:
    """
    Normalize a filesystem path for fontspec `Path=...` usage.

    Parameters
    ----------
    path : pathlib.Path
        Font path to normalize.

    Returns
    -------
    tuple[str, str]
        Directory with trailing slash and basename component.
    """
    norm = str(path).replace("\\", "/")
    if "/" in norm:
        d, f = norm.rsplit("/", 1)
        return ((d + "/") if d else "./"), f
    return "./", norm


def _build_validation_tex(font: CatalogFontEntryV12) -> str:
    """
    Build a minimal LuaLaTeX document for a single-font loadability test.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor to validate.

    Returns
    -------
    str
        Standalone LuaLaTeX document source.
    """
    path = Path(str(font.get("path", "")))
    directory, filename = _normalize_path_for_fontspec(path)
    detok_dir = "\\detokenize{" + directory + "}"
    detok_file = "\\detokenize{" + _latex_detokenize_safe(filename) + "}"
    renderer_prefix = _renderer_option_prefix()
    options = renderer_prefix + "Path=" + detok_dir
    script0 = primary_script(font) or ""
    script0_iso = ScriptISO(script0.upper()) if script0 else ScriptISO("")
    _lang, script_opt = _get_render_policy(script0_iso)
    if script_opt:
        options += "," + script_opt
    probe_text = _validation_probe_text(font)

    return (
        "\\documentclass{article}\n"
        "\\usepackage{fontspec}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\n"
        "\\fontspec[" + options + "]{" + detok_file + "}" + probe_text + "\n"
        "\\end{document}\n"
    )


def _validation_probe_text(font: CatalogFontEntryV12) -> str:
    """
    Select a minimal probe glyph for LuaLaTeX loadability validation.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor whose specimen metadata is used for probe
        selection.

    Returns
    -------
    str
        One-character probe glyph derived from the font's own specimen
        data when possible, otherwise a conservative ASCII fallback.

    Notes
    -----
    The validator must not assume Latin coverage. It therefore prefers
    the first non-whitespace character from `specimen_text`, then from
    `sample_text.text`, and falls back to `X` only when no better probe
    exists.
    """
    candidates: list[str] = []

    specimen = get_specimen_text(font)
    if isinstance(specimen, str):
        candidates.append(specimen)

    sample_value = get_sample_text_value(font)
    if isinstance(sample_value, str):
        candidates.append(sample_value)

    for candidate in candidates:
        cleaned = _strip_ascii_control_chars(candidate)
        for ch in cleaned:
            if not ch.isspace():
                return ch

    return "X"


def _summarize_lualatex_output(output: str) -> str:
    """
    Extract a short deterministic summary from LuaLaTeX combined output.

    Parameters
    ----------
    output : str
        Combined stdout/stderr emitted by LuaLaTeX.

    Returns
    -------
    str
        Short summary suitable for warning logs.
    """
    lowered = output.lower()
    needles = (
        "no glyphs in subset",
        "fontspec error",
        "fatal error",
        "luaotfload",
        "! ",
    )
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(needle in stripped.lower() for needle in needles):
            return stripped

    for line in output.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped

    if "timeout" in lowered:
        return "LuaLaTeX validation timed out"
    return "LuaLaTeX load failure"


def validate_font_loadability(
    font: CatalogFontEntryV12,
) -> tuple[bool, str | None]:
    """
    Validate whether a font can be loaded by LuaLaTeX.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor to validate.

    Returns
    -------
    tuple[bool, str | None]
        Pair ``(ok, detail)`` where ``detail`` contains a short failure
        summary when validation fails.

    Notes
    -----
    Validation compiles a minimal one-font document in a temporary
    directory. Non-zero exit status or subset-empty diagnostics cause
    rejection.
    """
    tex_source = _build_validation_tex(font)
    lualatex_bin = shutil.which("lualatex")
    if lualatex_bin is None:
        return False, "lualatex not available"

    with tempfile.TemporaryDirectory(prefix="fontshow-loadability-") as tmpdir:
        tmp_path = Path(tmpdir)
        tex_path = tmp_path / "probe.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    lualatex_bin,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(tmp_path),
                    str(tex_path),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return False, "LuaLaTeX validation timed out"

    output = proc.stdout or ""
    lowered = output.lower()
    if proc.returncode != 0:
        return False, _summarize_lualatex_output(output)
    if "no glyphs in subset" in lowered:
        return False, "no glyphs in subset"
    return True, None


def _current_runtime_fingerprint() -> str | None:
    """
    Collect the current LuaLaTeX runtime fingerprint for catalog fallback.

    Parameters
    ----------
    None

    Returns
    -------
    str | None
        Runtime fingerprint when the local environment can be
        characterized, otherwise ``None``.
    """
    metadata = collect_latex_validation_metadata()
    fingerprint = metadata.get("runtime_fingerprint")
    return fingerprint if isinstance(fingerprint, str) and fingerprint else None


def _persisted_loadability_state(
    font: CatalogFontEntryV12,
    *,
    runtime_fingerprint: str | None,
) -> tuple[str, str | None]:
    """
    Classify the persisted loadability state for a catalog font entry.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font descriptor to inspect.
    runtime_fingerprint : str | None
        Current runtime fingerprint used for staleness checks.

    Returns
    -------
    tuple[str, str | None]
        Pair ``(state, detail)`` where ``state`` is one of
        ``trusted-pass``, ``trusted-fail``, ``needs-runtime``, or
        ``skip-runtime``.
    """
    persisted = get_font_lualatex_loadability(font)
    if not persisted:
        return "needs-runtime", None

    if not bool(persisted.get("attempted", False)):
        return "needs-runtime", None

    persisted_fingerprint = persisted.get("runtime_fingerprint")
    if not isinstance(persisted_fingerprint, str) or not persisted_fingerprint:
        return "needs-runtime", None

    if runtime_fingerprint is None:
        return "skip-runtime", None

    if persisted_fingerprint != runtime_fingerprint:
        return "needs-runtime", None

    persisted_loadable = persisted.get("loadable")
    if persisted_loadable is True:
        return "trusted-pass", None
    if persisted_loadable is False:
        persisted_reason = persisted.get("reason")
        detail = persisted_reason if isinstance(persisted_reason, str) else None
        return "trusted-fail", detail
    return "needs-runtime", None


def filter_loadable_catalog_fonts(
    fonts: list[CatalogFontEntryV12],
) -> list[CatalogFontEntryV12]:
    """
    Filter out fonts that fail best-effort LuaLaTeX validation.

    Parameters
    ----------
    fonts : list[CatalogFontEntryV12]
        Catalog font entries ready for rendering.

    Returns
    -------
    list[CatalogFontEntryV12]
        Original entries except those proven unloadable by LuaLaTeX.

    Notes
    -----
    If `lualatex` is unavailable, validation is skipped and the input is
    returned unchanged to preserve the command's current API behavior.
    """
    return filter_loadable_catalog_fonts_with_report(fonts).kept


def filter_loadable_catalog_fonts_with_report(
    fonts: list[CatalogFontEntryV12],
) -> LoadabilityFilterResult:
    """
    Filter fonts and collect structured unloadable-font reporting data.

    Parameters
    ----------
    fonts : list[CatalogFontEntryV12]
        Catalog font entries ready for rendering.

    Returns
    -------
    LoadabilityFilterResult
        Kept render set plus structured exclusion records.
    """
    runtime_fingerprint = _current_runtime_fingerprint()
    candidates = [font for font in fonts if _is_validation_candidate(font)]
    if not candidates:
        return LoadabilityFilterResult(kept=list(fonts), excluded=[])

    if runtime_fingerprint is None and shutil.which("lualatex") is None:
        log_warn("lualatex not available; skipping font loadability validation")
        return LoadabilityFilterResult(kept=list(fonts), excluded=[])

    kept: list[CatalogFontEntryV12] = []
    excluded: list[LoadabilityExclusion] = []
    for font in fonts:
        if not _is_validation_candidate(font):
            kept.append(font)
            continue

        state, detail = _persisted_loadability_state(
            font,
            runtime_fingerprint=runtime_fingerprint,
        )
        if state == "trusted-pass":
            kept.append(font)
            continue
        if state == "trusted-fail":
            pass
        elif state == "skip-runtime":
            kept.append(font)
            continue
        else:
            ok, detail = validate_font_loadability(font)
            if ok:
                kept.append(font)
                continue

        identity = (
            str(font.get("unique_font_id", "")).strip()
            or str(font.get("full_name", "")).strip()
            or str(font.get("family", "")).strip()
            or str(font.get("path", "")).strip()
            or "unknown-font"
        )
        log_warn(f"Font skipped: {identity}")
        log_warn("Reason: LuaLaTeX load failure")
        log_warn(f"Detail: {detail or 'LuaLaTeX load failure'}")
        excluded.append(
            LoadabilityExclusion(
                identity=identity,
                family=str(font.get("family", "")).strip(),
                path=str(font.get("path", "")).strip(),
                detail=detail,
            )
        )

    return LoadabilityFilterResult(kept=kept, excluded=excluded)
