"""
FontTools metadata extraction helpers.

This module implements the logic used to extract font metadata from
OpenType and TrueType font binaries using the `fontTools` library.

Responsibilities
----------------
- Inspect OpenType tables via `fontTools.ttLib`.
- Extract name table metadata such as family, style, and version.
- Decode OS/2 table information and font capabilities.
- Detect color font tables and other format features.
- Compute Unicode block coverage and charset ranges.
- Produce normalized metadata used by the inventory subsystem.

Design principles
-----------------
All interaction with the `fontTools` library is isolated in this module
so that font binary inspection remains centralized and deterministic.
The module returns plain Python structures suitable for inventory
construction and serialization.

Architectural role
------------------
This module belongs to the **inventory subsystem** and performs the
font binary inspection stage used during inventory generation.

Typical workflow
----------------
The dump-fonts pipeline discovers font files and calls
`fonttools_extract_all()` from this module to obtain normalized
metadata derived from the font binary. The resulting data is then
combined with platform metadata (e.g. Fontconfig results) and written
to the inventory JSON.
"""

from __future__ import annotations

import json
import struct
from typing import TYPE_CHECKING, Any

from fontTools.ttLib import TTCollection, TTFont, TTLibError

from fontshow.constants.opentype import NAME_ID_SAMPLE_TEXT
from fontshow.core.json_format import dumps_pretty
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.inventory.utils import font_cache_key
from fontshow.ontology.unicode_tables import UNICODE_BLOCK_RANGES

# ------------------------------------------------------------
# Optional fontTools dependency
# ------------------------------------------------------------

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from fontTools.misc import timeTools
    from fontTools.ttLib import TTCollection, TTFont, TTLibError

    FONTTOOLS_AVAILABLE = True

else:
    try:
        from fontTools.misc import timeTools
        from fontTools.ttLib import TTCollection, TTFont, TTLibError

        FONTTOOLS_AVAILABLE = True

        if hasattr(timeTools, "TIMESTAMP_WARNINGS"):
            timeTools.TIMESTAMP_WARNINGS = False

    except ImportError:
        FONTTOOLS_AVAILABLE = False

        class TTLibError(Exception):
            """
            Fallback exception used when `fontTools` is unavailable.

            Parameters
            ----------
            None

            Notes
            -----
            This local fallback preserves the exception type used by the
            rest of the module when the real dependency cannot be
            imported.
            """

            _MSG = "fontTools is not installed"

            def __init__(self) -> None:
                """
                Initialize the fallback exception with a fixed message.

                Parameters
                ----------
                None

                Returns
                -------
                None
                """
                super().__init__(self._MSG)

        class TTFont:
            """
            Fallback stub that raises `TTLibError` on instantiation.

            Parameters
            ----------
            None

            Notes
            -----
            This stub exists only to preserve import-time compatibility
            when `fontTools` is unavailable.
            """

            def __init__(self, *_args, **_kwargs) -> None:
                """
                Reject construction when `fontTools` is unavailable.

                Parameters
                ----------
                None

                Returns
                -------
                None

                Raises
                ------
                TTLibError
                    Always raised because the real `fontTools` backend is
                    unavailable.
                """
                raise TTLibError

        class TTCollection:
            """
            Fallback stub that raises `TTLibError` on instantiation.

            Parameters
            ----------
            None

            Notes
            -----
            This stub exists only to preserve import-time compatibility
            when `fontTools` is unavailable.
            """

            def __init__(self, *_args, **_kwargs) -> None:
                """
                Reject construction when `fontTools` is unavailable.

                Parameters
                ----------
                None

                Returns
                -------
                None

                Raises
                ------
                TTLibError
                    Always raised because the real `fontTools` backend is
                    unavailable.
                """
                raise TTLibError


def detect_font_container(path: Path) -> str:
    """
    Detect font container format using file header and extension.

    Parameters
    ----------
    path : pathlib.Path
        Path to the font file.

    Returns
    -------
    str
        Detected container type: "TTF", "OTF", "TTC", "WOFF", "WOFF2",
        or "UNKNOWN" if not recognized.

    Notes
    -----
    Detection is best-effort and combines magic-byte checks with
    filename extension fallback when header inspection is unavailable.
    """
    ext = path.suffix.lower()
    try:
        with path.open("rb") as f:
            head = f.read(4)
    except OSError:
        head = b""

    if head == b"ttcf":
        return "TTC"
    if head == b"wOFF" or ext == ".woff":
        return "WOFF"
    if head == b"wOF2" or ext == ".woff2":
        return "WOFF2"
    if head == b"OTTO" or ext == ".otf":
        return "OTF"
    if head in (b"\x00\x01\x00\x00", b"true", b"typ1") or ext == ".ttf":
        return "TTF"
    if ext == ".ttc":
        return "TTC"
    return "UNKNOWN"


def _charset_ranges_from_ttfont(tt: TTFont) -> list[list[int]]:
    """
    Extract merged Unicode codepoint ranges from cmap tables.

    Parameters
    ----------
    tt : TTFont
        Open font object whose Unicode cmap tables are inspected.

    Returns
    -------
    list[list[int]]
        Sorted contiguous codepoint ranges [[start, end], ...].

    Notes
    -----
    Discovery-only helper:
    - performs no semantic interpretation
    - deterministic output
    """
    try:
        cmap = tt["cmap"]
    except KeyError:
        return []

    codepoints: set[int] = set()

    for table in cmap.tables:
        if not table.isUnicode():
            continue
        codepoints.update(table.cmap.keys())

    if not codepoints:
        return []

    sorted_cps = sorted(codepoints)

    ranges: list[list[int]] = []
    start = prev = sorted_cps[0]

    for cp in sorted_cps[1:]:
        if cp == prev + 1:
            prev = cp
            continue

        ranges.append([start, prev])
        start = prev = cp

    ranges.append([start, prev])
    return ranges


def extract_sample_text(font_path: str) -> list[str] | None:
    """
    Extract embedded sample text from a font file.

    Parameters
    ----------
    font_path : str
        Filesystem path to the font file.

    Returns
    -------
    list[str] | None
        List of unique embedded sample text strings if present,
        otherwise None.

    Raises
    ------
    None
        Extraction errors (OSError, ValueError, TTLibError, UnicodeError)
        are handled internally and converted into a ``None`` result.

    Notes
    -----
    Extraction is best-effort and silently ignores malformed
    or partially corrupted name table entries.
    """
    try:
        # Silence TTFont info logs, which can be noisy on malformed fonts
        # and are not relevant for sample text extraction. We want to preserve
        # any errors, however.
        tt = TTFont(font_path, lazy=True)
    except (OSError, ValueError, TTLibError):
        return None

    if "name" not in tt:
        tt.close()
        return None

    name_table = tt["name"]

    seen: set[str] = set()
    unique_samples: list[str] = []

    for record in name_table.names:
        if record.nameID != NAME_ID_SAMPLE_TEXT:
            continue

        try:
            text = record.toUnicode().strip()
        except (UnicodeError, ValueError):
            continue

        if not text or text in seen:
            continue

        seen.add(text)
        unique_samples.append(text)

    tt.close()

    return unique_samples or None


def _best_name(names: dict[str, list[str]], name_id: int) -> str | None:
    """
    Return the first non-empty value for a given nameID.

    Parameters
    ----------
    names : dict[str, list[str]]
        Mapping of nameID (as string) to a list of candidate strings.
    name_id : int
        The integer nameID to query.

    Returns
    -------
    str | None
        First non-empty, stripped string for the given nameID, or None
        if no usable value is found.

    Notes
    -----
    Candidate values are evaluated in stored order and the first usable
    string wins.

    Empty and whitespace-only candidates are ignored.
    """
    vals = names.get(str(name_id), [])
    for v in vals:
        if v and v.strip():
            return v.strip()
    return None


def _extract_name_table(tt: TTFont) -> dict[str, list[str]]:
    """
    Extract the OpenType/TrueType name table as a JSON-friendly mapping.

    Data structure:
        The returned dictionary maps ``nameID`` (string) to a list of unique
        values, preserving the first-seen order.

        Example::

            {
              "1": ["DejaVu Sans", "DejaVuSans"],
              "2": ["Book"],
              "4": ["DejaVu Sans Book"]
            }

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    dict[str, list[str]]
        Mapping {name_id_str: [values...]} preserving first-seen order.
        Returns an empty dict if the font has no name table.
    """
    out: dict[str, list[str]] = {}
    if "name" not in tt:
        return out
    name_table = tt["name"]
    for rec in name_table.names:
        try:
            s = rec.toUnicode()
        except (UnicodeError, ValueError, TypeError):
            try:
                s = str(rec)
            except (UnicodeError, ValueError, TypeError):
                continue
        if not s:
            continue
        key = str(int(rec.nameID))
        out.setdefault(key, [])
        if s not in out[key]:
            out[key].append(s)
    return out


def _extract_os2_table(tt: TTFont) -> dict[str, Any]:
    """Extract a small subset of OS/2 fields, best-effort.

     The OS/2 table is frequently present but can be malformed. This function
     therefore uses defensive attribute access and returns only a stable subset.

     Extracted keys (when available):
     - ``weight_class`` (int)
     - ``width_class`` (int)
     - ``embedding_rights`` (int)
     - ``vendor_id`` (str, normalized to ASCII where possible)
     - ``version`` (int)

    Parameters
     ----------
     tt : TTFont
         Open TTFont instance representing a single font face.

     Returns
     -------
     dict[str, Any]
         Dictionary containing extracted OS/2 fields when available,
         or an empty dict if the OS/2 table is missing or malformed.
    """
    if "OS/2" not in tt:
        return {}
    try:
        t = tt["OS/2"]
    except (AttributeError, TypeError, struct.error):
        return {}

    out: dict[str, Any] = {}
    for attr, key in [
        ("usWeightClass", "weight_class"),
        ("usWidthClass", "width_class"),
        ("fsType", "embedding_rights"),
        ("achVendID", "vendor_id"),
        ("version", "version"),
    ]:
        try:
            out[key] = getattr(t, attr)
        except (AttributeError, TypeError):
            continue
    # Normalize vendor ID
    if "vendor_id" in out:
        try:
            vid = out["vendor_id"]
            if isinstance(vid, bytes):
                out["vendor_id"] = vid.decode("ascii", errors="replace")
        except (UnicodeError, AttributeError, TypeError):
            pass
    return out


def _detect_color_tables(tt: TTFont) -> list[str]:
    """
    Detect presence of color-related OpenType tables.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    list[str]
        List of detected color-related table tags present in the font.
    """
    candidates = ["COLR", "CPAL", "CBDT", "CBLC", "sbix", "SVG "]
    return [t for t in candidates if t in tt]


def _compute_unicode_blocks(codepoints: set[int]) -> dict[str, int]:
    """
    Count how many code points fall into each configured Unicode block.

    Parameters
    ----------
    codepoints : set[int]
        Set of Unicode code points present in the font cmap.

    Returns
    -------
    dict[str, int]
        Mapping {block_name: count} including only blocks with count > 0.
    """
    blocks: dict[str, int] = {}

    for name, (start, end) in UNICODE_BLOCK_RANGES.items():
        count = sum(1 for cp in codepoints if start <= cp <= end)
        if count > 0:
            blocks[name] = count

    return blocks


def _extract_unicode_coverage(tt: TTFont, limit: int = 200_000) -> dict[str, Any]:
    """
    Compute a lightweight Unicode coverage summary from the cmap table.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.
    limit : int, optional
        Maximum number of distinct code points to collect before stopping.

    Returns
    -------
    dict[str, Any]
        Dictionary with keys:
        - "count": number of distinct code points observed,
        - "min": minimum code point or None,
        - "max": maximum code point or None.
        Returns an empty dict if no cmap table exists.
    """
    if "cmap" not in tt:
        return {}
    cmap = tt["cmap"]
    cps: set[int] = set()
    for sub in cmap.tables:
        try:
            cm = sub.cmap
        except (AttributeError, TypeError):
            continue
        for cp in cm:
            if isinstance(cp, int):
                cps.add(cp)
        if len(cps) > limit:
            break
    if not cps:
        return {"count": 0, "min": None, "max": None}
    return {"count": len(cps), "min": min(cps), "max": max(cps)}


def _extract_opentype_features(tt: TTFont) -> list[str]:
    """
    Extract OpenType GSUB/GPOS feature tags (best-effort).

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    list[str]
        Sorted list of detected OpenType feature tags.
    """
    feats: set[str] = set()
    for tag in ("GSUB", "GPOS"):
        if tag not in tt:
            continue
        tbl = tt[tag]
        try:
            fl = tbl.table.FeatureList
            if not fl:
                continue
            for rec in fl.FeatureRecord:
                feats.add(rec.FeatureTag)
        except (AttributeError, TypeError, IndexError):
            continue
    return sorted(feats)


_FONT_TYPE_RULES: tuple[tuple[str, str], ...] = (
    ("CFF ", "OpenType CFF"),
    ("glyf", "TrueType"),
)

_TABLE_EXTRACTORS: tuple[tuple[str, str, tuple[type[BaseException], ...], Any], ...] = (
    ("names", "_extract_name_table", (ValueError, TypeError), "name"),
    ("os2", "_extract_os2_table", (ValueError, TypeError, AttributeError), "OS/2"),
    ("unicode", "_extract_unicode_coverage", (ValueError, TypeError), "unicode"),
    (
        "color_tables",
        "_detect_color_tables",
        (ValueError, TypeError, AttributeError),
        [],
    ),
    (
        "opentype_features",
        "_extract_opentype_features",
        (ValueError, TypeError, AttributeError),
        [],
    ),
)

_TECHNICAL_METRIC_RULES: tuple[
    tuple[str, str, str, type, tuple[type[BaseException], ...], Any], ...
] = (
    (
        "head",
        "unitsPerEm",
        "units_per_em",
        int,
        (KeyError, AttributeError, TypeError, ValueError),
        None,
    ),
    (
        "hhea",
        "ascent",
        "ascent",
        int,
        (KeyError, AttributeError, TypeError, ValueError),
        None,
    ),
    (
        "hhea",
        "descent",
        "descent",
        int,
        (KeyError, AttributeError, TypeError, ValueError),
        None,
    ),
    (
        "post",
        "italicAngle",
        "italic_angle",
        float,
        (KeyError, AttributeError, TypeError, ValueError),
        0.0,
    ),
    (
        "post",
        "isFixedPitch",
        "is_fixed_pitch",
        bool,
        (KeyError, AttributeError, TypeError, ValueError),
        False,
    ),
    (
        "maxp",
        "numGlyphs",
        "glyph_count",
        int,
        (KeyError, AttributeError, TypeError, ValueError),
        None,
    ),
)


def _extract_tt_tables(tt: TTFont) -> list[str]:
    """
    Extract sorted table tags from a font face.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    list[str]
        Sorted table tags, or an empty list when table discovery fails.
    """
    try:
        return sorted(tt.keys())
    except (AttributeError, TypeError):
        return []


def _classify_font_type(tt: TTFont) -> str:
    """
    Classify the coarse font type from available table tags.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    str
        Coarse font type label.
    """
    try:
        return next(label for table_tag, label in _FONT_TYPE_RULES if table_tag in tt)
    except (StopIteration, AttributeError, TypeError):
        return "Unknown"


def _run_table_extractors(tt: TTFont) -> dict[str, Any]:
    """
    Run best-effort structured table extractors for a font face.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    dict[str, Any]
        Extracted structured metadata keyed by output field name.
    """
    extracted: dict[str, Any] = {}
    for key, extractor_name, handled_errors, error_label in _TABLE_EXTRACTORS:
        extractor = globals()[extractor_name]
        try:
            extracted[key] = extractor(tt)
        except handled_errors as e:
            if isinstance(error_label, str):
                extracted[key] = {"error": f"{error_label}: {e}"}
            else:
                extracted[key] = error_label
    return extracted


def _collect_unicode_codepoints(tt: TTFont, limit: int = 200_000) -> set[int]:
    """
    Collect Unicode cmap codepoints from a font face.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.
    limit : int, optional
        Maximum number of distinct codepoints to collect.

    Returns
    -------
    set[int]
        Distinct Unicode codepoints found in the cmap.
    """
    codepoints: set[int] = set()
    if "cmap" not in tt:
        return codepoints

    cmap = tt["cmap"]
    for sub in cmap.tables:
        if not sub.isUnicode():
            continue
        for cp in sub.cmap:
            codepoints.add(int(cp))
            if len(codepoints) >= limit:
                return codepoints
    return codepoints


def _extract_unicode_blocks(tt: TTFont) -> dict[str, int] | dict[str, str]:
    """
    Extract per-block Unicode coverage from a font face.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    dict[str, int] | dict[str, str]
        Per-block coverage mapping, or an ``error`` payload when extraction fails.
    """
    try:
        codepoints = _collect_unicode_codepoints(tt)
        return _compute_unicode_blocks(codepoints) if codepoints else {}
    except (AttributeError, TypeError, ValueError) as e:
        return {"error": f"unicode_blocks: {e}"}


def _extract_variable_flags(tt: TTFont) -> dict[str, bool]:
    """
    Extract variable-font presence flags from a font face.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    dict[str, bool]
        Presence flags for ``fvar`` and ``STAT`` tables.
    """
    try:
        return {"fvar": ("fvar" in tt), "STAT": ("STAT" in tt)}
    except (AttributeError, TypeError):
        return {"fvar": False, "STAT": False}


def _extract_technical_metrics(tt: TTFont) -> dict[str, Any]:
    """
    Extract core technical metrics for schema output.

    Parameters
    ----------
    tt : TTFont
        Open TTFont instance representing a single font face.

    Returns
    -------
    dict[str, Any]
        Core technical metrics keyed by schema field name.
    """
    metrics: dict[str, Any] = {}
    for (
        table_name,
        attr_name,
        out_key,
        cast_fn,
        handled_errors,
        default,
    ) in _TECHNICAL_METRIC_RULES:
        try:
            table = tt[table_name]
            metrics[out_key] = cast_fn(getattr(table, attr_name))
        except handled_errors:
            metrics[out_key] = default
    return metrics


def _fonttools_extract_from_tt(
    *,
    _path: Path,
    container: str,
    tt: TTFont,
    ttc_index: int | None,
) -> dict[str, Any]:
    """Extract a per-face metadata block from an open ``TTFont``.

    Data structure:
        The returned dictionary is designed to be JSON-serializable and stable.
        It is later consumed by :func:`build_font_descriptor`.

        Key fields include:
        - ``ok``: bool, success flag
        - ``container``: str, container type (TTF/OTF/TTC/WOFF/WOFF2/...)
        - ``ttc_index``: int|None, TTC face index for TTC files
        - ``tables``: list[str], present table tags
        - ``font_type``: str, coarse font type classification
        - ``names``: dict[str, list[str]] name table mapping (or error dict)
        - ``os2``: dict[str, Any] OS/2 subset (or error dict)
        - ``unicode``: dict[str, Any] coverage summary (or error dict)
        - ``unicode_blocks``: dict[str, int] per-block coverage counts (or error dict)
        - ``variable``: dict[str, bool] presence flags for fvar/STAT
        - ``color_tables``: list[str] present color-related tables
        - ``opentype_features``: list[str] GSUB/GPOS feature tags

    Parameters
    ----------
    _path : pathlib.Path
        Font file path (used for context and logging).
    container : str
        Container type string (e.g. TTF, OTF, TTC).
    tt : TTFont
        Open TTFont instance for the current face.
    ttc_index : int | None
        TTC face index, or None for single-face fonts.

    Returns
    -------
    dict[str, Any]
        JSON-serializable dictionary describing extracted metadata for the face.
    """
    data: dict[str, Any] = {"ok": True, "container": container, "ttc_index": ttc_index}
    data["tables"] = _extract_tt_tables(tt)
    data["font_type"] = _classify_font_type(tt)
    data.update(_run_table_extractors(tt))
    data["unicode_blocks"] = _extract_unicode_blocks(tt)
    data["variable"] = _extract_variable_flags(tt)
    data.update(_extract_technical_metrics(tt))
    return data


def _load_cached_face(
    cache_file: Path, *, defaults: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """
    Load a cached face block, applying optional default keys.

    Parameters
    ----------
    cache_file : pathlib.Path
        Cache file expected to contain one serialized face block.
    defaults : dict[str, Any] | None, optional
        Default keys applied to the decoded mapping when present.

    Returns
    -------
    dict[str, Any] | None
        Decoded cached face mapping, or None when the cache file is
        unreadable, malformed, or not a dictionary.
    """
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(cached, dict):
        return None

    if defaults:
        for key, value in defaults.items():
            cached.setdefault(key, value)
    return cached


def _extract_single_face(
    *,
    path: Path,
    cache_dir: Path,
    container: str,
    use_cache: bool,
    t0_total: float,
) -> list[dict[str, Any]]:
    """
    Extract one metadata block for a single-face container.

    Parameters
    ----------
    path : pathlib.Path
        Font file path.
    cache_dir : pathlib.Path
        Cache directory for serialized extraction output.
    container : str
        Detected container type.
    use_cache : bool
        Whether cache reuse is enabled.
    t0_total : float
        Extraction start timestamp from ``perf_counter()``.

    Returns
    -------
    list[dict[str, Any]]
        One-element list containing the extracted face block.
    """
    from time import perf_counter

    key = font_cache_key(path, None)
    cache_file = cache_dir / f"{key}.json"
    if use_cache and cache_file.exists():
        log_trace_cat(
            log,
            "cache",
            "cache hit",
            extra={
                "font_path": str(path),
                "cache_file": str(cache_file),
            },
        )
        cached = _load_cached_face(cache_file)
        if cached is not None:
            return [cached]

    log_trace_cat(
        log,
        "cache",
        "cache miss",
        extra={
            "font_path": str(path),
        },
    )

    out: dict[str, Any] = {"ok": False, "container": container, "ttc_index": None}
    try:
        tt = TTFont(path, lazy=True, recalcBBoxes=False, recalcTimestamp=False)
        out = _fonttools_extract_from_tt(
            _path=path, container=container, tt=tt, ttc_index=None
        )
    except (OSError, ValueError, TTLibError) as e:
        out["ok"] = False
        out["error"] = f"Cannot open font: {e}"
        log_trace_cat(
            log,
            "io",
            "fonttools extraction failed",
            extra={
                "font_path": str(path),
                "error": str(e),
            },
        )

    cache_file.write_text(
        dumps_pretty(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    duration_ms = int((perf_counter() - t0_total) * 1000)
    log_trace_cat(
        log,
        "perf",
        "fonttools extraction timing",
        extra={
            "font_path": str(path),
            "container": container,
            "duration_ms": duration_ms,
            "faces": 1,
        },
    )
    return [out]


def _extract_ttc_faces(
    *,
    path: Path,
    cache_dir: Path,
    use_cache: bool,
    t0_total: float,
) -> list[dict[str, Any]]:
    """
    Extract metadata blocks for all faces in a TTC container.

    Parameters
    ----------
    path : pathlib.Path
        TTC file path.
    cache_dir : pathlib.Path
        Cache directory for serialized face outputs.
    use_cache : bool
        Whether cache reuse is enabled.
    t0_total : float
        Extraction start timestamp from ``perf_counter()``.

    Returns
    -------
    list[dict[str, Any]]
        Extracted metadata blocks for all TTC faces, or a one-element
        error block list when the TTC cannot be opened.
    """
    from time import perf_counter

    results: list[dict[str, Any]] = []
    try:
        col = TTCollection(path)
    except (OSError, ValueError, TTLibError) as e:
        out = {
            "ok": False,
            "container": "TTC",
            "ttc_index": None,
            "error": f"Cannot open TTC: {e}",
        }
        log_trace_cat(
            log,
            "io",
            "fonttools extraction failed",
            extra={
                "font_path": str(path),
                "error": str(e),
            },
        )
        key = font_cache_key(path, None)
        (cache_dir / f"{key}.json").write_text(
            dumps_pretty(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return [out]

    ttc_count = len(col.fonts)
    for idx, tt in enumerate(col.fonts):
        log_trace_cat(
            log,
            "io",
            "TTC face extraction",
            extra={
                "font_path": str(path),
                "face_index": idx,
                "ttc_count": ttc_count,
            },
        )

        key = font_cache_key(path, idx)
        cache_file = cache_dir / f"{key}.json"
        if use_cache and cache_file.exists():
            cached = _load_cached_face(
                cache_file,
                defaults={"container": "TTC", "ttc_index": idx, "ttc_count": ttc_count},
            )
            if cached is not None:
                results.append(cached)
                continue

        t0_face = perf_counter()
        try:
            out = _fonttools_extract_from_tt(
                _path=path, container="TTC", tt=tt, ttc_index=idx
            )
            out["ttc_count"] = ttc_count
        except (OSError, ValueError, TTLibError) as e:
            out = {
                "ok": False,
                "container": "TTC",
                "ttc_index": idx,
                "ttc_count": ttc_count,
                "error": f"TTC face extract failed: {e}",
            }

        duration_ms = int((perf_counter() - t0_face) * 1000)
        log_trace_cat(
            log,
            "perf",
            "fonttools face extraction timing",
            extra={
                "font_path": str(path),
                "face_index": idx,
                "duration_ms": duration_ms,
            },
        )

        cache_file.write_text(
            dumps_pretty(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        results.append(out)

    duration_ms = int((perf_counter() - t0_total) * 1000)
    log_trace_cat(
        log,
        "perf",
        "fonttools extraction timing",
        extra={
            "font_path": str(path),
            "container": "TTC",
            "duration_ms": duration_ms,
            "faces": ttc_count,
        },
    )
    return results


_CONTAINER_EXTRACTORS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "TTC": _extract_ttc_faces,
}


def fonttools_extract_all(
    path: Path, cache_dir: Path, use_cache: bool = True
) -> list[dict[str, Any]]:
    """
    Extract fontTools metadata for a font file, returning one entry per face.

    Parameters
    ----------
    path : pathlib.Path
        Font file path.
    cache_dir : pathlib.Path
        Directory used for per-face JSON cache files.
    use_cache : bool, optional
        If True, reuse cached JSON blocks where possible.

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries, each describing a single font face.

    Notes
    -----
    - Single-face formats return a one-element list.
    - TTC files return one element per face.
    - If fontTools is unavailable, a single error block is returned.
    """
    # -------------------------------
    # Guard: fontTools not available
    # -------------------------------
    if not FONTTOOLS_AVAILABLE:
        return [
            {
                "ok": False,
                "container": detect_font_container(path),
                "ttc_index": None,
                "error": "fontTools not available",
            }
        ]

    from time import perf_counter

    t0_total = perf_counter()

    container = detect_font_container(path)
    log_trace_cat(
        log,
        "io",
        "container detected",
        extra={
            "font_path": str(path),
            "container": container,
        },
    )

    extractor = _CONTAINER_EXTRACTORS.get(container)
    if extractor is not None:
        return extractor(
            path=path,
            cache_dir=cache_dir,
            use_cache=use_cache,
            t0_total=t0_total,
        )

    return _extract_single_face(
        path=path,
        cache_dir=cache_dir,
        container=container,
        use_cache=use_cache,
        t0_total=t0_total,
    )
