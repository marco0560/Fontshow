Audit the repository for architectural and documentation invariants.

Goal
----

Detect inconsistencies between code, CLI surface, tests, and documentation.

Do NOT modify code.
Report findings only.

Repository Areas
----------------

- fontshow/
- tests/
- scripts/
- docs/

Checks to Perform
-----------------

1. CLI Surface Consistency

   Identify all CLI entrypoints:
   - modules executable via `python -m fontshow.*`
   - argparse-based commands
   - console_scripts or CLI wrappers

   Verify:

   - every CLI command is documented in docs/
   - docs do not reference non-existing commands
   - deprecated commands are not still documented


2. Module Reachability

   Identify modules under fontshow/ that:

   - are never imported
   - are not used by CLI
   - are not referenced by tests

   Flag them as possible dead modules.


3. Public API Consistency

   Detect functions or classes that:

   - appear to be public
   - but are never used outside their module.

   Flag possible internalization (leading underscore).


4. Test Coverage Gaps

   For modules under fontshow/:

   - identify modules with no tests
   - identify functions that appear untested

   Suggest where tests should exist.


5. Documentation Drift

   Extract references in docs/ such as:

   - `python -m fontshow.*`
   - `fontshow <command>`

   Verify those commands exist.


6. Scripts vs Package Logic

   For scripts under scripts/:

   - detect duplicated logic also present in fontshow/
   - suggest refactoring into shared functions.


Output Format
-------------

Report grouped sections:

- CLI inconsistencies
- undocumented commands
- possible dead modules
- untested modules
- documentation drift
- refactoring opportunities

Constraints
-----------

- Do not invent repository structure.
- Do not modify files.
- Do not suggest stylistic changes.
- Focus only on structural inconsistencies.
