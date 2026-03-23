"""
Catalog domain data structures.

This module defines the core data types used internally by the catalog
subsystem during catalog generation.

Responsibilities
----------------
- Provide structured representations of fonts prepared for catalog
  rendering.
- Encapsulate normalized metadata derived from the inventory and
  enriched by catalog preprocessing steps.
- Serve as the shared data model used by catalog helpers such as
  labeling, sample selection, and document rendering.

Design principles
-----------------
Types defined here belong strictly to the catalog domain layer. They
should not depend on CLI orchestration code or pipeline modules. The
goal is to keep catalog logic decoupled from the create-catalog entry
point while allowing multiple catalog helpers to share a consistent
data representation.

Architectural role
------------------
This module sits between the inventory layer and the catalog rendering
helpers:

    inventory → catalog.types → catalog.* → pipeline (create_catalog)

The structures defined here are used throughout the catalog subsystem
but are not part of the inventory schema nor the LaTeX rendering
infrastructure.
"""

from typing import TypedDict


class _FontDetail(TypedDict):
    """
    Structured representation of a parsed font-detail record.

    Parameters
    ----------
    raw_line : str
        Original input line from which font details were parsed.
    extracted_names : list[str]
        Names extracted directly from the raw line before cleanup.
    base_names : list[str]
        Normalized base-name variants derived from the extracted names.

    Notes
    -----
    This typed dictionary captures the normalized outcome of parsing a
    raw font-detail line. It is used internally by the catalog domain to
    keep extracted names and their cleaned base-name variants together.
    """

    raw_line: str
    extracted_names: list[str]
    base_names: list[str]
