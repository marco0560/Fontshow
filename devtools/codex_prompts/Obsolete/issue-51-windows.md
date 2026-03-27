Work on GitHub issue `#51` on native Windows 11.

Issue scope:
- `#51` is `Windows font identity resolution missing: catalog generation lacks loadable font references`.
- This prompt is for native Windows 11 only.
- Do not treat WSL as sufficient for this issue.
- Do not change Linux behavior except where cross-platform architecture requires a guarded, no-regression adaptation.

Repository rules:
1. Read `AGENTS.md` and follow it strictly.
2. We are in the Fontshow repo and inside the repository `.venv`.
3. Use `repoindex` before broad exploration.
4. Follow `devtools/codex_prompts/issue.md`, but apply the native-Windows scoping in this prompt.

Issue-grounded intent:
- Linux already has usable file/path/fontconfig-based identity.
- Native Windows can discover fonts, but catalog generation lacks loadable font references.
- The issue explicitly frames this as missing platform capability, not a Linux regression.

Execution goals on native Windows 11:
1. Re-read `issues.json` for `#51`.
2. Reproduce the current native Windows behavior end to end:
   - `preflight`
   - `dump-fonts`
   - `parse-inventory`
   - `create-catalog`
3. Identify the minimal missing identity data that prevents meaningful LaTeX font loading.
4. Implement the smallest viable Windows-native identity provider or enrichment path justified by the issue body and current architecture.
5. Keep provider selection explicit, testable, and platform-gated.
6. Avoid Linux regressions and avoid ad hoc LaTeX heuristics.

Suggested phased approach:
1. Phase A first: baseline Windows registry-backed identity resolution, if the current codebase still lacks it.
2. Only proceed toward more advanced Windows-native APIs if Phase A is insufficient and repository evidence supports it.
3. Do not start speculative LuaLaTeX cache introspection unless the issue work clearly requires it.

Validation expectations:
- Add deterministic tests for any platform-gated logic that can be unit-tested on any platform.
- If some behavior requires real Windows execution, document the manual validation explicitly.
- Do not add tests that require external Windows-only binaries beyond what is already assumed for the issue reproduction.

Expected output of this task:
1. Minimal Windows-native implementation for identity resolution.
2. Deterministic tests where possible.
3. Explicit native-Windows manual validation notes.
4. A statement of what, if anything, must be finished later on Linux integration/closing.

Important constraints:
- Do not weaken validation rules.
- Do not special-case LaTeX output with undocumented heuristics.
- Do not diverge Linux behavior.
- Keep the change minimal and architectural boundaries explicit.
