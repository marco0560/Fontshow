Continue work on Fontshow from the current repository state in the project root.

Context and ground rules:
- We are inside `.venv`.
- Follow repo style and existing patterns.
- Use `apply_patch` for file edits.
- Keep docstrings in repo NumPy-style format.
- Be careful with the dirty worktree: do not revert unrelated user changes.

Current verified state:
- `ruff check .` passes.
- `python -m mypy .` passes.
- `python -m pytest -q` passes with `368 passed`.
- Script inference is data-driven from ontology data.
- Multiple TeX-driven script/language expansion batches have already been promoted into production.
- Test-catalog rendering has been improved to show one family header with multiple file variants underneath.
- Catalog debug metadata currently renders human-readable `SCRIPT` and `LANGS`, and `OPTS` with comma-space separation.
- Template-side `.working`, `.broken`, and `.excluded` auxiliary logging has been reintegrated.

Important files to inspect first:
- `fontshow/catalog/document.py`
- `fontshow/ontology/language_tables.py`
- `fontshow/latex/templates.py`
- `fontshow/constants/catalog.py`
- `tests/test_catalog_document.py`
- `tests/test_infer_scripts.py`

Recent full-catalog artifacts:
- `fontshow_Linux_20260316_017.tex`
- `fontshow_Linux_20260316_016.log`
- `fontshow_Linux_20260316_015.log`

What was fixed recently:
- Removed the stale `Stage 0` section label.
- Put `[OK]` on the same line as `FILE  : <filename>`.
- Moved per-file existence checks from TeX into Python.
- Reworked the no-language/script-tagged render path to avoid fragile direct `\fontspec` usage.
- Fixed a bug in that path by switching from `\renewfontfamily` to `\newfontfamily`.
- Tightened suppression/preference rules for neighboring scripts such as Chakma, Syloti Nagri, and Tai Le.

What is still incomplete:
1. Re-run the full non-test catalog pipeline from the current state:
   - `fontshow parse-inventory -i aggressive`
   - `fontshow create-catalog`
   - `lualatex -interaction=nonstopmode <latest full tex>` twice
2. Confirm whether the last `\newfontfamily` fix in `fontshow/catalog/document.py` resolves the previously failing full compile.
3. If the full compile still fails, inspect the next concrete failing entry in the generated `.tex` and patch the generator with the smallest safe blast radius.
4. Once the full compile succeeds, inspect:
   - generated PDF
   - `.log`
   - `.working`
   - `.broken`
   - `.excluded`
5. After the full-catalog path is stable, resume the TeX-driven ontology expansion with the next 10-script batch.

Known failure history to keep in mind:
- A previous full-catalog compile failed around `Lohit-Gujarati.ttf` with `I can't find file 'Lohit-Gujarati.ttf.fontspec'`.
- Another failed due to doubled path handling when absolute paths and `Path=` were combined incorrectly.
- Another exposed that unknown-script fonts such as `Academicons` should stay on the simpler `Path + File` path.
- The most recent full-catalog issue before this restart prompt was the temporary-font branch using `\renewfontfamily` for a command that did not yet exist; this has now been corrected to `\newfontfamily`, but the full compile has not yet been rerun after that exact fix.

TeX/ontology expansion status:
- Several script batches have already been promoted, including the initial `BUGI`/`BUHD` additions and subsequent 10-script batches.
- Linux `DEFAULT_TEST_FONTS` has been extended to exercise many of those additions in `create-catalog --test`.
- The next content step, after stabilizing the full compile, is batch 7 of 10 more low-risk scripts from the local TeX surface.

Expected workflow for this session:
1. Verify the latest full compile outcome after the `\newfontfamily` fix.
2. Stabilize the full-inventory LaTeX path until two passes complete.
3. Inspect the resulting artifacts and identify any remaining systemic rendering issues.
4. Then resume the next 10-script batch from the local-TeX gap queue.
5. Update tests, run `ruff`, `mypy`, and `pytest`, and report the result.

Do not spend time redoing already-green global checks unless changes require it. Start from the full-catalog compile path first.
