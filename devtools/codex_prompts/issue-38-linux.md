Work on GitHub issue `#38` on native Linux.

Issue scope:
- `#38` is `core(path): validate cross-platform path handling (Linux / WSL)`.
- This prompt is for the Linux-native part only.
- Do not implement native Windows work here. Native Windows belongs to `#51`.
- Do not assume WSL access in this session. WSL-specific validation is handled later by `issue-38-wsl.md`.

Repository rules:
1. Read `AGENTS.md` and follow it strictly.
2. We are in the Fontshow repo and inside the repository `.venv`.
3. Use `repoindex` before broad exploration.
4. Follow `devtools/codex_prompts/issue.md`, but apply the platform scoping in this prompt.

Execution goals on Linux:
1. Re-read `issues.json` for `#38`.
2. Reproduce the current Linux-native path-handling behavior.
3. Identify all path-normalization and path-consumption code that can differ between native Linux and WSL.
4. Determine the minimal Linux-executable hardening work that improves Linux/WSL shared path handling without needing a real WSL environment yet.
5. Add deterministic tests for Linux-side invariants and for any WSL-detectable logic that can be simulated safely from Linux.
6. Do not claim WSL runtime behavior is fully validated unless it was actually exercised in WSL.

Primary investigation targets:
- `src/fontshow/`
- `tests/`
- any path helpers, CLI path resolution, inventory path persistence, and LaTeX/path normalization helpers
- docs mentioning Linux/WSL path behavior

Expected output of this task:
1. Minimal code changes for Linux/WSL-shared path handling that can be implemented safely on Linux.
2. Deterministic tests covering the new invariants.
3. A short residual list of what still must be validated or adjusted in real WSL.
4. A commit block that references `#38` only if the Linux-native portion is sufficient to close it; otherwise use `Refs: #38` and state what remains for WSL.

Important constraints:
- No native Windows work.
- No speculative WSL fixes without file-grounded evidence.
- No environment-dependent tests requiring WSL, LaTeX, or external binaries.
- Keep changes minimal and localized.
