"""
Fontshow CLI command package.

This package contains the command implementations that form the
Fontshow command-line interface.

Responsibilities
----------------
- Provide CLI entry points for the Fontshow workflow.
- Implement command handlers for inventory generation, parsing,
  validation, and catalog creation.
- Expose command modules used by the main CLI dispatcher.

Design principles
-----------------
Each command module encapsulates a single stage of the Fontshow
pipeline. CLI modules focus on argument handling and orchestration,
while domain logic resides in the corresponding subsystems
(`inventory`, `catalog`, `platform`, etc.).

Architectural role
------------------
This package belongs to the **CLI interface layer** and implements
the command modules invoked by the Fontshow CLI dispatcher.
"""
