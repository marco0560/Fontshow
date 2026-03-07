"""
Runtime constants.

This module contains constants whose values are determined at runtime
and may be shared across multiple subsystems of the application.

Responsibilities
----------------
- Provide timestamp strings or build identifiers used in generated
  filenames or reports.
- Centralize runtime-derived constants so they are defined once and
  imported consistently across modules.

Design principles
-----------------
Runtime constants must not live in pipeline modules (such as
create_catalog.py) to avoid circular dependencies and duplication.
They are kept in the constants infrastructure layer so that any
subsystem—catalog, inventory, LaTeX rendering, or CLI—can import them
without creating cross-layer dependencies.

Architectural role
------------------
This module belongs to the **constants infrastructure layer** and
provides shared runtime values used throughout the application.
"""

from datetime import datetime

DATE_STR = datetime.now().strftime("%Y%m%d")

# ------------------------------------------------------------------
# Subprocess safety limits (Phase 6.4)
# ------------------------------------------------------------------

# Maximum time allowed for external fontconfig calls.
# Chosen to be safely above normal execution time while preventing hangs.
SUBPROCESS_TIMEOUT_SECONDS = 30
