"""
Core infrastructure package.

This package contains the low-level shared infrastructure used across
the Fontshow codebase.

Responsibilities
----------------
- Provide foundational helpers shared by multiple subsystems.
- Host cross-cutting infrastructure such as logging, CLI support,
  JSON-boundary helpers, warnings, and shared type definitions.
- Remain the stable import surface for utilities that must not depend
  on higher-level inventory, catalog, or platform orchestration.

Design principles
-----------------
Modules in this package must stay lightweight, broadly reusable, and
free from domain-specific business logic. They exist to support
higher-level packages without introducing circular dependencies or
stage-specific assumptions.

Architectural role
------------------
This package belongs to the **core infrastructure layer** and provides
the cross-cutting primitives consumed by the CLI, inventory, catalog,
platform, and preflight subsystems.
"""
