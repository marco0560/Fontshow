Generate pytest tests covering edge cases in the repository.

Goal
----

Improve robustness by testing boundary conditions and error paths.

Scope
-----

fontshow/
tests/

Do NOT modify production code unless absolutely required.

Edge Cases to Cover
-------------------

1. Boundary values

Detect functions that may fail on:

- empty lists
- empty dictionaries
- empty strings
- single-element collections
- zero values
- negative values
- very large values

Generate tests verifying correct behavior.


2. None handling

Detect functions where parameters may be None.

Generate tests verifying either:

- correct handling
- expected exception.


3. Exception paths

Detect code paths that raise exceptions.

Generate tests verifying:

- the exception is raised
- the exception type matches documentation.


4. Filesystem edge cases

For functions interacting with files:

Generate tests covering:

- missing file
- empty file
- malformed input
- permission error (if testable)


5. Subprocess failures

If subprocess calls exist:

Generate tests simulating:

- command not found
- non-zero exit code


6. Algorithm edge cases

Detect patterns such as:

- max() or min() on empty collections
- division by length
- indexing [0]

Generate tests verifying safe behavior.


Test Constraints
----------------

Tests must be:

- deterministic
- independent
- runnable with pytest
- using tmp_path where filesystem is required
- not dependent on system fonts or external programs unless mocked

Prefer mocking external dependencies.


Output
------

Produce unified diff patches adding tests under:

tests/


Test Style
----------

Use pytest style consistent with the repository.

Example structure:

def test_function_edge_case(tmp_path):
    ...


Output format:

Unified diffs only.
No explanations.
