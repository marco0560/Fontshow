#!/usr/bin/env python3

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

# =======================
# Configurazione
# =======================

OUTPUT_FILE = Path("font_inventory.txt")
CACHE_DIR = Path(".font_cache")
CACHE_DIR.mkdir(exist_ok=True)

try:
    from fontTools.ttLib import TTFont

    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False


# =======================
# Utility
# =======================


def run_command(cmd):
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False
    )
    return result.stdout


def get_font_files():
    output = run_command(["fc-list", "--format=%{file}\n"])
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def font_cache_key(path: Path):
    """
    Crea una chiave stabile basata su path + mtime + size
    """
    stat = path.stat()
    key = f"{path}|{stat.st_mtime_ns}|{stat.st_size}"
    return hashlib.sha256(key.encode()).hexdigest()


def detect_font_container(path: Path):
    """
    Rileva il tipo di contenitore del font:
    TrueType / OpenType / WOFF / WOFF2
    """
    suffix = path.suffix.lower()

    if suffix == ".woff2":
        return "WOFF2"
    if suffix == ".woff":
        return "WOFF"

    try:
        with path.open("rb") as f:
            header = f.read(4)
            if header == b"wOFF":
                return "WOFF"
            if header == b"wOF2":
                return "WOFF2"
            if header in (b"\x00\x01\x00\x00", b"true"):
                return "TrueType"
            if header == b"OTTO":
                return "OpenType"
    except Exception:
        pass

    return "Unknown"


# =======================
# FontConfig (fc-query)
# =======================


def get_fc_query_data(path: Path):
    key = font_cache_key(path)
    cache_file = CACHE_DIR / f"{key}.fc.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    output = run_command(["fc-query", str(path)])
    data = {
        "tool": "fc-query",
        "raw": output,
    }

    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


# =======================
# fontTools (TTFont)
# =======================


def get_fonttools_data(path: Path):
    """
    Estrae metadati avanzati OpenType / TrueType tramite fontTools.
    Supporta TrueType, OpenType, WOFF e WOFF2.
    Usa caching persistente su disco.
    """

    data = {
        "source": "fontTools",
        "path": str(path),
    }

    # fontTools non disponibile
    if not FONTTOOLS_AVAILABLE:
        data["error"] = "fontTools non disponibile"
        return data

    # Cache
    key = font_cache_key(path)
    cache_file = CACHE_DIR / f"{key}.tt.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    # -----------------------
    # Rilevamento contenitore
    # -----------------------
    container = detect_font_container(path)
    data["container_format"] = container

    # -----------------------
    # Apertura font
    # -----------------------
    try:
        tt = TTFont(
            path,
            lazy=True,
            recalcBBoxes=False,
            recalcTimestamp=False,
        )
    except Exception as e:
        data["error"] = f"Impossibile aprire il font: {e}"
        cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    # -----------------------
    # Tipo font interno
    # -----------------------
    if "CFF " in tt:
        data["font_type"] = "OpenType CFF"
    elif "glyf" in tt:
        data["font_type"] = "TrueType"
    else:
        data["font_type"] = "Unknown"

    if container in ("WOFF", "WOFF2"):
        data["font_type"] = f"Web Open Font Format ({container})"

    # -----------------------
    # Tabelle presenti
    # -----------------------
    data["tables"] = sorted(tt.keys())

    # -----------------------
    # Name table (metadati testuali)
    # -----------------------
    names = {}
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

    data["names"] = {k: sorted(v) for k, v in names.items()}

    # -----------------------
    # Unicode coverage
    # -----------------------
    if "cmap" in tt:
        unicodes = set()
        for table in tt["cmap"].tables:
            unicodes.update(table.cmap.keys())

        if unicodes:
            data["unicode"] = {
                "codepoints": len(unicodes),
                "min": f"U+{min(unicodes):04X}",
                "max": f"U+{max(unicodes):04X}",
            }
        else:
            data["unicode"] = {"codepoints": 0}

    # -----------------------
    # Variable font
    # -----------------------
    data["variable_font"] = {
        "fvar": "fvar" in tt,
        "STAT": "STAT" in tt,
        "avar": "avar" in tt,
        "gvar": "gvar" in tt,
    }

    # -----------------------
    # OpenType layout features
    # -----------------------
    features = set()
    for table_tag in ("GSUB", "GPOS"):
        if table_tag in tt:
            table = tt[table_tag].table
            if table.FeatureList:
                for feat in table.FeatureList.FeatureRecord:
                    features.add(feat.FeatureTag)

    data["opentype_features"] = sorted(features)

    # -----------------------
    # OS/2 metrics (robusto)
    # -----------------------
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

    # -----------------------
    # Cleanup
    # -----------------------
    tt.close()

    # -----------------------
    # Scrittura cache
    # -----------------------
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return data


# =======================
# Main
# =======================


def main():
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        out.write(f"Font inventory generato il {datetime.now()}\n")
        out.write(f"Sistema: {run_command(['uname', '-a']).strip()}\n")
        out.write(f"{run_command(['fc-list', '--version']).strip()}\n")
        out.write("=" * 60 + "\n\n")

        for fontfile in get_font_files():
            path = Path(fontfile)

            out.write("-" * 60 + "\n")
            out.write(f"FONT FILE: {fontfile}\n")
            out.write("-" * 60 + "\n")

            if not path.is_file():
                out.write("ATTENZIONE: file non trovato\n\n")
                continue

            # FontConfig
            fc_data = get_fc_query_data(path)
            out.write("[FontConfig]\n")
            out.write(fc_data["raw"])
            out.write("\n")

            # fontTools
            tt_data = get_fonttools_data(path)
            out.write("[fontTools]\n")
            out.write(json.dumps(tt_data, indent=2))
            out.write("\n\n")

        out.write("Fine elenco font.\n")


if __name__ == "__main__":
    main()
