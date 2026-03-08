"""
Shared utility package for cross-stage helpers.

Responsibilities
----------------
- Provide reusable helpers that are independent of a specific pipeline stage.
- Offer utilities that can be safely used by multiple subsystems
  (catalog generation, inventory processing, and CLI tools).

Design principles
-----------------
Modules in this package must remain lightweight and free from
dependencies on high-level pipeline orchestration logic. They provide
small reusable utilities that operate on already normalized data.

Architectural role
------------------
This package belongs to the **shared utilities layer** and hosts helpers
that are used across multiple Fontshow subsystems.
"""
