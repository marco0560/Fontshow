"""
Global constants used across the Fontshow project.

This module defines versioned and project-wide constants that must remain
stable and centrally maintained to guarantee deterministic behavior across
all pipeline stages.

Constants
---------
SCHEMA_VERSION : str
    Current Fontshow JSON inventory schema version. This value is used by
    producers and consumers of the inventory to ensure compatibility and
    validation correctness.
"""

SCHEMA_VERSION = "1.2"
