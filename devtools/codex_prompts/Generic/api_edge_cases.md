Analyze the repository for edge cases and failure paths in Python APIs.

Goal
----

Identify situations where functions or public APIs may fail or behave
incorrectly under unusual or boundary conditions.

Focus Areas
-----------

fontshow/
scripts/
tests/

Do NOT modify code.
Report findings and suggested tests only.

Checks to Perform
-----------------

1. Parameter Boundary Conditions

Detect functions where parameters may have boundary issues:

- numeric ranges (0, negative, very large values)
- empty collections
- single-element collections
- extremely large collections
- None values where not expected

Flag functions where these cases are not explicitly handled.


2. Type Robustness

Identify functions that assume specific types without validation.

Examples:
- arithmetic on possibly None values
- indexing without checking sequence length
- string operations on non-strings

Flag potential TypeError or AttributeError paths.


3. Silent Failure Paths

Detect code patterns such as:

- bare `except:` blocks
- exceptions swallowed without logging
- functions returning None on failure without documentation

Report these as possible hidden error conditions.


4. Exception Documentation Mismatch

For functions with docstrings containing a `Raises` section:

- verify that the function actually raises those exceptions
- detect exceptions raised but undocumented


5. Resource Edge Cases

Detect operations involving:

- file I/O
- subprocess execution
- external commands
- temporary directories

Verify that failure conditions are handled:

- file not found
- permission errors
- subprocess non-zero exit


6. Iteration and Empty Input

Detect algorithms assuming non-empty inputs.

Examples:

- `max()`, `min()` on possibly empty sequences
- indexing `[0]`
- division by `len(x)`


7. State-Dependent Logic

Detect functions whose behavior depends on:

- environment variables
- filesystem state
- installed fonts or external tools

Flag cases where missing dependencies may cause runtime errors.


8. Test Coverage of Edge Cases

For each flagged function:

- check if tests exist
- check if boundary conditions are tested
- identify missing tests


Output Format
-------------

Group findings into sections:

1. boundary-condition risks
2. type robustness issues
3. silent exception handling
4. undocumented exceptions
5. filesystem / subprocess risks
6. empty-input vulnerabilities
7. missing edge-case tests

For each finding include:

- file path
- function name
- explanation of the edge case
- suggested pytest test


Constraints
-----------

- Do not invent repository structure.
- Do not propose refactoring.
- Focus only on edge cases that may cause incorrect behavior.
