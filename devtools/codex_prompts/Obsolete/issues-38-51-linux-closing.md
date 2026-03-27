Perform Linux-side closing work after the Windows tasks for `#38` and `#51` have been completed.

Scope:
- `#38` covers Linux native + WSL path handling.
- `#51` covers native Windows font identity resolution.
- This prompt is for the final Linux-side integration pass after both platform-specific tasks have run.

Repository rules:
1. Read `AGENTS.md` and follow it strictly.
2. We are in the Fontshow repo and inside the repository `.venv`.
3. Use `repoindex` before broad exploration.
4. Do not assume prior assistant conclusions are correct; read the actual resulting code and tests.

Execution goals:
1. Review the final code changes produced by:
   - Linux-native `#38`
   - WSL `#38`
   - native Windows `#51`
2. Verify the combined codebase still behaves correctly on Linux.
3. Identify any loose ends that must be resolved on Linux, such as:
   - architectural cleanup required by the final merged implementation
   - missing Linux-side tests for cross-platform guards
   - docs drift caused by the Windows work
   - CLI/help/schema references affected by the final combined behavior
4. Add only the minimal closing fixes needed to stabilize the integrated result.
5. Decide whether `#38` and `#51` are fully complete after this pass.

Expected work items:
- run focused reproduction for Linux-relevant behavior
- run deterministic tests
- add/update docs only where the final merged behavior is now different
- avoid reopening scope that belongs to unrelated issues

Important constraints:
- Do not redo the platform-specific implementation work unless integration proves it is necessary.
- Keep the pass narrow and integration-focused.
- If the Windows work introduced behavior that Linux cannot validate directly, document the residual limitation rather than guessing.

Expected output:
1. Minimal Linux-side closing patch, if needed.
2. Final test/doc integration updates, if needed.
3. Clear closure status for `#38` and `#51`.
