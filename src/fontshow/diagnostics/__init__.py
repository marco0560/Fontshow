"""
Diagnostics utilities package.

This package contains helpers used to generate diagnostic messages
during inventory parsing and validation.

Responsibilities
----------------
- Provide utilities for formatting inventory-related diagnostics.
- Support the emission of warnings and informational messages during
  parsing and validation stages.

Design principles
-----------------
Diagnostics helpers are pure utilities that do not perform orchestration
or CLI command handling. They operate on normalized inventory data and
produce deterministic diagnostic messages.

Architectural role
------------------
This package belongs to the **diagnostics subsystem** and supports the
inventory parsing and validation workflows.
"""
