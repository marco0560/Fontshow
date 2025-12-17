# Fontshow

Fontshow generates a PDF (using LuaLaTeX) catalog of the system fonts installed on the machine.
The main goal is to produce human-readable LaTeX catalogs (`catalogo_font_sistema_<PLATFORM>_<YYYYMMDD>_NNN.tex`) that, when compiled with lualatex will produce the desired `catalogo_font_sistema_<PLATFORM>_<YYYYMMDD>_NNN.pdf` and a few temporary index files (i.e. `*.working`, `*.broken`, `*.excluded`).

## Quick start (Windows)

1. Ensure a recent `latex` system (i.e. `texlive`) is installed
2. Ensure `fontconfig` is installed and `python3` is available.
3. From the repository root run:

```bash
python3 crea_catalogo.py
```

3. To build the catalog PDF (run twice for TOC/counters):

```bash
lualatex catalogo_font_sistema.tex
lualatex catalogo_font_sistema.tex
```
## Quick start (Linux)

1. Ensure a recent `latex` system (i.e. `texlive`) is installed
2. Ensure `fontconfig` is installed and `python3` and `fc-list` are available.
3. From the repository root run:

```bash
python3 crea_catalogo.py
```

3. To build the catalog PDF (run twice for TOC/counters):

```bash
lualatex catalogo_font_sistema.tex
lualatex catalogo_font_sistema.tex
```

## Useful flags

- `-h` : help mode — print help text an exit
- `-t` : test mode — parse fonts and write `test_output_<PLATFORM>_<DATE>.txt` with raw and cleaned names.
- `-n N` : limit to first `N` fonts (if `N>0`) or last `|N|` fonts (if `N<0`) — useful during debugging.
- `-T` : filter using the `TEST_FONTS` set.

The flags have also a long form:
- `-h` - `--help`
- `-t` - `--test`
- `-T` - `--TestFixed`
- `-n N` - `--number N`

Example (limit & test):

```bash
python3 crea_catalogo.py -t -n 20
```

## Windows notes

Windows support reads the font registry via `winreg`. Changes to Windows-specific discovery live in the same entrypoint; test Windows changes on a Windows machine.

## Key files

- `crea_catalogo.py` — main multi-platform entrypoint. Platform dispatchers and LaTeX generation live here.
- `scripts/parse_fc_list.py` — parser helper and test harness for `fc-list` output.
- `scripts/crea_catalogo_esclusi.py` — helper to manage excluded fonts.
- `scripts/prova_aggiunte.py` — ad-hoc test additions.

## Important symbols & conventions

- Preserve public interfaces: `get_installed_fonts()` must return `list[str]`.
- Platform helpers: `get_installed_fonts_linux()`, `get_installed_fonts_windows()`.
- Parsing helpers: `extract_font_family()`, `clean_font_name()`.
- LaTeX helpers: `generate_latex(font_list)`, `escape_latex(text)` — always escape inserted text.
- Config: `OUTPUT_FILENAME`, `EXCLUDED_FONTS`, `SPECIAL_SCRIPT_FONTS`, `TEST_FONTS`.

The code embeds large triple-quoted LaTeX templates — whitespace and blank lines matter for output formatting.

## Testing & validation

- Syntax check: `python -m py_compile crea_catalogo.py`
- Use `python3 crea_catalogo.py -t` and `scripts/parse_fc_list.py` for parser debugging (include sample `fc-list` lines when changing parsing logic).
- After changing LaTeX templates, compile the generated `.tex` with `lualatex` twice and inspect the PDF.

## Contributing / PR guidance for AI agents

- Keep changes small and focused. When updating parsing, include at least one real `fc-list` sample line and the expected cleaned family name in the PR body.
- If you must change the return shape of `get_installed_fonts*`, open a maintainer question first.

## Contact / questions

If something is unclear, specify the target platform (Linux vs Windows) and provide sample `fc-list` lines for parsing changes.
