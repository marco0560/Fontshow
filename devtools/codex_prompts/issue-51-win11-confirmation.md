Perform native Windows 11 confirmation-only validation for GitHub issue `#51` after the issue has already been closed on `main`.

Issue scope:
- `#51` is `Windows font identity resolution missing: catalog generation lacks loadable font references`.
- This prompt is for a later confirmation pass on native Windows 11.
- This prompt does not reopen implementation scope unless confirmation proves a regression.

Repository rules:
1. Read `AGENTS.md` and follow it strictly.
2. We are in the Fontshow repo and inside the repository `.venv`.
3. Use `repoindex` before broad exploration.
4. Ground every claim in the current repository state at the time of execution.

Confirmation-only preconditions:
1. Confirm you are running on native Windows 11, not WSL.
2. Review the current `main` tree only. Do not reconstruct prior assistant conclusions.
3. Treat issue `#51` as already closed unless this session finds a concrete regression.

Execution goals on native Windows 11:
1. Re-read the current Windows discovery and identity-resolution implementation.
2. Reproduce the current end-to-end behavior with:
   - `preflight`
   - `dump-fonts`
   - `parse-inventory`
   - `create-catalog`
3. Confirm that catalog generation now has loadable font references for native Windows inventories.
4. Confirm that current Windows-specific behavior does not require undocumented Linux-only assumptions.
5. Record any residual limitation that still cannot be confirmed from this session without guessing.

Focus areas:
- discovered Windows font paths
- identity data propagated into inventories
- catalog rendering decisions for fonts without Linux-style file/fontconfig identity
- platform-gated behavior that differs between Linux and native Windows

Expected output of this task:
1. A confirmation report stating whether the closed `#51` behavior still holds on native Windows 11.
2. Explicit notes for any observed discrepancy or regression.
3. Minimal follow-up patch only if current `main` is demonstrably wrong.

Important constraints:
- Do not treat WSL as sufficient evidence.
- Do not broaden into unrelated platform work.
- Do not invent missing runtime evidence.
- If no regression is found, make no behavioral change.
