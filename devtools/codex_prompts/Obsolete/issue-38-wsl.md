Work on GitHub issue `#38` inside WSL after the Linux-native portion has been completed.

Issue scope:
- `#38` is `core(path): validate cross-platform path handling (Linux / WSL)`.
- This prompt is for the real WSL validation and any WSL-only fixes that remain after `issue-38-linux.md`.
- Do not broaden into native Windows work. Native Windows belongs to `#51`.

Repository rules:
1. Read `AGENTS.md` and follow it strictly.
2. We are in the Fontshow repo and inside the repository `.venv`.
3. Use `repoindex` before broad exploration.
4. Follow `devtools/codex_prompts/issue.md`, but apply the WSL scoping in this prompt.

Preconditions:
1. Review the Linux-native changes already made for `#38`.
2. Read the residual list or notes produced by the Linux task.
3. Confirm you are actually running inside WSL, not native Linux.

Execution goals in WSL:
1. Re-read `issues.json` for `#38`.
2. Reproduce the relevant path-handling behavior in real WSL.
3. Verify whether Linux-native fixes hold under WSL path semantics.
4. Identify the smallest remaining WSL-specific path issues, if any.
5. Implement only the minimal WSL-specific hardening needed to satisfy `#38`.
6. Add deterministic tests for logic that can be expressed without requiring future WSL-only CI; if a behavior can only be manually validated in WSL, document it explicitly rather than faking it.

Focus areas:
- path normalization
- repository-relative paths
- persisted inventory paths
- CLI path resolution
- interactions between WSL filesystem semantics and Linux-oriented code

Expected output of this task:
1. Minimal WSL-specific fixes, if needed.
2. Tests for any newly codified shared logic.
3. Explicit manual-validation notes for any behavior that cannot be encoded deterministically.
4. A clear statement whether `#38` is now complete or what remains for Linux closing.

Important constraints:
- Do not implement native Windows fixes here.
- Do not add tests that require a WSL runner.
- Keep all claims grounded in actual WSL execution from this session.
