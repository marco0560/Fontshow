"""
Inventory-side LuaLaTeX loadability probing.

This module computes persisted LuaLaTeX loadability for inventory font
entries during `dump-fonts`.

Responsibilities
----------------
- Select loadability candidates from schema v1.3 inventory entries.
- Build deterministic batched LuaLaTeX probe documents.
- Isolate failed fonts with recursive batch subdivision.
- Persist per-font loadability state without requiring real TeX in tests.

Design principles
-----------------
The probing flow is deterministic and serial by default. Successful
batches mark many fonts at once; failed batches are recursively split to
attribute failures without returning to one process per font in the
common all-success path.

Architectural role
------------------
This module belongs to the **inventory subsystem** because persisted
loadability is produced at inventory-generation time and stored in the
inventory schema.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.inventory.schema_accessors import (
    get_font_typography,
    get_sample_text_value,
    get_specimen_text,
    set_lualatex_loadability_fields,
)
from fontshow.latex.render import (
    _latex_detokenize_safe,
    _renderer_option_prefix,
    _strip_ascii_control_chars,
)

_SUPPORTED_LOADABILITY_EXTENSIONS = {".ttf", ".otf", ".ttc"}
_DEFAULT_BATCH_SIZE = 32


@dataclass(frozen=True)
class _ProbeCandidate:
    """
    Immutable inventory font selected for LuaLaTeX probing.

    Parameters
    ----------
    font_index : int
        Index of the mutable font entry inside the inventory list.
    path : pathlib.Path
        Existing font path used for path-based loading.
    probe_text : str
        Deterministic single-character probe glyph.
    probe_input : str
        Deterministic persisted summary of the probe input.
    fontspec_opts : str | None
        Optional render-policy fontspec options already present on the
        inventory entry.
    """

    font_index: int
    path: Path
    probe_text: str
    probe_input: str
    fontspec_opts: str | None


def _is_inventory_validation_candidate(font: MutableMapping[str, Any]) -> bool:
    """
    Return whether an inventory font entry can be loadability-probed.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Inventory font entry to inspect.

    Returns
    -------
    bool
        True when the entry points to an existing supported font file.
    """
    path = Path(str(font.get("path", "")).strip())
    return path.suffix.lower() in _SUPPORTED_LOADABILITY_EXTENSIONS and path.exists()


def _probe_text_from_font(font: MutableMapping[str, Any]) -> str:
    """
    Select a deterministic one-character probe glyph for a font entry.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Inventory font entry whose typography metadata is inspected.

    Returns
    -------
    str
        First non-whitespace character from specimen text, then sample
        text, otherwise ``X``.
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


def _probe_input_from_text(text: str) -> str:
    """
    Build the persisted probe-input summary for a one-character probe.

    Parameters
    ----------
    text : str
        Probe glyph selected for the font entry.

    Returns
    -------
    str
        Stable code-point representation such as ``U+0041``.
    """
    codepoint = ord(text[0])
    return f"U+{codepoint:04X}"


def _normalize_path_for_fontspec(path: Path) -> tuple[str, str]:
    """
    Normalize a font path for path-based `fontspec` loading.

    Parameters
    ----------
    path : pathlib.Path
        Font path to normalize.

    Returns
    -------
    tuple[str, str]
        Directory with trailing slash and basename component.
    """
    normalized = str(path).replace("\\", "/")
    if "/" in normalized:
        directory, filename = normalized.rsplit("/", 1)
        return ((directory + "/") if directory else "./"), filename
    return "./", normalized


def _fontspec_options(candidate: _ProbeCandidate) -> str:
    """
    Build deterministic `fontspec` options for a probe candidate.

    Parameters
    ----------
    candidate : _ProbeCandidate
        Candidate whose path and optional render policy are applied.

    Returns
    -------
    str
        Comma-separated option string for `fontspec`.
    """
    directory, _filename = _normalize_path_for_fontspec(candidate.path)
    options = _renderer_option_prefix() + "Path=" + "\\detokenize{" + directory + "}"
    if candidate.fontspec_opts:
        options += "," + candidate.fontspec_opts
    return options


def _render_probe_snippet(candidate: _ProbeCandidate) -> str:
    """
    Render the TeX snippet for one probe candidate.

    Parameters
    ----------
    candidate : _ProbeCandidate
        Candidate to render into the batch document.

    Returns
    -------
    str
        TeX fragment that emits begin/ok markers around the probe.
    """
    _directory, filename = _normalize_path_for_fontspec(candidate.path)
    detok_file = "\\detokenize{" + _latex_detokenize_safe(filename) + "}"
    return (
        f"\\typeout{{FONTSHOW_LOAD_BEGIN:{candidate.font_index}}}\n"
        f"\\fontspec[{_fontspec_options(candidate)}]{{{detok_file}}}"
        f"{candidate.probe_text}\n"
        f"\\typeout{{FONTSHOW_LOAD_OK:{candidate.font_index}}}\n"
    )


def _build_batch_tex(candidates: Sequence[_ProbeCandidate]) -> str:
    """
    Build the LuaLaTeX document for a probe batch.

    Parameters
    ----------
    candidates : collections.abc.Sequence[_ProbeCandidate]
        Candidates included in the batch.

    Returns
    -------
    str
        Standalone batch probe document.
    """
    body = "".join(_render_probe_snippet(candidate) for candidate in candidates)
    return (
        "\\documentclass{article}\n"
        "\\usepackage{fontspec}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\n"
        f"{body}"
        "\\end{document}\n"
    )


def _summarize_lualatex_output(output: str) -> str:
    """
    Extract a short deterministic failure detail from LuaLaTeX output.

    Parameters
    ----------
    output : str
        Combined stdout/stderr emitted by LuaLaTeX.

    Returns
    -------
    str
        Compact deterministic summary line.
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


def _successful_candidate_ids(output: str) -> set[int]:
    """
    Extract successfully completed candidate ids from batch output.

    Parameters
    ----------
    output : str
        Combined stdout/stderr emitted by LuaLaTeX.

    Returns
    -------
    set[int]
        Candidate ids that emitted an ``OK`` marker before batch exit.
    """
    prefix = "FONTSHOW_LOAD_OK:"
    ids: set[int] = set()
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        try:
            ids.add(int(stripped.removeprefix(prefix)))
        except ValueError:
            continue
    return ids


def _run_lualatex_batch(
    candidates: Sequence[_ProbeCandidate],
    *,
    lualatex_bin: str,
) -> tuple[int, str]:
    """
    Execute one LuaLaTeX batch probe.

    Parameters
    ----------
    candidates : collections.abc.Sequence[_ProbeCandidate]
        Candidates bundled into the batch.
    lualatex_bin : str
        Resolved executable path for the LuaLaTeX engine.

    Returns
    -------
    tuple[int, str]
        Process return code and combined output.
    """
    tex_source = _build_batch_tex(candidates)

    with tempfile.TemporaryDirectory(prefix="fontshow-loadability-batch-") as tmpdir:
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
            return 124, "LuaLaTeX validation timed out"

    return proc.returncode, proc.stdout or ""


def _split_candidates(
    candidates: Sequence[_ProbeCandidate],
) -> tuple[list[_ProbeCandidate], list[_ProbeCandidate]]:
    """
    Split a candidate sequence into two deterministic non-empty halves.

    Parameters
    ----------
    candidates : collections.abc.Sequence[_ProbeCandidate]
        Candidates to divide.

    Returns
    -------
    tuple[list[_ProbeCandidate], list[_ProbeCandidate]]
        Left and right halves.
    """
    midpoint = len(candidates) // 2
    return list(candidates[:midpoint]), list(candidates[midpoint:])


def _resolve_batch_results(
    candidates: Sequence[_ProbeCandidate],
    *,
    lualatex_bin: str,
) -> dict[int, dict[str, Any]]:
    """
    Resolve loadability results for a candidate batch.

    Parameters
    ----------
    candidates : collections.abc.Sequence[_ProbeCandidate]
        Candidates to resolve.
    lualatex_bin : str
        Resolved LuaLaTeX executable path.

    Returns
    -------
    dict[int, dict[str, Any]]
        Per-font persisted loadability state keyed by font index.
    """
    if not candidates:
        return {}

    returncode, output = _run_lualatex_batch(candidates, lualatex_bin=lualatex_bin)
    detail = _summarize_lualatex_output(output)
    successful_ids = _successful_candidate_ids(output)

    if returncode == 0 and len(successful_ids) == len(candidates):
        return {
            candidate.font_index: {
                "attempted": True,
                "loadable": True,
                "reason": None,
                "probe_input": candidate.probe_input,
            }
            for candidate in candidates
        }

    results: dict[int, dict[str, Any]] = {
        candidate.font_index: {
            "attempted": True,
            "loadable": True,
            "reason": None,
            "probe_input": candidate.probe_input,
        }
        for candidate in candidates
        if candidate.font_index in successful_ids
    }
    unresolved = [
        candidate
        for candidate in candidates
        if candidate.font_index not in successful_ids
    ]

    if len(unresolved) == 1:
        candidate = unresolved[0]
        results[candidate.font_index] = {
            "attempted": True,
            "loadable": False,
            "reason": detail,
            "probe_input": candidate.probe_input,
        }
        return results

    left, right = _split_candidates(unresolved)
    if left:
        results.update(_resolve_batch_results(left, lualatex_bin=lualatex_bin))
    if right:
        results.update(_resolve_batch_results(right, lualatex_bin=lualatex_bin))
    return results


def _chunk_candidates(
    candidates: Sequence[_ProbeCandidate],
    *,
    batch_size: int,
) -> list[list[_ProbeCandidate]]:
    """
    Chunk candidates into deterministic serial batches.

    Parameters
    ----------
    candidates : collections.abc.Sequence[_ProbeCandidate]
        Ordered candidates to partition.
    batch_size : int
        Maximum batch size.

    Returns
    -------
    list[list[_ProbeCandidate]]
        Ordered candidate chunks.
    """
    if batch_size <= 0:
        return [list(candidates)]
    return [
        list(candidates[start : start + batch_size])
        for start in range(0, len(candidates), batch_size)
    ]


def probe_and_persist_lualatex_loadability(
    fonts: list[MutableMapping[str, Any]],
    *,
    validation_metadata: MutableMapping[str, Any],
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> None:
    """
    Probe and persist LuaLaTeX loadability for inventory fonts.

    Parameters
    ----------
    fonts : list[collections.abc.MutableMapping[str, Any]]
        Mutable inventory font entries updated in place.
    validation_metadata : collections.abc.MutableMapping[str, Any]
        Inventory-level ``metadata.validation.lualatex`` block updated
        in place.
    batch_size : int, optional
        Maximum number of candidate fonts bundled into one serial batch.

    Returns
    -------
    None
    """
    lualatex_bin = shutil.which("lualatex")
    if lualatex_bin is None:
        return

    runtime_fingerprint = validation_metadata.get("runtime_fingerprint")
    if not isinstance(runtime_fingerprint, str) or not runtime_fingerprint:
        return

    candidates: list[_ProbeCandidate] = []
    for index, font in enumerate(fonts):
        if not _is_inventory_validation_candidate(font):
            continue

        typography = get_font_typography(font)
        render_policy = typography.get("render_policy")
        fontspec_opts: str | None = None
        if isinstance(render_policy, Mapping):
            raw_opts = render_policy.get("fontspec_opts")
            if isinstance(raw_opts, str) and raw_opts.strip():
                fontspec_opts = raw_opts.strip()

        probe_text = _probe_text_from_font(font)
        candidates.append(
            _ProbeCandidate(
                font_index=index,
                path=Path(str(font.get("path", ""))),
                probe_text=probe_text,
                probe_input=_probe_input_from_text(probe_text),
                fontspec_opts=fontspec_opts,
            )
        )

    if not candidates:
        return

    validation_metadata["attempted"] = True
    results: dict[int, dict[str, Any]] = {}
    for chunk in _chunk_candidates(candidates, batch_size=batch_size):
        results.update(_resolve_batch_results(chunk, lualatex_bin=lualatex_bin))

    for candidate in candidates:
        state = results.get(candidate.font_index)
        if state is None:
            continue
        set_lualatex_loadability_fields(
            fonts[candidate.font_index],
            state={
                "attempted": state["attempted"],
                "loadable": state["loadable"],
                "reason": state["reason"],
                "runtime_fingerprint": runtime_fingerprint,
                "probe_input": state["probe_input"],
            },
        )


def inventory_has_attempted_lualatex_validation(metadata: dict[str, Any]) -> bool:
    """
    Return whether inventory metadata already records attempted probing.

    Parameters
    ----------
    metadata : dict[str, Any]
        Inventory metadata mapping to inspect.

    Returns
    -------
    bool
        True when ``metadata.validation.lualatex.attempted`` is true.
    """
    validation = metadata.get("validation")
    if not isinstance(validation, dict):
        return False
    lualatex = validation.get("lualatex")
    if not isinstance(lualatex, dict):
        return False
    return bool(lualatex.get("attempted", False))
