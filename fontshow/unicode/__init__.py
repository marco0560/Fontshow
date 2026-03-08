"""
Unicode utilities package.

This package contains modules related to Unicode processing used by the
Fontshow pipeline.

Responsibilities
----------------
- Provide utilities for handling Unicode charset data.
- Support decoding and normalization of character set information.
- Provide helpers used by inventory analysis and script coverage logic.

Design principles
-----------------
Unicode processing utilities are isolated in this package so that
inventory and analysis modules can operate on normalized Unicode data
without reimplementing low-level handling logic.

Architectural role
------------------
This package belongs to the **Unicode processing subsystem** and
supports inventory metadata analysis.
"""
