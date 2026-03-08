"""
Font discovery subsystem.

This package contains helpers responsible for discovering fonts on the
host system and collecting metadata required to build the initial
Fontshow inventory.

Responsibilities
----------------
- Provide platform-specific mechanisms for locating installed fonts.
- Support discovery backends such as Fontconfig.
- Supply metadata needed for inventory generation.

Design principles
-----------------
Discovery modules interact with platform tools but must not perform
semantic interpretation of fonts. Their role is limited to locating
fonts and extracting raw metadata for later pipeline stages.

Architectural role
------------------
This package belongs to the **font discovery subsystem** and supports
the inventory generation stage implemented by the `dump-fonts` CLI
command.
"""
