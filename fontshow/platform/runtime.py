"""
Platform runtime detection helpers.

This module provides small utilities and constants that describe the
current execution platform. These values are computed at import time and
used by various subsystems to adapt behaviour when platform-specific
differences matter (for example filesystem handling or LaTeX invocation).

Responsibilities
----------------
- Detect the current operating system.
- Provide simple boolean flags for common platform checks.
- Centralize runtime platform knowledge so other modules do not perform
  ad-hoc platform detection.

Design principles
-----------------
Platform detection must live in a dedicated infrastructure module so
that domain and rendering modules (catalog, inventory, latex, etc.)
never depend on pipeline scripts or CLI entrypoints. This keeps the
dependency graph clean and prevents circular imports.

Architectural role
------------------
This module belongs to the **platform infrastructure layer** and may be
imported by any other module in the project that requires knowledge of
the runtime environment.
"""

import sys

if sys.platform == "win32":
    # modulo specifico Windows
    IS_WINDOWS = True
    IS_LINUX = False
elif sys.platform.startswith("linux"):
    IS_LINUX = True
    IS_WINDOWS = False
    # eventuale alternativa per altri OS
else:
    IS_WINDOWS = False
    IS_LINUX = False
