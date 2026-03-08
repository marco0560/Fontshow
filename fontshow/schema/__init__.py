"""
Schema package.

This package contains the JSON schema definitions used by Fontshow to
validate inventory files.

Responsibilities
----------------
- Provide the canonical JSON schema for the Fontshow inventory format.
- Support structural validation of inventory documents.

Design principles
-----------------
Schema definitions are static artifacts representing the authoritative
structure of Fontshow inventory files. They are consumed by validation
modules but contain no executable logic.

Architectural role
------------------
This package belongs to the **schema subsystem** and provides the
structural specification used by inventory validation.
"""
