"""
Fontshow test suite package.

This package groups the automated test modules validating the behavior
of the Fontshow command-line interface, pipeline components, and
supporting infrastructure.

Responsibilities
----------------
- Provide regression and behavioral tests for CLI commands.
- Verify deterministic behavior of pipeline stages.
- Ensure internal contracts and invariants remain valid.

Design principles
-----------------
Tests must remain deterministic, isolated, and independent from
system-specific font installations whenever possible. Fixtures and
stubs are used to ensure reproducible behavior across environments.

Architectural role
------------------
This package belongs to the **test infrastructure layer** and provides
verification coverage for the Fontshow runtime and developer tooling.

Important Note
--------------
This file is needed to allow the imports from tests/helpers.
"""
