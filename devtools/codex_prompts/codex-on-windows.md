Set up Codex on Windows for working on the Fontshow repository.

Goal:
- Prepare a Windows environment that can run Codex effectively for:
  - native Windows issue work such as `#51`
  - WSL issue work such as the WSL portion of `#38`

Recommended setup model:
1. Use **native Windows PowerShell** for native Windows issue work.
2. Use **WSL** for Linux/WSL issue work.
3. Keep one clone per environment if path semantics or interpreter setup differ materially.

## Part 1 — Native Windows prerequisites

1. Install Git for Windows.
2. Install Python 3.11+.
3. Install Node.js LTS if Codex or local tooling requires it.
4. Ensure `git`, `python`, `pip`, `node`, and `npm` are available in PowerShell.
5. Configure Git with the same identity/signing settings expected by this repository.

Recommended checks in PowerShell:

```powershell
git --version
python --version
pip --version
node --version
npm --version
```

## Part 2 — Clone the repository on Windows

1. Open PowerShell.
2. Clone the repository in a normal user-writable path, for example:

```powershell
cd $HOME
git clone git@github.com:marco0560/Fontshow.git
cd Fontshow
```

3. Verify the repository hook path if required by local setup:

```powershell
git config --local core.hooksPath .githooks
```

4. Inspect the local aliases you need:

```powershell
git config --local --get-regexp '^alias\.'
```

## Part 3 — Create the Python environment on Windows

From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
```

If `requirements-dev.txt` does not exist, inspect the repository’s actual dependency files and use those instead.

Verify:

```powershell
python -c "import fontshow; print(fontshow.__file__)"
pre-commit --version
pytest --version
```

## Part 4 — Install and verify Codex on Windows

Use the Codex installation method currently approved in your environment. If Codex is distributed through a package manager or installer in your setup, install it first, then verify:

```powershell
codex --help
```

If Codex requires authentication, complete the login flow before starting repository work.

## Part 5 — Recommended Windows working modes

### Native Windows mode

Use this for:
- `#51`
- any task that must observe native Windows font discovery, registry behavior, or Windows-only identity resolution

Start from:

```powershell
cd $HOME\Fontshow
.venv\Scripts\Activate.ps1
codex
```

### WSL mode

Use this for:
- the WSL portion of `#38`
- Linux-like validation that must run inside a real WSL environment

In WSL:

```bash
cd ~/Fontshow
source .venv/bin/activate
codex
```

## Part 6 — WSL installation notes

1. Install WSL and a Linux distribution.
2. Clone the repository inside the WSL filesystem, not under `/mnt/c`, unless you are explicitly validating cross-filesystem behavior.
3. Create a separate WSL `.venv`.
4. Install the same repository development dependencies there.

Recommended WSL setup:

```bash
git clone git@github.com:marco0560/Fontshow.git
cd Fontshow
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## Part 7 — Repository-specific working rules

Before starting issue work:
1. Read `AGENTS.md`.
2. Use the repository `.venv`.
3. Run `repoindex index`.
4. Use the dedicated prompt file for the issue you are working on.

Examples:
- native Linux: `devtools/codex_prompts/issue-38-linux.md`
- WSL: `devtools/codex_prompts/issue-38-wsl.md`
- native Windows: `devtools/codex_prompts/issue-51-windows.md`

## Part 8 — Minimum verification checklist

Before asking Codex to modify code, verify:

```powershell
pre-commit --version
pytest -q
```

or in WSL:

```bash
pre-commit --version
pytest -q
```

If the suite is too expensive to run immediately, at least verify:
- the environment activates correctly
- repository dependencies import correctly
- `repoindex` is installed and runnable

## Part 9 — Common pitfalls

- Do not use native Windows results as evidence for WSL behavior.
- Do not use WSL results as evidence for native Windows issue `#51`.
- Do not mix one `.venv` between native Windows and WSL.
- Do not work from a path with missing Git hook configuration if you expect repo hooks to run.
- Do not assume LaTeX availability unless you have verified it in that environment.
