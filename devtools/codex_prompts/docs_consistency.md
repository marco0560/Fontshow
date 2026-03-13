Audit documentation consistency between code and docs/.

Tasks:

1. Enumerate all CLI entrypoints defined in the repository
   (argparse, click, console_scripts, or __main__ modules).

2. Enumerate modules that can be executed via:
   python -m fontshow.*

3. Extract all command references from docs/:
   - python -m ...
   - fontshow ...
   - script invocations

4. Identify mismatches:
   - commands documented but not implemented
   - commands implemented but undocumented
   - renamed modules still referenced in docs

5. Produce patches only for files in docs/.

Constraints:
- Do not modify code.
- Do not invent commands.
- If unsure about a command, flag it instead of changing docs.

Output unified diffs only.
