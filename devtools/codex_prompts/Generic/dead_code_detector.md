Analyze the repository for structural inconsistencies and dead code.

Goal
----

Detect unused code, unreachable logic, accidental public APIs,
and architectural drift.

Do NOT modify code.

Report findings only.

Scope
-----

fontshow/
scripts/
tests/
docs/


Checks
------

1. Unused modules

Identify modules under fontshow/ that:

- are never imported
- are not executed as CLI modules
- are not referenced in tests

Flag them as potential dead modules.


2. Unused functions

Detect functions or classes that:

- are defined
- but never called or imported outside their module.

Ignore:

- test fixtures
- private helpers clearly scoped internally.


3. Accidental public API

Identify functions or classes that:

- do not start with "_"
- but appear to be internal
- and are not used externally.

These may need a leading underscore.


4. Unreachable branches

Detect branches such as:

- code after return
- conditions always true/false
- exception handlers that can never trigger.

Report suspicious constructs.


5. Duplicate logic

Detect functions across different modules that implement
very similar logic.

Suggest possible consolidation.


6. CLI drift

Identify commands that exist in the code but are not documented.

Identify documented commands that no longer exist.


7. Scripts vs package logic

For files under scripts/:

detect logic duplicated inside fontshow/.

Suggest moving shared logic into package modules.


8. Tests referencing obsolete APIs

Detect tests that reference:

- deprecated modules
- removed functions
- outdated CLI usage.


Output
------

Group results into sections:

- unused modules
- unused functions
- accidental public API
- unreachable branches
- duplicated logic
- CLI drift
- test inconsistencies


For each finding include:

- file path
- symbol name
- explanation of the issue


Constraints
-----------

- Do not invent repository structure.
- Do not propose stylistic refactors.
- Focus only on structural issues that may indicate dead code
  or architectural drift.
