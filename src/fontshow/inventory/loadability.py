"""
Inventory-side LuaLaTeX loadability probing.

This module computes persisted LuaLaTeX loadability for inventory font
entries during `dump-fonts`.

Responsibilities
----------------
- Select loadability candidates from schema v1.4 inventory entries.
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
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.core.types import ScriptISO
from fontshow.inventory.schema_accessors import (
    get_font_lualatex_loadability,
    get_font_typography,
    get_sample_text_value,
    get_specimen_text,
    set_lualatex_loadability_fields,
    set_lualatex_render_variants,
)
from fontshow.inventory.specimens import (
    MIN_SAMPLE_GLYPHS,
    _script_fallback_specimen,
    _specimen_collect_cmap,
    _specimen_preference,
    _specimen_skip,
)
from fontshow.latex.policy import _get_render_policy
from fontshow.latex.render import (
    _latex_detokenize_safe,
    _renderer_option_prefix,
    _strip_ascii_control_chars,
)
from fontshow.ontology.language_tables import SCRIPT_INFO

_SUPPORTED_LOADABILITY_EXTENSIONS = {".ttf", ".otf", ".ttc"}
_DEFAULT_BATCH_SIZE = 32


@dataclass(frozen=True)
class _ProbeCandidate:
    """
    Immutable inventory font selected for LuaLaTeX probing.

    Parameters
    ----------
    candidate_index : int
        Stable per-candidate identifier used for batch attribution.
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
    script : str | None
        Optional ISO-15924 script identifier associated with the probe.
    specimen_text : str | None
        Validated specimen selected for the render-path candidate.
    specimen_glyph_count : int | None
        Base-glyph count for ``specimen_text`` after filtering.
    specimen_strategy : str | None
        Deterministic strategy label describing how ``specimen_text``
        was produced.
    """

    candidate_index: int
    font_index: int
    path: Path
    probe_text: str
    probe_input: str
    fontspec_opts: str | None
    script: str | None = None
    specimen_text: str | None = None
    specimen_glyph_count: int | None = None
    specimen_strategy: str | None = None


def _is_inventory_validation_candidate(font: Mapping[str, Any]) -> bool:
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


def _loadability_identity(font: Mapping[str, Any]) -> str:
    """
    Build a stable identity for loadability readiness diagnostics.

    Parameters
    ----------
    font : collections.abc.Mapping[str, Any]
        Inventory font entry being reported.

    Returns
    -------
    str
        Human-readable identity using the best available font metadata.
    """
    full_name = str(font.get("full_name", "")).strip()
    family = str(font.get("family", "")).strip()
    path = str(font.get("path", "")).strip()
    font_id = str(font.get("unique_font_id", "")).strip()

    label = full_name or family or path or font_id or "unknown-font"
    parts = [label]
    if path and path != label:
        parts.append(f"path={path}")
    if font_id and font_id != label:
        parts.append(f"id={font_id}")
    return " | ".join(parts)


def validate_persisted_lualatex_loadability(
    fonts: Sequence[Mapping[str, Any]],
    validation_metadata: Mapping[str, Any],
) -> list[str]:
    """
    Validate that persisted LuaLaTeX loadability is catalog-ready.

    Parameters
    ----------
    fonts : collections.abc.Sequence[collections.abc.Mapping[str, Any]]
        Inventory font entries to inspect.
    validation_metadata : collections.abc.Mapping[str, Any]
        Current ``metadata.validation.lualatex`` block whose runtime
        fingerprint is authoritative for the inventory.

    Returns
    -------
    list[str]
        Deterministic error messages. An empty list means all existing
        supported font-file candidates have complete persisted loadability.
    """
    candidates = [font for font in fonts if _is_inventory_validation_candidate(font)]
    if not candidates:
        return []

    errors: list[str] = []
    if not bool(validation_metadata.get("attempted", False)):
        errors.append("metadata.validation.lualatex.attempted is not true")

    expected_fingerprint = validation_metadata.get("runtime_fingerprint")
    if not isinstance(expected_fingerprint, str) or not expected_fingerprint:
        errors.append("metadata.validation.lualatex.runtime_fingerprint is missing")

    for font in candidates:
        identity = _loadability_identity(font)
        persisted = get_font_lualatex_loadability(font)
        if not persisted:
            errors.append(f"{identity}: missing loadability.lualatex")
            continue

        if not bool(persisted.get("attempted", False)):
            errors.append(f"{identity}: loadability.lualatex.attempted is not true")

        persisted_fingerprint = persisted.get("runtime_fingerprint")
        if not isinstance(persisted_fingerprint, str) or not persisted_fingerprint:
            errors.append(
                f"{identity}: loadability.lualatex.runtime_fingerprint is missing"
            )
        elif (
            isinstance(expected_fingerprint, str)
            and expected_fingerprint
            and persisted_fingerprint != expected_fingerprint
        ):
            errors.append(
                f"{identity}: loadability.lualatex.runtime_fingerprint mismatch"
            )

        if not isinstance(persisted.get("loadable"), bool):
            errors.append(f"{identity}: loadability.lualatex.loadable is not boolean")

    return errors


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


def _probe_text_from_sample(sample: str) -> str:
    """
    Select the first non-whitespace glyph from a deterministic sample.

    Parameters
    ----------
    sample : str
        Sample text already selected for a specific render path.

    Returns
    -------
    str
        First non-whitespace glyph, or an empty string when the sample
        contains no usable probe glyph.
    """
    cleaned = _strip_ascii_control_chars(sample)
    for ch in cleaned:
        if not ch.isspace():
            return ch
    return ""


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
        f"\\typeout{{FONTSHOW_LOAD_BEGIN:{candidate.candidate_index}}}\n"
        f"\\fontspec[{_fontspec_options(candidate)}]{{{detok_file}}}"
        f"{candidate.probe_text}\n"
        f"\\typeout{{FONTSHOW_LOAD_OK:{candidate.candidate_index}}}\n"
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
            Per-candidate persisted loadability state keyed by candidate
            index.
    """
    if not candidates:
        return {}

    returncode, output = _run_lualatex_batch(candidates, lualatex_bin=lualatex_bin)
    detail = _summarize_lualatex_output(output)
    successful_ids = _successful_candidate_ids(output)

    if returncode == 0 and len(successful_ids) == len(candidates):
        return {
            candidate.candidate_index: {
                "attempted": True,
                "loadable": True,
                "reason": None,
                "probe_input": candidate.probe_input,
            }
            for candidate in candidates
        }

    results: dict[int, dict[str, Any]] = {
        candidate.candidate_index: {
            "attempted": True,
            "loadable": True,
            "reason": None,
            "probe_input": candidate.probe_input,
        }
        for candidate in candidates
        if candidate.candidate_index in successful_ids
    }
    unresolved = [
        candidate
        for candidate in candidates
        if candidate.candidate_index not in successful_ids
    ]

    if len(unresolved) == 1:
        candidate = unresolved[0]
        results[candidate.candidate_index] = {
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


def _resolve_candidate_chunks(
    chunks: Sequence[Sequence[_ProbeCandidate]],
    *,
    lualatex_bin: str,
    jobs: int,
) -> dict[int, dict[str, Any]]:
    """
    Resolve candidate chunks with deterministic result collation.

    Parameters
    ----------
    chunks : collections.abc.Sequence[collections.abc.Sequence[_ProbeCandidate]]
        Ordered candidate chunks to probe.
    lualatex_bin : str
        Resolved LuaLaTeX executable path.
    jobs : int
        Maximum number of chunks to probe concurrently. Values smaller
        than ``2`` use serial execution.

    Returns
    -------
    dict[int, dict[str, Any]]
        Per-candidate persisted loadability state keyed by candidate index.
    """
    if jobs < 2 or len(chunks) < 2:
        results: dict[int, dict[str, Any]] = {}
        for chunk in chunks:
            results.update(_resolve_batch_results(chunk, lualatex_bin=lualatex_bin))
        return results

    max_workers = min(jobs, len(chunks))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_resolve_batch_results, chunk, lualatex_bin=lualatex_bin)
            for chunk in chunks
        ]

    parallel_results: dict[int, dict[str, Any]] = {}
    for future in futures:
        parallel_results.update(future.result())
    return parallel_results


def probe_and_persist_lualatex_loadability(
    fonts: list[MutableMapping[str, Any]],
    *,
    validation_metadata: MutableMapping[str, Any],
    batch_size: int = _DEFAULT_BATCH_SIZE,
    jobs: int = 1,
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
    jobs : int, optional
        Maximum number of candidate chunks to probe concurrently. The
        default keeps production probing serial.

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
                candidate_index=len(candidates),
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
    results = _resolve_candidate_chunks(
        _chunk_candidates(candidates, batch_size=batch_size),
        lualatex_bin=lualatex_bin,
        jobs=jobs,
    )

    for candidate in candidates:
        state = results.get(candidate.candidate_index)
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


def _ordered_render_variant_scripts(font: MutableMapping[str, Any]) -> list[ScriptISO]:
    """
    Return deterministic script candidates for parse-time render probing.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Enriched inventory font entry being prepared for catalog use.

    Returns
    -------
    list[ScriptISO]
        Ordered script candidates matching the catalog renderer's
        multi-specimen selection policy.
    """
    typography = get_font_typography(font)
    primary_raw = typography.get("primary_script")
    ordered_raw: list[str] = []
    if isinstance(primary_raw, str) and primary_raw.strip():
        ordered_raw.append(primary_raw)

    inference = font.get("inference")
    if isinstance(inference, Mapping):
        scripts_raw = inference.get("scripts")
        if isinstance(scripts_raw, list):
            ordered_raw.extend(str(script) for script in scripts_raw)

    coverage = font.get("coverage")
    if isinstance(coverage, Mapping):
        scripts_raw = coverage.get("scripts")
        if isinstance(scripts_raw, list):
            ordered_raw.extend(str(script) for script in scripts_raw)

    seen: set[str] = set()
    normalized: list[ScriptISO] = []
    for raw in ordered_raw:
        cleaned = str(raw).strip().upper()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(ScriptISO(cleaned))

    primary_script = normalized[0] if normalized else None
    secondary_scripts = normalized[1:] if primary_script is not None else normalized

    def _sort_key(script_iso: ScriptISO) -> tuple[int, str]:
        info = SCRIPT_INFO.get(script_iso)
        if str(script_iso) == "LATN":
            return (0, str(script_iso))
        if isinstance(info, Mapping) and bool(info.get("rtl", False)):
            return (1, str(script_iso))
        return (2, str(script_iso))

    ordered: list[ScriptISO] = []
    if primary_script is not None:
        ordered.append(primary_script)
    ordered.extend(sorted(secondary_scripts, key=_sort_key))
    return ordered[:20]


def _render_variant_specimen(
    font: MutableMapping[str, Any], script_iso: ScriptISO
) -> str:
    """
    Return the sample text used to validate one render-path variant.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Enriched inventory font entry being validated.
    script_iso : ScriptISO
        Script code for the render-path candidate.

    Returns
    -------
    str
        Deterministic sample for the render path, or an empty string
        when the variant should not be validated.
    """
    typography = get_font_typography(font)
    primary_raw = typography.get("primary_script")
    primary_iso = (
        ScriptISO(str(primary_raw).strip().upper())
        if isinstance(primary_raw, str) and str(primary_raw).strip()
        else ScriptISO("")
    )
    if str(script_iso) == str(primary_iso):
        specimen = get_specimen_text(font)
        return _strip_ascii_control_chars(specimen) if isinstance(specimen, str) else ""

    variant_path = str(font.get("path", "")).strip()
    if not variant_path:
        return ""

    cps = _specimen_collect_cmap(variant_path, None)
    if not cps:
        return ""

    filtered, _glyphs, _strategy = _script_fallback_specimen(script_iso, cps)
    if filtered is not None:
        return _strip_ascii_control_chars(filtered)
    return _render_variant_cmap_fallback(cps, script_iso)


def _render_variant_cmap_fallback(cps: set[int], script_iso: ScriptISO) -> str:
    """
    Build a deterministic script-scoped fallback specimen from cmap data.

    Parameters
    ----------
    cps : set[int]
        Supported Unicode codepoints extracted from the font cmap.
    script_iso : ScriptISO
        Script whose ontology ranges constrain the fallback selection.

    Returns
    -------
    str
        Short deterministic script-constrained sample, or an empty
        string when no suitable codepoints are available.

    Notes
    -----
    This helper is used only for render-variant persistence. It avoids
    leaking unrelated scripts such as Latin into a secondary-script
    probe when the curated specimen is too short after cmap filtering.
    """
    script_info = SCRIPT_INFO.get(script_iso)
    if not isinstance(script_info, Mapping):
        return ""

    ranges = script_info.get("unicode_max_ranges")
    if not isinstance(ranges, list) or not ranges:
        return ""

    chosen: list[int] = []
    for cp in sorted(cps, key=_specimen_preference):
        if _specimen_skip(cp):
            continue
        if not any(start <= cp <= end for start, end in ranges):
            continue
        chosen.append(cp)
        if len(chosen) >= MIN_SAMPLE_GLYPHS:
            break

    if not chosen:
        return ""

    return "".join(chr(cp) for cp in chosen)


def _render_variant_specimen_details(
    font: MutableMapping[str, Any], script_iso: ScriptISO
) -> tuple[str, int, str] | None:
    """
    Return persisted specimen details for a render-path candidate.

    Parameters
    ----------
    font : collections.abc.MutableMapping[str, Any]
        Enriched inventory font entry being validated.
    script_iso : ScriptISO
        Script code for the render-path candidate.

    Returns
    -------
    tuple[str, int, str] | None
        ``(specimen_text, glyph_count, strategy)`` when a usable
        render-variant sample exists, otherwise ``None``.
    """
    typography = get_font_typography(font)
    primary_raw = typography.get("primary_script")
    primary_iso = (
        ScriptISO(str(primary_raw).strip().upper())
        if isinstance(primary_raw, str) and str(primary_raw).strip()
        else ScriptISO("")
    )
    if str(script_iso) == str(primary_iso):
        specimen = get_specimen_text(font)
        cleaned = (
            _strip_ascii_control_chars(specimen) if isinstance(specimen, str) else ""
        )
        if not cleaned:
            return None
        glyph_count = sum(1 for ch in cleaned if not ch.isspace())
        return cleaned, glyph_count, str(typography.get("specimen_strategy") or "")

    variant_path = str(font.get("path", "")).strip()
    if not variant_path:
        return None

    cps = _specimen_collect_cmap(variant_path, None)
    if not cps:
        return None

    filtered, glyphs, strategy = _script_fallback_specimen(script_iso, cps)
    if filtered is not None and strategy is not None:
        return _strip_ascii_control_chars(filtered), glyphs, strategy

    fallback = _render_variant_cmap_fallback(cps, script_iso)
    if not fallback:
        return None
    return _strip_ascii_control_chars(fallback), len(fallback), "script-cmap"


def probe_and_persist_lualatex_render_variants(
    fonts: list[MutableMapping[str, Any]],
    *,
    validation_metadata: MutableMapping[str, Any],
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> None:
    """
    Probe and persist script-aware LuaLaTeX render-path results.

    Parameters
    ----------
    fonts : list[collections.abc.MutableMapping[str, Any]]
        Mutable enriched inventory font entries updated in place.
    validation_metadata : collections.abc.MutableMapping[str, Any]
        Inventory-level ``metadata.validation.lualatex`` block updated
        in place for the current parse-time environment.
    batch_size : int, optional
        Maximum number of render-path candidates bundled into one
        serial batch.

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

        for script_iso in _ordered_render_variant_scripts(font):
            specimen_details = _render_variant_specimen_details(font, script_iso)
            if specimen_details is None:
                continue
            specimen, specimen_glyph_count, specimen_strategy = specimen_details
            probe_text = _probe_text_from_sample(specimen)
            if not probe_text:
                continue
            _lang, script_opt = _get_render_policy(script_iso)
            candidates.append(
                _ProbeCandidate(
                    candidate_index=len(candidates),
                    font_index=index,
                    path=Path(str(font.get("path", ""))),
                    probe_text=probe_text,
                    probe_input=_probe_input_from_text(probe_text),
                    fontspec_opts=script_opt or None,
                    script=str(script_iso),
                    specimen_text=specimen,
                    specimen_glyph_count=specimen_glyph_count,
                    specimen_strategy=specimen_strategy,
                )
            )

    if not candidates:
        return

    validation_metadata["attempted"] = True
    results: dict[int, dict[str, Any]] = {}
    for chunk in _chunk_candidates(candidates, batch_size=batch_size):
        results.update(_resolve_batch_results(chunk, lualatex_bin=lualatex_bin))

    grouped_states: dict[int, list[dict[str, Any]]] = {}
    for candidate in candidates:
        state = results.get(candidate.candidate_index)
        if state is None:
            continue
        grouped_states.setdefault(candidate.font_index, []).append(
            {
                "script": candidate.script,
                "fontspec_opts": candidate.fontspec_opts,
                "attempted": state["attempted"],
                "loadable": state["loadable"],
                "reason": state["reason"],
                "runtime_fingerprint": runtime_fingerprint,
                "probe_input": state["probe_input"],
                "specimen_text": candidate.specimen_text,
                "specimen_glyph_count": candidate.specimen_glyph_count,
                "specimen_strategy": candidate.specimen_strategy,
            }
        )

    for font_index, states in grouped_states.items():
        set_lualatex_render_variants(fonts[font_index], states=states)
        typography = get_font_typography(fonts[font_index])
        primary_script = typography.get("primary_script")
        primary_state = next(
            (state for state in states if state.get("script") == primary_script),
            states[0],
        )
        set_lualatex_loadability_fields(
            fonts[font_index],
            state={
                "attempted": primary_state["attempted"],
                "loadable": primary_state["loadable"],
                "reason": primary_state["reason"],
                "runtime_fingerprint": runtime_fingerprint,
                "probe_input": primary_state["probe_input"],
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
