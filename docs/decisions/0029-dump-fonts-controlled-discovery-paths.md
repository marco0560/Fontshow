# ADR 0029: dump-fonts controlled discovery paths

- Status: Accepted
- Date: 2026-04-16

## Context

`dump-fonts` normally discovers fonts through the platform discovery
backend. That is appropriate for inventory generation on a configured
host, but it makes performance measurement inputs dependent on the
machine's installed font set.

Bundling benchmark font datasets in the repository would create size and
licensing risk. Users instead need a deterministic way to point
`dump-fonts` at local, externally managed font directories.

## Decision

`dump-fonts` supports controlled discovery through:

```bash
fontshow dump-fonts --paths /path/to/fonts-a /path/to/fonts-b
```

When `--paths` is present:

- only the provided directories are scanned
- platform system discovery is not used as a fallback
- missing paths and non-directory paths fail the command
- discovered font paths are resolved, deduplicated, and sorted
- legacy font extension skip accounting remains active

When `--paths` is absent, the existing system discovery behavior remains
unchanged.

## Consequences

Positive:

- Benchmark inputs can be reproduced without storing fonts in the
  repository.
- Users can compare pipeline performance against the same local dataset.
- Invalid benchmark roots fail visibly instead of silently falling back
  to system fonts.

Costs:

- The CLI exposes another discovery mode that must remain covered by
  tests.
- Users remain responsible for managing benchmark font datasets outside
  the repository.

Guardrails:

- No CI job depends on external font datasets.
- No performance assertions are introduced.
- The default `dump-fonts` path continues to use system discovery.
