# Development Scripts

This document describes the purpose and status of the scripts contained in the
`scripts/` directory.

Scripts in this directory are intended for **development, maintenance, and
project tooling**. They are **not part of the Fontshow public API** and are not
covered by compatibility or stability guarantees.

They may change or be removed without notice.

---

## clean_repo.py

### Purpose

Utility script used during development to clean the repository workspace.

Typical use cases include:

- removing temporary or generated files,
- resetting local artifacts created during development or testing,
- preparing the repository for a clean run or release check.

### Status

Development-only utility.
Not used by the core pipeline or CLI.

---

## generate_cheatsheet.py

### Generation Purpose

Generates developer-facing cheat sheets from documentation sources.

This script is typically used to:

- consolidate reference information,
- produce printable or distributable cheat sheets,
- assist maintainers during documentation updates.

### Generation Status

Documentation tooling.
Not required for normal Fontshow operation.

---

## set_version.py (removed)

### Purpose (historical)

Previously used to manually update version information during development.

### Current status

This script has been removed.

Fontshow versioning is now fully managed via:

- semantic-release,
- Git tags,
- automated CI workflows.

Manual version manipulation is no longer supported or required.
