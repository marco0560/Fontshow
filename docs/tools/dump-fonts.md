# dump_fonts

This module discovers installed fonts on the host system and extracts
raw, low-level metadata using fontTools and (optionally) FontConfig.

It produces the canonical *raw font inventory* consumed by the rest of
the Fontshow pipeline.

---

## Responsibilities

- Discover installed font files (Linux / Windows)
- Extract per-face metadata
- Handle TrueType Collections (TTC)
- Cache expensive fontTools operations
- Persist LuaLaTeX loadability metadata by default
- Serialize results to JSON

---

## Loadability Persistence

`dump-fonts` now performs **LuaLaTeX loadability probing by default**
and persists the results in the generated inventory.

Behavior:

- candidate fonts are probed in deterministic serial batches
- per-font results are stored under `loadability.lualatex`
- inventory-level runtime metadata is stored under
  `metadata.validation.lualatex`
- the runtime fingerprint allows downstream stages to detect stale
  persisted results

To disable probing explicitly:

<!-- cheatsheet:start -->
```bash
python -m fontshow.cli.dump_fonts --no-loadability
```
<!-- cheatsheet:end -->

When `--no-loadability` is used:

- no LuaLaTeX probing is performed
- `metadata.validation.lualatex.attempted` remains false
- per-font loadability fields remain in their non-attempted state

---

### --include-fc-charset

When enabled, this option instructs Fontshow to query Fontconfig for
declared Unicode charset information and include it in the generated
inventory.

<!-- cheatsheet:start -->
```bash
python -m fontshow.cli.dump_fonts --include-fc-charset
```
<!-- cheatsheet:end -->

The resulting data is stored in the optional `charset` field of each
font entry.

Fontconfig charset extraction is best-effort and depends on the
availability and behavior of fc-query on the host system.
On some distributions, fc-query cannot reliably be used to inspect
individual font faces, resulting in empty charset data.

---

## Scope and non-responsibilities

The `dump-fonts` stage is responsible for **discovering fonts** and
**extracting raw metadata** from the system.

It is intentionally limited to data collection and does **not** perform:

- semantic validation
- language normalization
- charset interpretation
- inventory consistency checks
- catalog generation

In particular:

- No assumptions are made about the correctness of extracted metadata
- No normalization or enrichment is applied
- No validation errors are raised at this stage

The persisted LuaLaTeX loadability state is an exception to the
"metadata only" baseline: it is an optional deterministic runtime
assessment stored directly in the raw inventory so later stages can
reuse it instead of recomputing it.

All semantic interpretation and validation are delegated to the
inventory parsing stage.

This separation ensures that:

- font discovery remains environment-specific
- metadata extraction stays lossless
- higher-level logic remains centralized and testable

## API reference

::: fontshow.cli.dump_fonts
