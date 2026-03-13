Repository: Fontshow

Goal
Normalize and complete docstrings across the repository.

Scope
Work only inside the Python package:

fontshow/

Skip these directories entirely:
tests/
scripts/
.githooks/
docs/

Docstring policy

1. Preserve all existing information.
   - Never delete or shorten existing explanatory text.
   - Never compress architectural descriptions.

2. Only improve structure and completeness.

3. Add missing docstrings for:
   - modules
   - classes
   - functions
   - async functions
   - nested functions

4. Use NumPy-style sections when appropriate:

Parameters (None if empty)
Returns (None if empty)
Raises if appropriate
Notes for non obvious behaviour

5. If a function may raise exceptions directly or indirectly,
   document them in a Raises section.

6. If a docstring already exists:
   - preserve its content
   - reorganize it if necessary
   - add missing sections
   - do not remove sections such as
     Responsibilities
     Design principles
     Architectural role
     Notes

7. Module docstrings are especially important:
   - preserve architectural explanations
   - preserve domain boundaries
   - never reduce them to short summaries.

Hard constraints

- Modify docstrings only.
- Do not modify executable code.
- Do not change function signatures.
- Do not reorder imports.
- Do not reformat unrelated lines.
- Do not modify files outside the allowed scope.

Workflow

1. Inspect the repository.
2. Propose a patch for a SMALL batch of files (3–5 files max).
3. Show the patch before applying it.
4. Wait for approval.

Specifically, a local script pointed to the following files/functions
as worthy of attention, as they may be not satisfactorily docstring'ed
