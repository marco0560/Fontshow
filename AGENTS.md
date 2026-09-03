# AGENTS.md — Fontshow

## Repository map

| Path | Purpose |
| --- | --- |
| `src/fontshow/` | Main application code |
| `tests/` | Authoritative behavioral specification |
| `docs/` | Architecture, contracts, and decisions |
| `scripts/` | Development, release, audit, and generation tooling |
| `devtools/` | Codex prompts and auxiliary workflows |
| `.github/` | CI/CD pipelines |
| `_archive/` | Historical, inactive artifacts |

Use the repository's Codira index to scope the following areas:

| Area | Path | Responsibility |
| --- | --- | --- |
| Entry point | `__main__.py` | CLI entry |
| CLI | `cli/` | Command implementations |
| Catalog | `catalog/` | LaTeX document generation |
| Inventory | `inventory/` | Font metadata extraction and validation |
| Platform | `platform/` | OS and font discovery |
| Preflight | `preflight/` | Runtime and external-tool readiness |
| LaTeX | `latex/` | Escaping, templates, rendering policies |
| Ontology | `ontology/` | Language, script, and Unicode reference data |
| Schema | `schema/` | JSON schema definitions |
| Core | `core/` | Shared utilities, logging, JSON, and types |

## Architecture

Preserve the pipeline boundaries:

| Layer | Responsibility |
| --- | --- |
| CLI | Arguments, orchestration, exit codes |
| Preflight | Runtime and external-tool readiness |
| Platform | OS and Fontconfig integration |
| Inventory | Raw font-data validation, normalization, enrichment |
| Catalog | Catalog records, grouping, specimen selection |
| LaTeX | TeX escaping, templates, rendering policies |
| Ontology | Static language, script, Unicode reference data |
| Core | Shared utilities, logging, JSON, types |

- Keep environment-dependent behavior in `platform/`, `preflight/`, or an
  explicitly documented pipeline stage.
- Catalog rendering must not rediscover fonts or reinterpret raw platform state.
- Keep argument parsing and exit policy out of lower-level domain modules.
- Do not duplicate ontology, schema, or constant data across subsystems.
- Generated files are owned by their generator: modify the generator and
  regenerate the output.

## Validation

```bash
uv run python scripts/validate_repo.py
```
