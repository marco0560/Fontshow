"""
Fontshow – inventory.fonttools_extraction
=========================================

Font metadata extraction using FontTools.

This module contains the logic responsible for inspecting OpenType and
TrueType fonts using the `fontTools` library and extracting normalized
metadata required for building the Fontshow inventory.

Responsibilities
----------------
• Read OpenType tables via fontTools.TTFont
• Extract name table metadata (family, style, version, license, etc.)
• Decode OS/2 table information
• Detect color font tables
• Compute Unicode block coverage
• Derive charset ranges
• Extract OpenType feature information
• Produce structured metadata used by the inventory layer

Design principles
-----------------
• No dependency on pipeline entrypoints
• Deterministic extraction independent of platform
• Isolate all fontTools interaction in a single module
• Return plain Python structures suitable for inventory construction

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
from fontshow.inventory.utils import font_cache_key
from fontshow.json_format import dumps_pretty
from fontshow.logging_utils import log, log_trace_cat
from fontshow.unicode_tables import UNICODE_BLOCK_RANGES

# ------------------------------------------------------------
# Optional fontTools dependency
# ------------------------------------------------------------

if TYPE_CHECKING:
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
            _MSG = "fontTools is not installed"

            def __init__(self) -> None:
                super().__init__(self._MSG)

        class TTFont:
            def __init__(self, *_args, **_kwargs) -> None:
                raise TTLibError

        class TTCollection:
            def __init__(self, *_args, **_kwargs) -> None:
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
    """
    vals = names.get(str(name_id), [])
    for v in vals:
        if v and v.strip():
            return v.strip()
    return None


def extract_name_table(tt: TTFont) -> dict[str, list[str]]:
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


def extract_os2_table(tt: TTFont) -> dict[str, Any]:
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


def detect_color_tables(tt: TTFont) -> list[str]:
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


def compute_unicode_blocks(codepoints: set[int]) -> dict[str, int]:
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


def extract_unicode_coverage(tt: TTFont, limit: int = 200_000) -> dict[str, Any]:
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


def extract_opentype_features(tt: TTFont) -> list[str]:
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

    # TODO(#0): REFACTOR if touching
    # Complex extractor, split if extraction logic grows


def _fonttools_extract_from_tt(  # noqa: C901, PLR0912
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

    try:
        data["tables"] = sorted(tt.keys())
    except (AttributeError, TypeError):
        data["tables"] = []

    try:
        if "CFF " in tt:
            data["font_type"] = "OpenType CFF"
        elif "glyf" in tt:
            data["font_type"] = "TrueType"
        else:
            data["font_type"] = "Unknown"
    except (AttributeError, TypeError):
        data["font_type"] = "Unknown"

    try:
        data["names"] = extract_name_table(tt)
    except (ValueError, TypeError) as e:
        data["names"] = {"error": f"name: {e}"}

    try:
        data["os2"] = extract_os2_table(tt)
    except (ValueError, TypeError, AttributeError) as e:
        data["os2"] = {"error": f"OS/2: {e}"}

    # -------------------------------
    # Unicode coverage (min/max/count)
    # -------------------------------
    try:
        data["unicode"] = extract_unicode_coverage(tt)
    except (ValueError, TypeError) as e:
        data["unicode"] = {"error": f"unicode: {e}"}

    # -------------------------------
    # Unicode blocks
    # -------------------------------
    # We do not store the full cmap, but we can count coverage per Unicode block.
    # This is essential for robust CJK/emoji/script inference later.
    try:
        codepoints: set[int] = set()
        if "cmap" in tt:
            cmap = tt["cmap"]
            for sub in cmap.tables:
                if not sub.isUnicode():
                    continue
                # sub.cmap is {codepoint:int -> glyphName:str}
                for cp in sub.cmap:
                    codepoints.add(int(cp))
                    # Guard rail: avoid pathological fonts exploding memory
                    if len(codepoints) >= 200_000:
                        break
                if len(codepoints) >= 200_000:
                    break

        data["unicode_blocks"] = (
            compute_unicode_blocks(codepoints) if codepoints else {}
        )
    except (AttributeError, TypeError, ValueError) as e:
        data["unicode_blocks"] = {"error": f"unicode_blocks: {e}"}

    try:
        data["variable"] = {"fvar": ("fvar" in tt), "STAT": ("STAT" in tt)}
    except (AttributeError, TypeError):
        data["variable"] = {"fvar": False, "STAT": False}

    try:
        data["color_tables"] = detect_color_tables(tt)
    except (ValueError, TypeError, AttributeError):
        data["color_tables"] = []

    try:
        data["opentype_features"] = extract_opentype_features(tt)
    except (ValueError, TypeError, AttributeError):
        data["opentype_features"] = []

    # -------------------------------
    # Core technical metrics (schema v1.2)
    # -------------------------------
    try:
        head = tt["head"]
        data["units_per_em"] = int(head.unitsPerEm)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["units_per_em"] = None

    try:
        hhea = tt["hhea"]
        data["ascent"] = int(hhea.ascent)
        data["descent"] = int(hhea.descent)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["ascent"] = None
        data["descent"] = None

    try:
        post = tt["post"]
        data["italic_angle"] = float(post.italicAngle)
        data["is_fixed_pitch"] = bool(post.isFixedPitch)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["italic_angle"] = 0.0
        data["is_fixed_pitch"] = False

    try:
        maxp = tt["maxp"]
        data["glyph_count"] = int(maxp.numGlyphs)
    except (KeyError, AttributeError, TypeError, ValueError):
        data["glyph_count"] = None

    return data


# TODO(#0): REFACTOR if touching:
# Extraction pipeline; refactor if caching or TTC logic expands
def fonttools_extract_all(  # noqa: C901
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

    # Single-face formats
    if container != "TTC":
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
            try:
                return [json.loads(cache_file.read_text(encoding="utf-8"))]
            except (OSError, json.JSONDecodeError):
                pass

        out: dict[str, Any] = {"ok": False, "container": container, "ttc_index": None}
        log_trace_cat(
            log,
            "cache",
            "cache miss",
            extra={
                "font_path": str(path),
            },
        )

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

    # TTC formats (multi-face)
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
        # cache file-level error
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
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if isinstance(cached, dict):
                    cached.setdefault("container", "TTC")
                    cached.setdefault("ttc_index", idx)
                    cached.setdefault("ttc_count", ttc_count)
                results.append(cached)
                continue
            except (OSError, json.JSONDecodeError):
                pass

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
