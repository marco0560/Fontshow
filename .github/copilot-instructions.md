# Copilot / AI assistant guidance for Fontshow

Purpose
- Generate a LuaLaTeX catalog of system fonts. Primary outputs: `catalogo_font_sistema.tex` and temporary index files (`*.working`, `*.broken`, `*.excluded`).

Quick run (platform-specific)
- Linux: ensure `fontconfig` is installed (`fc-list` available).
  - Run: `python3 crea_catalogo.py`
  - Then: `lualatex catalogo_font_sistema.tex` (run twice)
- Windows: run from the workspace root (uses `winreg`):
    - `python crea_catalogo.py`
    - `lualatex catalogo_font_sistema.tex`
- Test parsing: `python3 crea_catalogo.py -t` generates `test_output_<platform>_<date>.txt` with raw font data and cleaned names.
- Limit fonts: `python3 crea_catalogo.py -n N` processes only the first N fonts (if positive) or the last |N| fonts (if negative) (can combine with -t).
- Filter fonts: `python3 crea_catalogo.py -T` processes only fonts containing substrings from TEST_FONTS set (can combine with -t and -n).

Where to work
- `crea_catalogo.py`: main multi-platform script (detects OS at runtime). Use this for cross-platform changes or new features.
- For platform-specific adjustments: edit `get_installed_fonts_linux()` or `get_installed_fonts_windows()` within `crea_catalogo.py`.
- `scripts/parse_fc_list.py`: helper for previewing/parsing `fc-list` output.
- `scripts/crea_catalogo_esclusi.py`: variant script (purpose unclear, check code).
- `scripts/prova_aggiunte.py`: test script for additions.

Key functions & variables (search these exact names)
- `get_installed_fonts()` — public entry point that dispatches to platform-specific implementations.
- `get_installed_fonts_linux()` / `get_installed_fonts_windows()` — platform font discovery.
- `extract_font_family()` — helper that parses `fc-list` lines (Linux parsing is fragile; prefer using the helper when changing output format).
- `clean_font_name()` — normalizes registry/fc-list names to family names.
- `generate_latex(font_list)` — builds the LaTeX document (contains large triple-quoted templates where whitespace matters).
- `escape_latex(text)` — escapes LaTeX special characters; always run filenames/texts through it before injecting into templates.
- `OUTPUT_FILENAME`, `EXCLUDED_FONTS`, `SPECIAL_SCRIPT_FONTS`, `TEST_FONTS` — config points you will commonly change.

Conventions & constraints specific to this repo
- Multi-platform in single file: script detects OS and uses appropriate font discovery method.
- API stability: do not change return shapes of the `get_installed_fonts*` functions (they return `list[str]` of family names). If you must change types, ask the maintainer first.
- LaTeX templates: preserve exact indentation and spacing within triple-quoted LaTeX strings. Formatting/whitespace affects the rendered PDF and index generation.
- Exclusions: `EXCLUDED_FONTS` contains families known to break LuaLaTeX; update with caution and document why a font was added.
- Output naming: includes platform and date (YYYYMMDD) in filename.

Dependencies & integration points
- Linux: `fc-list` (fontconfig). Use `scripts/parse_fc_list.py` to validate parsing changes.
- LaTeX: `lualatex` with packages `fontspec`, `polyglossia`, `tcolorbox`, `lipsum`, etc. Ensure TeXLive or MikTeX installation contains these packages.
- Windows: code reads font registry via `winreg` so tests/changes should be validated on Windows.

Developer workflows & checks
- Syntax check before running: `python -m py_compile crea_catalogo.py`.
- Quick local run: run the script from the workspace root matching the platform.
- Test font parsing: `python3 crea_catalogo.py -t` to generate detailed parsing output for debugging.
- Compile LaTeX twice to ensure TOC and counters are written: `lualatex catalogo_font_sistema.tex` (x2).
- Validate font parsing: use `scripts/parse_fc_list.py` to preview `fc-list` output and test `extract_font_family()` changes.

Guidance for AI agents
- Preserve existing naming and public interfaces (`get_installed_fonts`, `generate_latex`, `escape_latex`, `EXCLUDED_FONTS`).
- When updating parsing/formatting, add a small, targeted unit test or run `scripts/parse_fc_list.py` with sample `fc-list` output and include an example `fc-list` line in your change description.
- Ask clarifying questions before making breaking changes to return types or LaTeX structure.

Relevant files (examples)
- crea_catalogo.py — main multi-platform script
- scripts/parse_fc_list.py — helper parser for `fc-list`
- scripts/crea_catalogo_esclusi.py — variant script
- scripts/prova_aggiunte.py — test additions

If something is unclear
- Ask: which platform is the change targeting? Should platform-specific functions be adjusted?

End of file — please review and tell me if you want additional examples, more detailed run/debug steps, or CI/test snippets added.
