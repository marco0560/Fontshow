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

## API reference

::: fontshow.dump_fonts
