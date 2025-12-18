#!/usr/bin/env python3
"""
Fontshow - cross-platform font inventory dumper

This script generates a *canonical* font inventory in JSON format, suitable for
later parsing and for producing OS-agnostic outputs (e.g. LaTeX catalog).

Design goals
-----------
- One codebase for Linux and Windows.
- OS-specific logic is limited to the "font discovery" phase.
- Extraction is normalized into a stable JSON schema.
- Rich OpenType/TrueType metadata via `fontTools`.
- Optional Linux-only enrichment via FontConfig (`fc-query` / `fc-list`).
- Persistent caching to keep re-runs fast.

Output
------
A single JSON file following the schema documented in:
- docs/font-inventory-schema.md
- docs/dump-fonts.md

Notes on Windows
----------------
Windows does not ship FontConfig. Therefore, "languages/scripts/charset" (which
FontConfig can derive) are left empty unless you add a separate analyzer.
However, most fields can still be computed via `fontTools` alone.

Compatibility
-------------
- Python: 3.10+
- Linux: requires `fontconfig` for discovery and optional enrichment
- Windows: uses Registry + Fonts directories for discovery
- Optional: `fontTools` strongly recommended (needed for deep metadata)

Usage
-----
    python3 scripts/dump_fonts.py --output font_inventory.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# -----------------------
# Optional dependency: fontTools
# -----------------------
try:
    from fontTools.ttLib import TTFont  # type: ignore

    FONTTOOLS_AVAILABLE = True
except Exception:
    TTFont = None  # type: ignore
    FONTTOOLS_AVAILABLE = False

# -----------------------
# Platform detection
# -----------------------
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    import winreg  # type: ignore


# -----------------------
# Cache
# -----------------------
DEFAULT_CACHE_DIR = Path(".font_cache")


def font_cache_key(path: Path) -> str:
    """Compute a stable cache key for a font file."""
    stat = path.stat()
    key = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# -----------------------
# Low-level utilities
# -----------------------
def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def run_command(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and return the completed process."""
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False
    )


def read_file_header4(path: Path) -> bytes:
    try:
        with path.open("rb") as f:
            return f.read(4)
    except Exception:
        return b""


def detect_font_container(path: Path) -> str:
    """Detect the *container* format of a font file."""
    suffix = path.suffix.lower()

    if suffix == ".woff2":
        return "WOFF2"
    if suffix == ".woff":
        return "WOFF"

    header = read_file_header4(path)

    if header == b"wOFF":
        return "WOFF"
    if header == b"wOF2":
        return "WOFF2"
    if header in (b"\x00\x01\x00\x00", b"true"):
        return "TrueType"
    if header == b"OTTO":
        return "OpenType"
    if header == b"ttcf":
        return "TTC"

    return "Unknown"


# -----------------------
# Font discovery
# -----------------------
def get_installed_font_files() -> List[Path]:
    """Return a list of installed font files for the current platform."""
    if IS_LINUX:
        return get_installed_font_files_linux()
    if IS_WINDOWS:
        return get_installed_font_files_windows()
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_installed_font_files_linux() -> List[Path]:
    """Linux font discovery using FontConfig (fc-list)."""
    proc = run_command(["fc-list", "--format=%{file}\n"])
    if proc.returncode != 0:
        raise RuntimeError(f"fc-list failed:\n{proc.stdout}")
    files = []
    for line in proc.stdout.splitlines():
        p = line.strip()
        if p:
            files.append(Path(p))
    return sorted({p.resolve() for p in files})


def _windows_font_dirs() -> List[Path]:
    """Return known Windows font directories."""
    dirs: List[Path] = []
    windir = os.environ.get("WINDIR")
    if windir:
        dirs.append(Path(windir) / "Fonts")
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        dirs.append(Path(localappdata) / "Microsoft" / "Windows" / "Fonts")
    return [d for d in dirs if d.exists()]


def get_installed_font_files_windows() -> List[Path]:
    """Windows font discovery using Registry + font directories."""
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Fonts",
    ]

    font_dirs = _windows_font_dirs()
    found: List[Path] = []

    for reg_path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:  # type: ignore[name-defined]
                nvals = winreg.QueryInfoKey(key)[1]  # type: ignore[name-defined]
                for i in range(nvals):
                    _name, value, _ = winreg.EnumValue(key, i)  # type: ignore[name-defined]
                    if not isinstance(value, str):
                        continue
                    v = value.strip().strip('"')
                    if not v:
                        continue
                    p = Path(v)
                    if p.is_absolute():
                        if p.exists():
                            found.append(p)
                        continue
                    for d in font_dirs:
                        candidate = d / v
                        if candidate.exists():
                            found.append(candidate)
                            break
        except FileNotFoundError:
            continue

    # Best-effort: include fonts present in directories but not in registry
    for d in font_dirs:
        for ext in (".ttf", ".otf", ".ttc", ".woff", ".woff2"):
            found.extend(d.glob(f"*{ext}"))

    return sorted({p.resolve() for p in found})


# -----------------------
# Linux-only: FontConfig enrichment
# -----------------------
def fc_query_raw(path: Path) -> str:
    proc = run_command(["fc-query", str(path)])
    return proc.stdout


def fc_query_extract(path: Path, include_charset: bool = False) -> Dict[str, Any]:
    """Extract a small set of useful FontConfig-derived fields."""
    raw = fc_query_raw(path)

    def _find_line(prefix: str) -> Optional[str]:
        for line in raw.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return None

    lang = _find_line("lang:")
    languages: List[str] = []
    if lang:
        languages = [x.strip() for x in lang.split("|") if x.strip()]

    decorative = (_find_line("decorative:") or "").strip().lower() == "true"
    color = (_find_line("color:") or "").strip().lower() == "true"
    variable = (_find_line("variable:") or "").strip().lower() == "true"
    capability = _find_line("capability:")

    scripts: List[str] = []
    if capability:
        for token in capability.replace('"', "").split():
            if token.startswith("otlayout:"):
                scripts.append(token.split(":", 1)[1])

    charset_blob: Optional[str] = None
    if include_charset:
        lines = raw.splitlines()
        try:
            idx = next(
                i for i, linea in enumerate(lines) if linea.startswith("charset:")
            )
            blob: List[str] = [lines[idx]]
            for j in range(idx + 1, len(lines)):
                linea = lines[j]
                if not linea.strip():
                    break
                blob.append(linea)
            charset_blob = "\n".join(blob)
        except StopIteration:
            charset_blob = None

    return {
        "languages": languages,
        "scripts": sorted(set(scripts)),
        "decorative": decorative,
        "color": color,
        "variable": variable,
        "charset": charset_blob,
    }


# -----------------------
# fontTools extraction
# -----------------------
NAME_ID_FAMILY = 1
NAME_ID_SUBFAMILY = 2
NAME_ID_LICENSE = 13
NAME_ID_LICENSE_URL = 14
NAME_ID_POSTSCRIPT = 6


def _best_name(names: Dict[str, List[str]], name_id: int) -> Optional[str]:
    vals = names.get(str(name_id), [])
    vals = [v for v in vals if v and v.strip()]
    return vals[0] if vals else None


def fonttools_extract(
    path: Path, cache_dir: Path, use_cache: bool = True
) -> Dict[str, Any]:
    """Extract deep metadata via fontTools (robust, cached)."""
    data: Dict[str, Any] = {"ok": False}

    if not FONTTOOLS_AVAILABLE:
        return {"ok": False, "error": "fontTools not available"}

    key = font_cache_key(path)
    cache_file = cache_dir / f"{key}.tt.json"
    if use_cache and cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    container = detect_font_container(path)
    data["container"] = container

    try:
        tt = TTFont(  # type: ignore[misc]
            path, lazy=True, recalcBBoxes=False, recalcTimestamp=False
        )
    except Exception as e:
        data["ok"] = False
        data["error"] = f"Cannot open font: {e}"
        cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    data["ok"] = True
    data["tables"] = sorted(tt.keys())

    if "CFF " in tt:
        data["font_type"] = "OpenType CFF"
    elif "glyf" in tt:
        data["font_type"] = "TrueType"
    else:
        data["font_type"] = "Unknown"

    color_tables = {"COLR", "CPAL", "CBDT", "CBLC", "sbix", "SVG "}
    data["color_tables"] = sorted([t for t in color_tables if t in tt])

    names: Dict[str, Any] = {}
    if "name" in tt:
        for rec in tt["name"].names:
            try:
                value = rec.toUnicode()
            except Exception:
                try:
                    value = rec.string.decode("utf-8", errors="ignore")
                except Exception:
                    value = str(rec.string)
            names.setdefault(str(rec.nameID), set()).add(value)
    data["names"] = {k: sorted(list(v)) for k, v in names.items()}

    unicodes = set()
    if "cmap" in tt:
        try:
            for table in tt["cmap"].tables:
                unicodes.update(table.cmap.keys())
        except Exception as e:
            data["cmap_error"] = str(e)

    if unicodes:
        data["unicode"] = {
            "count": len(unicodes),
            "min": f"U+{min(unicodes):04X}",
            "max": f"U+{max(unicodes):04X}",
        }
    else:
        data["unicode"] = {"count": 0}

    data["variable"] = {
        "fvar": "fvar" in tt,
        "STAT": "STAT" in tt,
        "avar": "avar" in tt,
        "gvar": "gvar" in tt,
    }

    features = set()
    for table_tag in ("GSUB", "GPOS"):
        if table_tag in tt:
            try:
                table = tt[table_tag].table
                if getattr(table, "FeatureList", None):
                    for feat in table.FeatureList.FeatureRecord:
                        features.add(feat.FeatureTag)
            except Exception as e:
                data[f"{table_tag}_error"] = str(e)
    data["opentype_features"] = sorted(features)

    if "OS/2" in tt:
        try:
            os2 = tt["OS/2"]
            data["os2"] = {
                "weight_class": getattr(os2, "usWeightClass", None),
                "width_class": getattr(os2, "usWidthClass", None),
                "fs_type": getattr(os2, "fsType", None),
                "vendor_id": getattr(os2, "achVendID", b"")
                .decode("ascii", errors="ignore")
                .strip(),
                "version": getattr(os2, "version", None),
            }
        except Exception as e:
            data["os2"] = {"error": f"OS/2 table unreadable: {e}"}

    try:
        tt.close()
    except Exception:
        pass

    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


# -----------------------
# Normalization into canonical schema
# -----------------------
def classify_font(
    format_block: Dict[str, Any], unicode_max: Optional[str]
) -> Dict[str, bool]:
    is_color = bool(format_block.get("color"))
    has_emoji_range = False
    try:
        if unicode_max and unicode_max.startswith("U+"):
            max_cp = int(unicode_max[2:], 16)
            has_emoji_range = max_cp >= 0x1F300
    except Exception:
        pass

    is_emoji = is_color or has_emoji_range
    is_decorative = bool(format_block.get("decorative", False))
    is_text = not is_emoji
    return {"is_text": is_text, "is_decorative": is_decorative, "is_emoji": is_emoji}


def build_font_descriptor(
    font_path: Path,
    platform_name: str,
    fonttools: Dict[str, Any],
    fontconfig: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    names: Dict[str, List[str]] = (
        fonttools.get("names", {})
        if isinstance(fonttools.get("names", {}), dict)
        else {}
    )
    family = _best_name(names, NAME_ID_FAMILY)
    style = _best_name(names, NAME_ID_SUBFAMILY)
    postscript = _best_name(names, NAME_ID_POSTSCRIPT)

    languages: List[str] = []
    scripts: List[str] = []
    charset: Optional[str] = None
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
    variable_flags = fonttools.get("variable", {})
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
        embedding_rights = os2.get("fs_type")

    descriptor = {
        "identity": {
            "file": str(font_path),
            "family": family,
            "style": style,
            "postscript_name": postscript,
        },
        "format": {
            "container": container,
            "font_type": font_type,
            "variable": variable,
            "color": color,
        },
        "coverage": coverage,
        "typography": typography,
        "classification": classification,
        "license": {
            "vendor": vendor,
            "embedding_rights": embedding_rights,
            "text": license_text,
            "url": license_url,
        },
        "sources": {
            "fonttools": bool(fonttools.get("ok", False)),
            "fontconfig": bool(fontconfig is not None),
            "windows_registry": platform_name == "windows",
        },
    }

    if not fonttools.get("ok", False):
        descriptor["sources"]["fonttools_error"] = fonttools.get("error", "unknown")

    return descriptor


# -----------------------
# Main dump function
# -----------------------
def dump_fonts(
    output_path: Path,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    include_fontconfig: bool = True,
    include_charset: bool = False,
    use_cache: bool = True,
    strict: bool = False,
) -> None:
    """Generate a canonical font inventory JSON for the current platform."""
    cache_dir.mkdir(exist_ok=True, parents=True)

    platform_name = (
        "windows" if IS_WINDOWS else "linux" if IS_LINUX else platform.system().lower()
    )

    font_files = get_installed_font_files()

    inventory: Dict[str, Any] = {
        "metadata": {
            "generator": "Fontshow dump_fonts.py",
            "platform": platform_name,
            "generated_at": utc_now_iso(),
            "python": sys.version.split()[0],
        },
        "fonts": [],
    }

    if IS_LINUX and include_fontconfig:
        try:
            inventory["metadata"]["fontconfig"] = run_command(
                ["fc-list", "--version"]
            ).stdout.strip()
        except Exception:
            inventory["metadata"]["fontconfig"] = "unknown"

    for p in font_files:
        if not p.exists():
            if strict:
                raise FileNotFoundError(str(p))
            continue

        ft = fonttools_extract(p, cache_dir=cache_dir, use_cache=use_cache)

        fc: Optional[Dict[str, Any]] = None
        if IS_LINUX and include_fontconfig:
            try:
                fc = fc_query_extract(p, include_charset=include_charset)
            except Exception as e:
                if strict:
                    raise
                fc = {"error": str(e)}

        descriptor = build_font_descriptor(
            p,
            platform_name,
            ft,
            fc if isinstance(fc, dict) and "error" not in fc else None,
        )
        inventory["fonts"].append(descriptor)

    inventory["fonts"].sort(
        key=lambda d: (
            d["identity"].get("family") or "",
            d["identity"].get("style") or "",
            d["identity"].get("file") or "",
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a canonical font inventory (JSON) for Fontshow.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("font_inventory.json"),
        help="Output JSON file",
    )
    p.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Cache directory for per-font analyses",
    )
    p.add_argument("--no-cache", action="store_true", help="Disable cache reuse")
    p.add_argument(
        "--no-fontconfig",
        action="store_true",
        help="Linux only: disable FontConfig enrichment",
    )
    p.add_argument(
        "--include-charset",
        action="store_true",
        help="Linux only: include the (large) FontConfig charset block",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Abort on errors instead of recording them and continuing",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if not FONTTOOLS_AVAILABLE:
        print(
            "WARNING: fontTools not available. Inventory will be incomplete.",
            file=sys.stderr,
        )

    try:
        dump_fonts(
            output_path=args.output,
            cache_dir=args.cache_dir,
            include_fontconfig=not args.no_fontconfig,
            include_charset=args.include_charset,
            use_cache=not args.no_cache,
            strict=args.strict,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(f"OK: wrote inventory to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
