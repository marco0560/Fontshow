"""
Fontshow constants package.

This package groups constant definitions used throughout the Fontshow
codebase.

Responsibilities
----------------
- Provide centralized definitions of static configuration values.
- Expose OpenType specification identifiers used during font metadata
  extraction.
- Provide runtime constants shared across multiple subsystems.

Design principles
-----------------
Constants must be defined in a single authoritative location to avoid
duplication and inconsistencies. Modules in this package must not
contain business logic and should remain safe to import from any layer
of the architecture.

Architectural role
------------------
This package belongs to the **constants infrastructure layer** and
provides shared constant values used by the catalog, inventory,
platform, and CLI subsystems.
"""
