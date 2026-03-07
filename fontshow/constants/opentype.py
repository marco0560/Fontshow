"""
Fontshow – constants.opentype
=============================

OpenType specification constants used by Fontshow.

This module centralizes numeric identifiers and fixed values defined by the
OpenType specification, primarily those related to the ``name`` table and
other standardized font metadata structures.

The purpose of this module is to avoid scattering OpenType identifiers across
the codebase and to ensure that all specification-derived constants are
defined in a single canonical location.

Design principles
-----------------
• Values mirror the OpenType specification and must not be modified.
• No runtime logic or functions are defined here.
• Safe to import from any layer of the architecture.
• Acts as the authoritative reference for OpenType numeric identifiers.

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
