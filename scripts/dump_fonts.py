#!/usr/bin/env python3
"""
Fontshow - cross-platform font inventory dumper (Linux + Windows)

This script discovers installed font files and writes a canonical JSON inventory
used by the rest of Fontshow (parsing + LaTeX rendering).

Key features
------------
- Cross-platform discovery:
  - Linux: FontConfig (fc-list)
  - Windows: common font directories (Windows Fonts + user fonts)
- Deep metadata extraction via fontTools
- TrueType Collections (.ttc) are fully supported:
  - each face inside a TTC becomes a separate "font" entry
  - identity carries (file + ttc_index)
- Optional Linux-only enrichment via FontConfig (fc-query):
  - scripts / languages / charset
- Persistent caching to avoid repeated decompression/decompilation

Output
------
A single JSON file:
  {
    "metadata": {...},
    "fonts": [ {font descriptor}, ... ]
  }

The JSON schema is documented in:
- docs/font-inventory-schema.md
- docs/dump-fonts.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTCollection, TTFont

# -----------------------
# Platform helpers
# -----------------------
IS_LINUX = sys.platform.startswith("linux")
IS_WINDOWS = sys.platform.startswith("win")


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def run_command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


# -----------------------
# Font discovery
# -----------------------
def get_installed_font_files() -> list[Path]:
    if IS_LINUX:
        return get_installed_font_files_linux()
    if IS_WINDOWS:
        return get_installed_font_files_windows()
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_installed_font_files_linux() -> list[Path]:
    """Linux font discovery using FontConfig (fc-list)."""
    proc = run_command(["fc-list", "--format=%{file}\n"])
    if proc.returncode != 0:
        raise RuntimeError(f"fc-list failed:\n{proc.stdout}")

    files: list[Path] = []
    for line in proc.stdout.splitlines():
        p = line.strip()
        if p:
            files.append(Path(p))

    # Resolve + unique
    return sorted({p.resolve() for p in files if p.exists()})


def _windows_font_dirs() -> list[Path]:
    r"""Known Windows font directories (system + user).

    Note: Windows supports per-user font installs under:
      %LOCALAPPDATA%\Microsoft\Windows\Fonts
    """
    dirs: list[Path] = []
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        dirs.append(Path(windir) / "Fonts")

    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")

    # Fallback guess
    dirs.append(Path("C:/Windows/Fonts"))
    return [d for d in dirs if d.exists()]


def get_installed_font_files_windows() -> list[Path]:
    exts = {".ttf", ".otf", ".ttc", ".otc", ".woff", ".woff2"}
    found: set[Path] = set()
    for d in _windows_font_dirs():
        try:
            for p in d.rglob("*"):
                if p.is_file() and p.suffix.lower() in exts:
                    found.add(p.resolve())
        except Exception:
            # ignore permission issues etc.
            continue
    return sorted(found)


# -----------------------
# Container detection
# -----------------------
def detect_font_container(path: Path) -> str:
    """Detect font container by header and extension.

    Returns: "TTF", "OTF", "TTC", "WOFF", "WOFF2", or "UNKNOWN"
    """
    ext = path.suffix.lower()
    try:
        with path.open("rb") as f:
            head = f.read(4)
    except Exception:
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


# -----------------------
# Cache
# -----------------------
def font_cache_key(path: Path, ttc_index: int | None = None) -> str:
    """Stable cache key for a font *face*.

    For TTC, include the face index so each face gets its own cache entry.
    """
    st = path.stat()
    idx = "" if ttc_index is None else f"|ttc:{ttc_index}"
    key = f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}{idx}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# -----------------------
# Linux-only: FontConfig enrichment
# -----------------------
def fc_query_extract(path: Path, include_charset: bool = False) -> dict[str, Any]:
    """Extract a small set of useful FontConfig-derived fields (Linux only).

    IMPORTANT: For TTC files FontConfig can describe multiple faces; this dumper
    currently attaches a single (file-level) block. Per-face scripts/languages
    are inferred downstream by parse_font_inventory.py when needed.
    """
    proc = run_command(["fc-query", str(path)])
    raw = proc.stdout if proc.stdout else ""

    def _find_line(prefix: str) -> str | None:
        for line in raw.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return None

    lang = _find_line("lang:")
    languages: list[str] = []
    if lang:
        languages = [x.strip() for x in lang.split("|") if x.strip()]

    decorative = (_find_line("decorative:") or "").strip().lower() == "true"
    color = (_find_line("color:") or "").strip().lower() == "true"
    variable = (_find_line("variable:") or "").strip().lower() == "true"
    capability = _find_line("capability:")

    scripts: list[str] = []
    if capability:
        for token in capability.replace('"', "").split():
            if token.startswith("otlayout:"):
                scripts.append(token.split(":", 1)[1])

    charset_blob: str | None = None
    if include_charset:
        lines = raw.splitlines()
        try:
            idx = next(i for i, ln in enumerate(lines) if ln.startswith("charset:"))
            blob: list[str] = [lines[idx]]
            for j in range(idx + 1, len(lines)):
                ln = lines[j]
                if not ln.strip():
                    break
                blob.append(ln)
            charset_blob = "\n".join(blob)
        except StopIteration:
            charset_blob = None

    return {
        "languages": languages,
        "scripts": sorted(set(scripts)),
        "charset": charset_blob,
        "decorative": decorative,
        "color": color,
        "variable": variable,
    }


# -----------------------
# fontTools extraction
# -----------------------
NAME_ID_FAMILY = 1
NAME_ID_SUBFAMILY = 2
NAME_ID_FULLNAME = 4
NAME_ID_POSTSCRIPT = 6
NAME_ID_LICENSE = 13
NAME_ID_LICENSE_URL = 14


def _best_name(names: dict[str, list[str]], name_id: int) -> str | None:
    vals = names.get(str(name_id), [])
    for v in vals:
        if v and v.strip():
            return v.strip()
    return None


def extract_name_table(tt: TTFont) -> dict[str, list[str]]:
    """Return name table as {nameID(str): [values...]} with duplicates removed."""
    out: dict[str, list[str]] = {}
    if "name" not in tt:
        return out
    name_table = tt["name"]
    for rec in name_table.names:  # type: ignore[attr-defined]
        try:
            s = rec.toUnicode()
        except Exception:
            try:
                s = str(rec)
            except Exception:
                continue
        if not s:
            continue
        key = str(int(rec.nameID))
        out.setdefault(key, [])
        if s not in out[key]:
            out[key].append(s)
    return out


def extract_os2_table(tt: TTFont) -> dict[str, Any]:
    """Extract small OS/2 subset, robust against malformed tables."""
    if "OS/2" not in tt:
        return {}
    t = tt["OS/2"]
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
        except Exception:
            continue
    # Normalize vendor ID
    if "vendor_id" in out:
        try:
            vid = out["vendor_id"]
            if isinstance(vid, bytes):
                out["vendor_id"] = vid.decode("ascii", errors="replace")
        except Exception:
            pass
    return out


def detect_color_tables(tt: TTFont) -> list[str]:
    """Return list of present color-related tables."""
    candidates = ["COLR", "CPAL", "CBDT", "CBLC", "sbix", "SVG "]
    return [t for t in candidates if t in tt]


def extract_unicode_coverage(tt: TTFont, limit: int = 200_000) -> dict[str, Any]:
    """Compute a lightweight Unicode coverage summary from cmap.

    We do not store all codepoints (too big). We store min/max/count.
    """
    if "cmap" not in tt:
        return {}
    cmap = tt["cmap"]
    cps: set[int] = set()
    for sub in cmap.tables:  # type: ignore[attr-defined]
        try:
            cm = sub.cmap  # type: ignore[attr-defined]
        except Exception:
            continue
        for cp in cm.keys():
            if isinstance(cp, int):
                cps.add(cp)
        if len(cps) > limit:
            break
    if not cps:
        return {"count": 0, "min": None, "max": None}
    return {"count": len(cps), "min": min(cps), "max": max(cps)}


def extract_opentype_features(tt: TTFont) -> list[str]:
    """Best-effort extraction of GSUB/GPOS feature tags."""
    feats: set[str] = set()
    for tag in ("GSUB", "GPOS"):
        if tag not in tt:
            continue
        tbl = tt[tag]
        try:
            fl = tbl.table.FeatureList  # type: ignore[attr-defined]
            if not fl:
                continue
            for rec in fl.FeatureRecord:  # type: ignore[attr-defined]
                feats.add(rec.FeatureTag)
        except Exception:
            continue
    return sorted(feats)


def _fonttools_extract_from_tt(
    *,
    path: Path,
    container: str,
    tt: TTFont,
    ttc_index: int | None,
) -> dict[str, Any]:
    """Extract metadata from an already-open TTFont (single face)."""
    data: dict[str, Any] = {"ok": True, "container": container, "ttc_index": ttc_index}

    try:
        data["tables"] = sorted(tt.keys())
    except Exception:
        data["tables"] = []

    try:
        if "CFF " in tt:
            data["font_type"] = "OpenType CFF"
        elif "glyf" in tt:
            data["font_type"] = "TrueType"
        else:
            data["font_type"] = "Unknown"
    except Exception:
        data["font_type"] = "Unknown"

    try:
        data["names"] = extract_name_table(tt)
    except Exception as e:
        data["names"] = {"error": f"name: {e}"}

    try:
        data["os2"] = extract_os2_table(tt)
    except Exception as e:
        data["os2"] = {"error": f"OS/2: {e}"}

    try:
        data["unicode"] = extract_unicode_coverage(tt)
    except Exception as e:
        data["unicode"] = {"error": f"unicode: {e}"}

    try:
        data["variable"] = {"fvar": ("fvar" in tt), "STAT": ("STAT" in tt)}
    except Exception:
        data["variable"] = {"fvar": False, "STAT": False}

    try:
        data["color_tables"] = detect_color_tables(tt)
    except Exception:
        data["color_tables"] = []

    try:
        data["opentype_features"] = extract_opentype_features(tt)
    except Exception:
        data["opentype_features"] = []

    return data


def fonttools_extract_all(
    path: Path, cache_dir: Path, use_cache: bool = True
) -> list[dict[str, Any]]:
    """Extract fontTools metadata for one file, returning one entry per face."""
    container = detect_font_container(path)

    # Single-face formats
    if container != "TTC":
        key = font_cache_key(path, None)
        cache_file = cache_dir / f"{key}.json"
        if use_cache and cache_file.exists():
            try:
                return [json.loads(cache_file.read_text(encoding="utf-8"))]
            except Exception:
                pass

        out: dict[str, Any] = {"ok": False, "container": container, "ttc_index": None}
        try:
            tt = TTFont(path, lazy=True, recalcBBoxes=False, recalcTimestamp=False)  # type: ignore[misc]
            out = _fonttools_extract_from_tt(
                path=path, container=container, tt=tt, ttc_index=None
            )
        except Exception as e:
            out["ok"] = False
            out["error"] = f"Cannot open font: {e}"

        cache_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
        return [out]

    # TTC formats (multi-face)
    results: list[dict[str, Any]] = []
    try:
        col = TTCollection(path)
    except Exception as e:
        out = {
            "ok": False,
            "container": "TTC",
            "ttc_index": None,
            "error": f"Cannot open TTC: {e}",
        }
        # cache file-level error
        key = font_cache_key(path, None)
        (cache_dir / f"{key}.json").write_text(
            json.dumps(out, indent=2), encoding="utf-8"
        )
        return [out]

    ttc_count = len(col.fonts)
    for idx, tt in enumerate(col.fonts):
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
            except Exception:
                pass

        try:
            out = _fonttools_extract_from_tt(
                path=path, container="TTC", tt=tt, ttc_index=idx
            )
            out["ttc_count"] = ttc_count
        except Exception as e:
            out = {
                "ok": False,
                "container": "TTC",
                "ttc_index": idx,
                "ttc_count": ttc_count,
                "error": f"TTC face extract failed: {e}",
            }

        cache_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
        results.append(out)

    return results


# -----------------------
# Descriptor build
# -----------------------
def classify_font(
    format_block: dict[str, Any], unicode_max: int | None
) -> dict[str, Any]:
    """Simple format-based classification (downstream inference is richer)."""
    container = format_block.get("container")
    font_type = format_block.get("font_type")
    color = bool(format_block.get("color"))
    decorative = bool(format_block.get("decorative"))
    variable = bool(format_block.get("variable"))

    # Emoji heuristics
    is_emoji = bool(color and unicode_max and unicode_max >= 0x1F300)

    return {
        "is_variable": variable,
        "is_color": color,
        "is_decorative": decorative,
        "is_emoji": is_emoji,
        "container": container,
        "font_type": font_type,
    }


def build_font_descriptor(
    font_path: Path,
    platform_name: str,
    fonttools: dict[str, Any],
    fontconfig: dict[str, Any] | None,
) -> dict[str, Any]:
    names: dict[str, list[str]] = (
        fonttools.get("names", {})
        if isinstance(fonttools.get("names", {}), dict)
        else {}
    )

    family = _best_name(names, NAME_ID_FAMILY)
    style = _best_name(names, NAME_ID_SUBFAMILY)
    postscript = _best_name(names, NAME_ID_POSTSCRIPT)
    fullname = _best_name(names, NAME_ID_FULLNAME)

    languages: list[str] = []
    scripts: list[str] = []
    charset: str | None = None
    decorative = False
    fc_color = False
    fc_variable = False
    if fontconfig:
        languages = fontconfig.get("languages", []) or []
        scripts = fontconfig.get("scripts", []) or []
        charset = fontconfig.get("charset")
        decorative = bool(fontconfig.get("decorative", False))
        fc_color = bool(fontconfig.get("color", False))
        fc_variable = bool(fontconfig.get("variable", False))

    container = fonttools.get("container", detect_font_container(font_path))
    font_type = fonttools.get("font_type", "Unknown")
    variable_flags = fonttools.get("variable", {}) or {}
    variable = bool(
        variable_flags.get("fvar") or variable_flags.get("STAT") or fc_variable
    )

    color_tables = fonttools.get("color_tables", []) or []
    color = bool(fc_color or len(color_tables) > 0)

    unicode_block = fonttools.get("unicode", {}) or {}
    unicode_max = unicode_block.get("max")

    coverage = {
        "unicode": {
            "count": int(unicode_block.get("count", 0) or 0),
            "min": unicode_block.get("min"),
            "max": unicode_max,
        },
        "scripts": scripts,
        "languages": languages,
        "charset": charset,
    }

    typography = {
        "weight_class": None,
        "width_class": None,
        "opentype_features": fonttools.get("opentype_features", []) or [],
    }

    os2 = fonttools.get("os2", {})
    if isinstance(os2, dict) and "error" not in os2:
        typography["weight_class"] = os2.get("weight_class")
        typography["width_class"] = os2.get("width_class")

    format_block = {
        "container": container,
        "font_type": font_type,
        "ttc_index": fonttools.get("ttc_index"),
        "ttc_count": fonttools.get("ttc_count"),
        "variable": variable,
        "color": color,
        "decorative": decorative,
    }

    classification = classify_font(format_block, unicode_max)

    license_text = _best_name(names, NAME_ID_LICENSE)
    license_url = _best_name(names, NAME_ID_LICENSE_URL)

    vendor = None
    embedding_rights = None
    if isinstance(os2, dict) and "error" not in os2:
        vendor = os2.get("vendor_id")
        embedding_rights = os2.get("embedding_rights")

    return {
        "identity": {
            "file": str(font_path),
            "ttc_index": fonttools.get("ttc_index"),
            "family": family,
            "style": style,
            "fullname": fullname,
            "postscript_name": postscript,
        },
        "platform": {"name": platform_name},
        "format": format_block,
        "coverage": coverage,
        "typography": typography,
        "classification": classification,
        "license": {"text": license_text, "url": license_url},
        "vendor": vendor,
        "embedding_rights": embedding_rights,
        "source": {
            "fonttools": {
                "ok": bool(fonttools.get("ok", False)),
                "error": fonttools.get("error"),
            },
            "fontconfig": (None if fontconfig is None else {"ok": True}),
        },
    }


# -----------------------
# Main
# -----------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Dump a canonical JSON font inventory (Linux + Windows)."
    )
    ap.add_argument("--output", default="font_inventory.json", help="Output JSON path.")
    ap.add_argument(
        "--cache-dir",
        default=".cache/fontshow-fonttools",
        help="Cache directory for fontTools extraction.",
    )
    ap.add_argument("--no-cache", action="store_true", help="Disable cache (slower).")
    ap.add_argument(
        "--no-fontconfig",
        action="store_true",
        help="Disable Linux FontConfig enrichment (fc-query).",
    )
    ap.add_argument(
        "--include-charset",
        action="store_true",
        help="Include raw FontConfig charset blob (Linux only).",
    )

    args = ap.parse_args()

    out_path = Path(args.output)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    use_cache = not args.no_cache
    include_fontconfig = IS_LINUX and (not args.no_fontconfig)

    platform_name = platform.system().lower()

    inventory: dict[str, Any] = {
        "metadata": {
            "generator": "Fontshow dump_fonts.py",
            "platform": platform_name,
            "generated_at": utc_now_iso(),
            "python": sys.version.split()[0],
        },
        "fonts": [],
    }

    if include_fontconfig:
        try:
            inventory["metadata"]["fontconfig"] = run_command(
                ["fc-list", "--version"]
            ).stdout.strip()
        except Exception:
            pass

    files = get_installed_font_files()
    if not files:
        raise SystemExit("No font files discovered.")

    # Cache fc-query results per file (not per TTC face)
    fc_cache: dict[str, Any] = {}

    for i, p in enumerate(files, start=1):
        if i % 500 == 0:
            print(f"... {i}/{len(files)} files", file=sys.stderr)

        fc: dict[str, Any] | None = None
        if include_fontconfig:
            key = str(p)
            if key in fc_cache:
                fc = fc_cache[key]
            else:
                try:
                    fc = fc_query_extract(p, include_charset=bool(args.include_charset))
                except Exception as e:
                    fc = {"error": str(e)}
                fc_cache[key] = fc

        ft_list = fonttools_extract_all(p, cache_dir, use_cache=use_cache)

        for ft in ft_list:
            desc = build_font_descriptor(
                p,
                platform_name,
                (
                    ft
                    if isinstance(ft, dict)
                    else {"ok": False, "error": "invalid fonttools block"}
                ),
                fc if isinstance(fc, dict) and "error" not in fc else None,
            )
            inventory["fonts"].append(desc)

    inventory["fonts"].sort(
        key=lambda d: (
            d["identity"].get("family") or "",
            d["identity"].get("style") or "",
            d["identity"].get("file") or "",
            (
                d["identity"].get("ttc_index")
                if d["identity"].get("ttc_index") is not None
                else -1
            ),
        )
    )

    out_path.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"Wrote {len(inventory['fonts'])} font entries to {out_path}", file=sys.stderr
    )


if __name__ == "__main__":
    main()
