"""
OpenType specification constants.

This module defines numeric identifiers and fixed values derived from
the OpenType specification.

Responsibilities
----------------
- Provide constants representing OpenType ``name`` table identifiers.
- Centralize specification-derived values used during font metadata
  extraction.
- Serve as the canonical reference for OpenType numeric identifiers
  used by Fontshow.

Design principles
-----------------
Constants mirror the OpenType specification and must not be modified.
This module contains no runtime logic and is safe to import from any
layer of the architecture.

Architectural role
------------------
This module belongs to the **constants infrastructure layer** and
provides specification-derived identifiers used by the inventory and
metadata extraction subsystems.

Notes
-----
The numeric values defined here are copied from the OpenType
specification and are treated as stable external identifiers.

Typical usage
-------------
These constants are typically used when reading or interpreting OpenType
tables via FontTools, for example when extracting entries from the ``name``
table.

Example
-------
    from fontshow.constants.opentype import NAME_ID_FAMILY

    family_name = name_table.getName(NAME_ID_FAMILY, platformID, platEncID)

References
----------
OpenType Specification:
https://learn.microsoft.com/en-us/typography/opentype/spec/name
"""

# -----------------------
# fontTools extraction
# -----------------------
NAME_ID_FAMILY = 1
NAME_ID_SUBFAMILY = 2
NAME_ID_FULLNAME = 4
NAME_ID_POSTSCRIPT = 6
NAME_ID_VERSION = 5
NAME_ID_LICENSE = 13
NAME_ID_LICENSE_URL = 14
NAME_ID_SAMPLE_TEXT = 19
