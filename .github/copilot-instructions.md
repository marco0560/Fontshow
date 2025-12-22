# Copilot / AI assistant guidance for Fontshow

Purpose
- Create a LuaLaTeX catalog of system fonts. Primary outputs: `catalogo_font_sistema_<PLATFORM>_<YYYYMMDD>_*.tex` and temporary indexes (`*.working`, `*.broken`, `*.excluded`).

Quick commands (Linux-focused)
- Ensure `fontconfig` is available (`fc-list`).
- Run the main script from the repo root:

```bash
python3 crea_catalogo.py
```

- Test parsing only (produces `test_output_<PLATFORM>_<DATE>.txt`):

```bash
python3 crea_catalogo.py -t
```

- Limit fonts for quick runs: `python3 crea_catalogo.py -n N` (first N if positive, last |N| if negative).
- Use the test font set: `python3 crea_catalogo.py -T` (uses `TEST_FONTS`).
- Build the PDF output with LuaLaTeX (run twice to update TOC/counters):

```bash
lualatex catalogo_font_sistema.tex
lualatex catalogo_font_sistema.tex
```

Where to edit (key files)
- `crea_catalogo.py`: single, multi-platform entrypoint. Modify platform dispatch and main flow here.
- `scripts/parse_fc_list.py`: parser helper and test harness — use it to validate `fc-list` input and craft example lines for parser changes.
- `scripts/dump_fonts_fc.py` and `scripts/dump_fonts.py`: utilities for dumping fonts — inspect for platform-specific behavior.
- `scripts/crea_catalogo_esclusi.py`: helper for maintaining `EXCLUDED_FONTS`.

Important symbols and API stability
- Preserve these public symbols and return shapes when modifying code:
  - `get_installed_fonts()` -> returns `list[str]`
  - `get_installed_fonts_linux()` / `get_installed_fonts_windows()` -> platform implementations
  - `extract_font_family()` / `clean_font_name()` -> parsing/normalization helpers
  - `generate_latex(font_list)` -> emits final LaTeX (templates rely on exact whitespace)
  - `escape_latex(text)` -> must be used for any filename/text inserted into templates

Config points and conventions
- `OUTPUT_FILENAME`, `EXCLUDED_FONTS`, `SPECIAL_SCRIPT_FONTS`, `TEST_FONTS` are project-level constants — change cautiously.
- The LaTeX templates are embedded with triple-quoted strings; preserve indentation and blank lines exactly.
- `EXCLUDED_FONTS` contains families that break LuaLaTeX — only add after reproducing the failure and documenting why.

Testing and validation
- Syntax check Python files before running: `python -m py_compile crea_catalogo.py`
- For parser changes, include one or more real `fc-list` sample lines and run `scripts/parse_fc_list.py` to show before/after cleaning.
- When changing LaTeX output, compile the produced `catalogo_font_sistema*.tex` with `lualatex` (x2) and inspect the PDF.

PR guidance for AI agents
- Keep changes small and focused. If modifying parsing, include sample `fc-list` input and the resulting cleaned family name in the PR description.
- Run a limited test while developing: `python3 crea_catalogo.py -t -n 20`.

If unclear
- Ask which platform (Linux vs Windows) to target and provide `fc-list` sample lines when proposing parser changes.

Files of interest
- `crea_catalogo.py` — main script and entrypoint
- `scripts/parse_fc_list.py` — parser helper and test harness
- `scripts/crea_catalogo_esclusi.py` — excluded-font helper
- `scripts/prova_aggiunte.py` — addition test script

-- End of guidance
# Copilot / AI assistant guidance for Fontshow

Purpose
- Create a LuaLaTeX catalog of system fonts. Primary outputs: `catalogo_font_sistema_<PLATFORM>_<YYYYMMDD>_*.tex` and temporary indexes (`*.working`, `*.broken`, `*.excluded`).

Quick commands (Linux-focused)
- Ensure `fontconfig` is available (`fc-list`).
- Run: `python3 crea_catalogo.py` (from repository root).
- Test parsing only: `python3 crea_catalogo.py -t` -> produces `test_output_<PLATFORM>_<DATE>.txt` with raw and cleaned font names.
- Limit fonts: `python3 crea_catalogo.py -n N` (first N if positive, last |N| if negative).
- Filter by test set: `python3 crea_catalogo.py -T` (uses `TEST_FONTS`).
- Build the PDF: run `lualatex catalogo_font_sistema.tex` twice to update TOC/counters.

Where to edit
- `crea_catalogo.py`: single, multi-platform entrypoint. Change platform logic here.
- Platform helpers to update: `get_installed_fonts_linux()`, `get_installed_fonts_windows()`.
- Parsing helper: `scripts/parse_fc_list.py` — use this to validate `fc-list` parsing and to craft example lines for tests.

Key symbols to preserve
- `get_installed_fonts()` — public dispatcher (must return `list[str]`).
- `get_installed_fonts_linux()`, `get_installed_fonts_windows()` — platform implementations.
- `extract_font_family()` / `clean_font_name()` — core parsing/normalization helpers.
- `generate_latex(font_list)` — emits final LaTeX (templates use exact whitespace).
- `escape_latex(text)` — must be used for any filename/text inserted into templates.
- Config points: `OUTPUT_FILENAME`, `EXCLUDED_FONTS`, `SPECIAL_SCRIPT_FONTS`, `TEST_FONTS`.

Repo conventions and gotchas
- The script embeds large triple-quoted LaTeX templates — preserve indentation and blank-lines exactly.
- `EXCLUDED_FONTS` lists families that break LuaLaTeX; only add to it after reproducing the failure and documenting the cause.
- API stability: do not change return shapes for `get_installed_fonts*` (they return `list[str]`). Open a maintainer question before changing.

Testing & validation
- Syntax check: `python -m py_compile crea_catalogo.py`.
- For parser changes, provide one or more real `fc-list` sample lines and run `scripts/parse_fc_list.py` to show before/after cleaning.
- When changing LaTeX output, compile `catalogo_font_sistema*.tex` with `lualatex` (x2) and inspect the generated PDF.

PR guidance for AI agents
- Keep changes small and focused. If you modify parsing, include sample `fc-list` input and the resulting cleaned family name in the PR body.
- Run `python3 crea_catalogo.py -t -n 20` locally to limit noise while debugging.

Files of interest
- `crea_catalogo.py` — main script (entrypoint).
- `scripts/parse_fc_list.py` — parser helper and test harness.
- `scripts/crea_catalogo_esclusi.py` — helper for excluded fonts.
- `scripts/prova_aggiunte.py` — add-on test script.

If unclear
- Ask: Which platform should be targeted (Linux vs Windows)? Provide `fc-list` sample lines when proposing parser changes.

-- End of guidance (please review and request edits)
