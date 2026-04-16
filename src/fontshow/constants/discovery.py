"""
Font discovery constants.

This module defines shared constants used by the font discovery
subsystem.

Responsibilities
----------------
- Centralize file-extension policy applied during font discovery.
- Provide import-safe constants shared by discovery backends.

Design principles
-----------------
Discovery policy constants must live outside the platform scanning
module so that the filtering policy is defined in one authoritative
location and can be reused without duplicating extension lists.

Architectural role
------------------
This module belongs to the **constants infrastructure layer** and
provides discovery-specific values used by the platform subsystem.
"""

DISCOVERABLE_FONT_EXTENSIONS = {".otc", ".otf", ".ttc", ".ttf", ".woff", ".woff2"}
LEGACY_FONT_EXTENSIONS = {".pfb", ".pfa", ".t1", ".pcf", ".pcf.gz", ".bdf"}
