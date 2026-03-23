"""
Catalog domain package.

This package contains the helpers used by the Fontshow catalog
generation pipeline.

Responsibilities
----------------
- Provide metadata extraction helpers used during catalog generation.
- Provide labeling utilities for scripts, languages, and font classes.
- Provide sample-selection logic for specimen rendering.
- Provide document assembly helpers that produce the final LaTeX output.

Design principles
-----------------
The catalog package is responsible for transforming normalized inventory
metadata into catalog-ready structures. Rendering primitives remain in
the `fontshow.latex` subsystem, while inventory analysis lives in the
`fontshow.inventory` domain.

Architectural role
------------------
This package belongs to the **catalog domain layer** and implements the
stage that converts analyzed inventory data into the structures used to
render the final catalog document.
"""
