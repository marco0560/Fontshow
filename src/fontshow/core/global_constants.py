"""
Global project constants.

This module defines versioned constants shared across the Fontshow
pipeline.

Responsibilities
----------------
- Define the canonical inventory schema version.
- Provide project-wide constants used across multiple subsystems.

Design principles
-----------------
Constants that influence cross-module behavior must be defined in a
single authoritative location to ensure deterministic behavior across
pipeline stages.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and exposes
global constants used by inventory processing, validation, and CLI
modules.

Notes
-----
The constants defined here are intentionally minimal and versioned so
schema-sensitive pipeline stages share a single authoritative source.
"""

SCHEMA_VERSION = "1.4"
