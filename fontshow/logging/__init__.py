"""
Logging subsystem package.

This package contains modules responsible for structured logging
within the Fontshow codebase.

Responsibilities
----------------
- Provide logging infrastructure used across the pipeline.
- Support structured and category-based TRACE logging.
- Expose helpers used by CLI and pipeline modules for diagnostics.s

Design principles
-----------------
Logging functionality is centralized to ensure consistent formatting
and behavior across all subsystems. Modules in this package must remain
safe to import from any layer of the architecture.

Architectural role
------------------
This package belongs to the **core infrastructure layer** and provides
logging utilities used by inventory processing, catalog generation,
and CLI commands.
"""
