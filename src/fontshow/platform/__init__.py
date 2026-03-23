"""
Platform subsystem package.

This package contains modules responsible for interacting with the
runtime environment and platform-specific facilities.

Responsibilities
----------------
- Detect runtime platform characteristics.
- Discover installed font files on supported systems.
- Integrate with platform tools such as Fontconfig.
- Provide platform metadata used during inventory generation.

Design principles
-----------------
Platform-specific logic is isolated within this subsystem so that the
rest of the Fontshow pipeline can operate on normalized data structures
without depending on operating-system details.

Architectural role
------------------
This package belongs to the **platform subsystem** and implements the
environment integration layer used by inventory generation workflows.
"""
