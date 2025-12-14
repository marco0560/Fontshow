<!-- Copilot instructions (merged from Linux/.github/copilot-instructions.md) -->
# Copilot / AI assistant guidance for Fontshow

Purpose
- Generate a LuaLaTeX catalog of system fonts. Primary outputs: `catalogo_font_sistema.tex` and temporary index files (`*.working`, `*.broken`, `*.excluded`).

Quick run (platform-specific)
- Linux: ensure `fontconfig` is installed (`fc-list` available).
  - cd into the folder containing the script (e.g. `Linux/` or `Misto/`) and run:
    ```bash
    python3 crea_catalogo.py
    lualatex catalogo_font_sistema.tex  # run twice
    ```
- Windows: run the Windows copy from `Windows/` (uses `winreg`):
    ```powershell
    cd Windows
    python crea_catalogo.py
    lualatex catalogo_font_sistema.tex
    ```

Where to work
- `Misto/crea_catalogo.py`: working multi-platform script (detects OS at runtime). Prefer this for cross-platform changes or add feature work that must run on both OSes.
- `Linux/crea_catalogo.py`: Linux-leaning copy (kept for reference/compatibility). Use it if you are only adjusting Linux-specific parsing.
- `Windows/crea_catalogo.py` and `Windows/crea_catalogo_esclusi.py`: Windows-specific copies. Edit these only for Windows-targeted fixes.
- `scripts/parse_fc_list.py`: helper for previewing/parsing `fc-list` output.

Key functions & variables (search these exact names)
- `get_installed_fonts()` — public entry point that dispatches to platform-specific implementations.
- `get_installed_fonts_linux()` / `get_installed_fonts_windows()` — platform font discovery.
- `extract_font_family()` — helper that parses `fc-list` lines (Linux parsing is fragile; prefer using the helper when changing output format).
- `clean_font_name()` — normalizes registry/fc-list names to family names.
- `generate_latex(font_list)` — builds the LaTeX document (contains large triple-quoted templates where whitespace matters).
- `escape_latex(text)` — escapes LaTeX special characters; always run filenames/texts through it before injecting into templates.
- `OUTPUT_FILENAME`, `EXCLUDED_FONTS`, `SPECIAL_SCRIPT_FONTS` — config points you will commonly change.

Conventions & constraints specific to this repo
- Platform separation: there are multiple copies of the script. Do not change Windows-only code on a Linux host and vice versa unless you update the corresponding platform file as well.
- API stability: do not change return shapes of the `get_installed_fonts*` functions (they return `list[str]` of family names). If you must change types, ask the maintainer first.
- LaTeX templates: preserve exact indentation and spacing within triple-quoted LaTeX strings. Formatting/whitespace affects the rendered PDF and index generation.
- Exclusions: `EXCLUDED_FONTS` contains families known to break LuaLaTeX; update with caution and document why a font was added.

Dependencies & integration points
- Linux: `fc-list` (fontconfig). Use `scripts/parse_fc_list.py` to validate parsing changes.
- LaTeX: `lualatex` with packages `fontspec`, `polyglossia`, `tcolorbox`, `lipsum`, etc. Ensure TeXLive or MikTeX installation contains these packages.
- Windows: code reads font registry via `winreg` so tests/changes should be validated on Windows.

Developer workflows & checks
- Syntax check before running: `python -m py_compile crea_catalogo.py`.
- Quick local run: run the script in the folder matching the platform or use `Misto/crea_catalogo.py` for cross-platform runs.
- Compile LaTeX twice to ensure TOC and counters are written: `lualatex catalogo_font_sistema.tex` (x2).

Guidance for AI agents
- Preserve existing naming and public interfaces (`get_installed_fonts`, `generate_latex`, `escape_latex`, `EXCLUDED_FONTS`).
- When updating parsing/formatting, add a small, targeted unit test or a `scripts/` preview invocation (e.g., run `parse_fc_list.py`) and include an example `fc-list` line in your change description.
- Ask clarifying questions before making breaking changes to return types or LaTeX structure.

Relevant files (examples)
- Misto/crea_catalogo.py — multi-platform working copy
- Linux/crea_catalogo.py — Linux-tailored copy
- Windows/crea_catalogo.py — Windows copy
- Windows/crea_catalogo_esclusi.py — helper/variants
- scripts/parse_fc_list.py — helper parser for `fc-list`

If something is unclear
- Ask: which platform is the change targeting? Should mirrors in the other folders be synchronized?

End of file — please review and tell me if you want additional examples, more detailed run/debug steps, or CI/test snippets added.
