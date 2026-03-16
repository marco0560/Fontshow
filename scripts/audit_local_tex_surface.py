#!/usr/bin/env python3
"""
Audit the local TeX installation surface used by Fontshow.

This maintenance script inspects the locally installed ``fontspec`` and
``polyglossia`` resources and emits a deterministic JSON summary of the
script and language surface available to catalog rendering.

Responsibilities
----------------
- Parse locally installed ``fontspec`` script declarations.
- Parse locally installed Polyglossia language modules.
- Produce a normalized JSON report for downstream gap analysis.

Design principles
-----------------
The audit is local-only and deterministic. It does not query the
network, modify TeX state, or depend on project runtime code outside
the committed ontology package.

Architectural role
------------------
This script belongs to the developer tooling layer and supports
maintenance of the TeX/ontology alignment workflow.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

_FONT_SPEC_DEFAULT = Path(
    "/usr/share/texmf-dist/tex/latex/fontspec/fontspec-luatex.sty"
)
_POLYGLOSSIA_DEFAULT = Path("/usr/share/texmf-dist/tex/latex/polyglossia")
_SCRIPT_PATTERN = re.compile(r"\\newfontscript\{([^}]+)\}\{")


def extract_fontspec_scripts(fontspec_text: str) -> list[str]:
    """
    Extract declared fontspec script names from a style file.

    Parameters
    ----------
    fontspec_text : str
        Raw contents of ``fontspec-luatex.sty``.

    Returns
    -------
    list[str]
        Sorted unique script names accepted by ``fontspec``.
    """
    return sorted(
        {name.replace("~", " ") for name in _SCRIPT_PATTERN.findall(fontspec_text)}
    )


def extract_polyglossia_languages(polyglossia_dir: Path) -> list[str]:
    """
    Extract installed Polyglossia language module names.

    Parameters
    ----------
    polyglossia_dir : pathlib.Path
        Directory containing ``gloss-*.ldf`` modules.

    Returns
    -------
    list[str]
        Sorted unique language/module names.
    """
    return sorted(
        {
            path.stem.replace("gloss-", "")
            for path in polyglossia_dir.glob("gloss-*.ldf")
            if path.is_file()
        }
    )


def build_local_tex_surface(
    *,
    fontspec_path: Path,
    polyglossia_dir: Path,
) -> dict[str, object]:
    """
    Build a normalized summary of the local TeX support surface.

    Parameters
    ----------
    fontspec_path : pathlib.Path
        Path to ``fontspec-luatex.sty``.
    polyglossia_dir : pathlib.Path
        Directory containing Polyglossia language modules.

    Returns
    -------
    dict[str, object]
        JSON-serializable local TeX audit payload.

    Raises
    ------
    FileNotFoundError
        Raised when either local TeX resource path is missing.
    """
    if not fontspec_path.exists():
        msg = f"fontspec file not found: {fontspec_path}"
        raise FileNotFoundError(msg)
    if not polyglossia_dir.exists():
        msg = f"polyglossia directory not found: {polyglossia_dir}"
        raise FileNotFoundError(msg)

    fontspec_text = fontspec_path.read_text(encoding="utf-8", errors="replace")
    fontspec_scripts = extract_fontspec_scripts(fontspec_text)
    polyglossia_languages = extract_polyglossia_languages(polyglossia_dir)

    return {
        "fontspec_path": str(fontspec_path),
        "polyglossia_dir": str(polyglossia_dir),
        "fontspec_scripts": fontspec_scripts,
        "polyglossia_languages": polyglossia_languages,
        "counts": {
            "fontspec_scripts": len(fontspec_scripts),
            "polyglossia_languages": len(polyglossia_languages),
        },
    }


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the TeX surface audit.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fontspec-path",
        type=Path,
        default=_FONT_SPEC_DEFAULT,
        help="Path to fontspec-luatex.sty",
    )
    parser.add_argument(
        "--polyglossia-dir",
        type=Path,
        default=_POLYGLOSSIA_DEFAULT,
        help="Directory containing gloss-*.ldf files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/local_tex_surface.json"),
        help="Output JSON report path",
    )
    return parser.parse_args()


def main() -> int:
    """
    Execute the local TeX audit and write the JSON report.
    """
    args = parse_args()
    report: dict[str, Any] = build_local_tex_surface(
        fontspec_path=args.fontspec_path,
        polyglossia_dir=args.polyglossia_dir,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {args.output}")
    print(
        "[OK] "
        f"fontspec scripts={report['counts']['fontspec_scripts']} "
        f"polyglossia languages={report['counts']['polyglossia_languages']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
