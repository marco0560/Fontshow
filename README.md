# Fontshow

Fontshow generates a PDF catalog of the system fonts installed on the machine.
It first produces a human-readable LaTeX catalog (`catalogo_font_sistema_<PLATFORM>_<YYYYMMDD>_NNN.tex`) that, when compiled with lualatex, will produce the desired `catalogo_font_sistema_<PLATFORM>_<YYYYMMDD>_NNN.pdf` and a few temporary index files (i.e. `*.working`, `*.broken`, `*.excluded`) that cam be deleted.

## Quick start (Windows)

1. Ensure a recent `latex` system (i.e. `texlive`) is installed
2. Ensure `fontconfig` is installed and `python3` is available.
3. From the repository root run:

```bash
python3 crea_catalogo.py
```

4. To build the catalog PDF (run twice for TOC/counters):

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

4. To build the catalog PDF (run twice for TOC/counters):

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
- `--help ` for `-h`
- `--test ` for `-t`
- `--TestFixed ` for `-T`
- `--number N ` for `-n N`

Example (limit & test):

```bash
python3 crea_catalogo.py -t -n 20
```

## Windows notes

Windows support reads the font registry via `winreg`. Changes to Windows-specific discovery live in the same entrypoint; test Windows changes on a Windows machine.

## Commit policy

This program uses the **Conventional Commits** standard with aoutomatic enforcement through Git hooks and CI.

### Mandatory Format

```text
type(scope): summary
```

or, for breaking changes:

```text
type(scope)!: summary
```

with an optional footer:

```text
BREAKING CHANGE: description of the breaking change
```

---

### Allowed Types

* **feat** – new feature
* **fix** – bug fix
* **docs** – documentation
* **refactor** – refactoring without functional changes
* **test** – tests
* **chore** – maintenance, tooling, CI, release

### Allowed Scopes

Scopes must belong to the project whitelist, for example:

* `core`
* `cli`
* `parser`
* `output`
* `config`
* `build`
* `git`
* `release`
* `docs`
* `ci`

---

### Length and Style

* The first line of the commit **must not exceed 72 characters**.
* The summary must be in English, **imperative** (e.g., "add" instead of "added"), and without a trailing period.

---

### Valid Examples

```text
feat(core): add font filtering support
fix(cli): handle missing input file
feat(core)!: change default output format
```

### Invalid Examples

```text
Added new feature
fix bug
feat: too generic
```

### Enforcement

* Non-compliant commits are blocked locally via git hooks.

* CI rejects any non-compliant commit.

* Versioning and changelog generation are entirely automatic.

---

### Commit Signing

All commits must be signed with a verifiable signature.

## Key files

- `crea_catalogo.py` — main multi-platform entrypoint. Platform dispatchers and LaTeX generation live here.
- `scripts/parse_fc_list.py` — parser helper and test harness for `fc-list` output.
- `scripts/crea_catalogo_esclusi.py` — helper to manage excluded fonts.
- `scripts/prova_aggiunte.py` — ad-hoc test additions.

## Additional tools and documentation

Fontshow also includes auxiliary scripts for font inspection and analysis.

- `scripts/dump_fonts_fc.py` — advanced font inventory and metadata extraction
  (FontConfig + fontTools, caching, WOFF/WOFF2 support).

Detailed documentation is available in the `docs/` directory:

- `docs/font-inventory.md`
- `docs/fonttools-integration.md`

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
