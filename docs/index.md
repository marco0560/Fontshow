# Fontshow Documentation

## Getting started

- [Getting started](getting_started.md)
- [CLI overview](cli.md)
- [Bash completion](bash-completion.md)
- [Cheatsheet](cheatsheet.md)
- [Commands](tools/preflight.md)

### Command documentation

Each command in the Fontshow pipeline has a dedicated documentation page
describing its behavior, inputs, outputs, and validation rules.

The authoritative command documentation is located under:

- Preflight checks
  → `tools/preflight.md`

- Font inspection and metadata extraction
  → `tools/dump-fonts.md`

- Inventory parsing and validation
  → `tools/parse-inventory.md`

- Inventory validation
  → `tools/validate-inventory.md`

- Catalog generation
  → `tools/create-catalog.md`

These documents describe *how each stage behaves*, while the pipeline
documentation describes *how the stages relate to each other*.

## Data model

- [Data dictionary](data_dictionary.md)
- [Schema overview](schema/index.md)
- [Inventory schema v1.5](schema/inventory_v1_5.md)
- [Language normalization](schema/language-normalization.md)

## Development and maintenance

- [Repository architecture](architecture.md)
- [Codebase map](codebase-map.md)
- [Development environment](dev-environment.md)
- [Development scripts](scripts.md)
- [Logging system](logging.md)
- [Contributing guidelines](CONTRIBUTING.md)
- [CLI Contract](cli-contract.md)

The architecture document explains the main structural boundaries of the
project. The codebase map complements it with a developer-oriented guide
to package responsibilities, data flow, change points, and bug triage
entrypoints.

## Engineering Notes (internal)

These notes are not part of the public API or user documentation, but serve as long-term project
memory for maintainers.

- [Lessons Learned](engineering/lessons-learned.md)
- [Codex evaluation](engineering/codex-evaluation-04-02-2026.md)
- [Exceptions policy](engineering/exception_policy.md)
- [Release system](engineering/release-system.md)
- [TRACE logging guide](engineering/TRACE-logging-developper-guide.md)

## Project planning and governance

Fontshow development is guided by a canonical, version-controlled
planning and governance document set, maintained directly in the repository.

The planning set defines:

- development phases and milestones
- issue and atomic action models
- testing and stabilization strategy
- governance and evolution guidelines

- [Planning document set overview](planning/00_Planning_Document_Set.md)
- [Issue 66 persisted loadability implementation plan](planning/13_ISSUE_66_PERSISTED_LOADABILITY_IMPLEMENTATION_PLAN.md)

Formal architectural and project decisions are tracked as individual,
immutable records to preserve rationale and historical context.

- [Decisions index](decisions/index.md)

## Security & Release

- [Security and Release Policy](security-and-release-policy.md)
- [Key Rotation](key-rotation.md)

## Data Schema

- [Schema](schema/index.md)
- [Data Dictionary](data_dictionary.md)

## Release Process

- [Release Checklist](release/checklist.md)
