# Copilot / AI Assistant instructions for this repo

Purpose
- This repository contains `crea_catalogo.py`, a Python script that enumerates system fonts and generates a LuaLaTeX catalog (`catalogo_font_sistema.tex`).

Quick run
- Ensure `fontconfig` is installed on Linux (`fc-list` available).
- Generate the .tex file:
  `python3 crea_catalogo.py`
- Compile with LuaLaTeX (run twice):
  `lualatex catalogo_font_sistema.tex`

Key files
- `crea_catalogo.py`: main script. Edit only if you understand font detection and LaTeX escaping.

Important variables / behavior
- `OUTPUT_FILENAME`: filename written by the script (default `catalogo_font_sistema.tex`).
- `EXCLUDED_FONTS`: set of font family names skipped because they are known-problematic.
- `SPECIAL_SCRIPT_FONTS`: mapping of specific families to language/script options (polyglossia + fontspec).
- On Linux the script uses `fc-list` to enumerate fonts; on Windows it reads the registry via `winreg`.

Formatting constraints
- Preserve indentation and spacing inside the triple-quoted LaTeX sample strings — the LaTeX output layout depends on exact whitespace.
- When adding features, keep LaTeX escaping (`escape_latex`) robust for backslashes and special characters.

When modifying font detection
- Prefer `fc-list -f '%{file}:%{family}\n'` on Linux to reliably capture filenames.
- Any change to `get_installed_fonts*` must keep compatibility with `generate_latex()` or update the generator accordingly.
 - For now: when making code changes, modify only the Linux execution path. Limit edits to `get_installed_fonts_linux` and Linux-specific helpers; avoid changing the Windows codepath (`get_installed_fonts_windows`) or shared interfaces unless you get explicit confirmation.

Testing & validation
- Run `python -m py_compile crea_catalogo.py` before executing to catch syntax issues.
- Use the helper script `scripts/parse_fc_list.py` (if present) to preview `fc-list` parsing.

If you are an AI assistant
- Ask for clarification before making breaking changes that alter function return types (e.g., from `list[str]` to `list[tuple]`).
- If adding filenames to the LaTeX output, ensure they are escaped for LaTeX and do not change the public API unless requested.

Notes for maintainers
- The script targets LuaLaTeX (`fontspec`, `polyglossia`). Keep LuaLaTeX references intact.
- Platform differences: maintain a `winreg = None` placeholder on non-Windows during cross-platform development to avoid import errors.

End of instructions.
