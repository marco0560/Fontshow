# Changelog summary

This page provides a **decision-oriented** summary of recent changes.

For the authoritative, commit-level history, refer to:

- GitHub Releases
- `CHANGELOG.md` (semantic-release output)
- Git tags

---

## Recent highlights

### Unified CLI dispatcher

- `fontshow <command>` is the authoritative entrypoint
- Consistent execution contract across commands (`main(args) -> int`)
- Exit code contract documented and tested

See: `decisions.md` for rationale and constraints.

### Charset-driven enrichment (C-step 5.1–5.3)

- Deterministic normalization of FontConfig charset ranges
- Unicode block coverage derived from charset
- Script coverage ratios derived from Unicode blocks

See: schema and data dictionary for field definitions.
