"""
Inventory subsystem package.

This package contains the modules responsible for constructing,
enriching, validating, and manipulating Fontshow inventory data.

Responsibilities
----------------
- Define the normalized inventory data model.
- Extract and normalize font metadata.
- Perform metadata enrichment such as script and language inference.
- Validate inventory structures and semantic consistency.

Design principles
-----------------
The inventory subsystem transforms raw font metadata into the
normalized inventory structures used throughout the Fontshow pipeline.
Modules in this package operate on in-memory data structures and avoid
CLI orchestration or rendering logic.

Architectural role
------------------
This package belongs to the **inventory subsystem** and implements the
core pipeline stages that build and validate Fontshow inventory data.
"""
