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
- Serialize results to JSON

---

### --include-fc-charset

When enabled, this option instructs Fontshow to query Fontconfig for
declared Unicode charset information and include it in the generated
inventory.

```bash
python -m fontshow.dump_fonts --include-fc-charset
```

The resulting data is stored in the optional `charset` field of each
font entry.

Fontconfig charset extraction is best-effort and depends on the
availability and behavior of fc-query on the host system.
On some distributions, fc-query cannot reliably be used to inspect
individual font faces, resulting in empty charset data.

---

## API reference

::: fontshow.dump_fonts
