"""
JSON support package.

This package is reserved for helpers related to JSON-facing concerns in
Fontshow.

Responsibilities
----------------
- Provide a namespace for JSON-specific utilities when such helpers are
  split out from other subsystems.
- Keep JSON-boundary concerns isolated from domain logic when dedicated
  modules are introduced.

Design principles
-----------------
The package should remain lightweight and focused on JSON-facing
infrastructure rather than inventory, catalog, or CLI orchestration
logic. It currently serves primarily as package scaffolding.

Architectural role
------------------
This package belongs to the **core JSON/support layer** and exists as a
dedicated namespace for JSON-related helpers.
"""
