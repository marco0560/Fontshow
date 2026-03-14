# Decision 0023 - Font skip accounting and legacy format filtering

**Date**: 14/03/2026
**Status**: Accepted

## Context

During inventory generation (`fontshow dump-fonts`) the pipeline may encounter
font files that cannot be safely processed.

Two main categories were observed:

1. **Legacy font formats**

   Examples:

   - `.pfb`
   - `.pfa`
   - `.t1`
   - `.pcf`
   - `.pcf.gz`
   - `.bdf`

   These formats are either:

   - Type1 fonts not reliably supported by the Fontshow pipeline
   - bitmap formats incompatible with fontTools-based processing

   Attempting to process them produces unreliable metadata or parser errors.

2. **Structurally unloadable fonts**

   Some fonts are valid OpenType containers but cannot be processed by the
   Fontshow pipeline because they lack outline glyph tables.

   Example:

   - `NotoColorEmoji.ttf`

   These fonts contain bitmap color glyph tables such as:

   - `CBDT`
   - `CBLC`

   and do not expose:

   - `glyf`
   - `CFF`
   - `CFF2`

   required for the pipeline’s glyph and charset analysis.

Prior to this decision the pipeline produced repeated warnings when such fonts
were encountered and the final summary did not clearly report skipped fonts.

This made debugging and CI inspection unnecessarily difficult.

## Decision

The pipeline is modified as follows.

### 1. Early filtering of legacy formats

Files with extensions belonging to:

```text
.pfb
.pfa
.t1
.pcf
.pcf.gz
.bdf
```

are skipped during discovery.

The skip reason is recorded in the counter:

```python
skipped_legacy_extension
```

### 2. Structural unloadability detection

Fonts that cannot be loaded by the fontTools parser are skipped and counted as:

```python
skipped_structurally_unloadable
```

This detection remains **structural**, not extension-based.

This ensures future compatibility with evolving OpenType formats.

### 3. Warning deduplication

Warnings for structurally unloadable fonts are emitted **once per font file**
to avoid log flooding.

### 4. Improved dump summary

The final `dump-fonts` summary now reports skip counters, for example:

```text
[INFO] dump-fonts summary
       total_faces_seen=5246
       total_font_files=5238
       total_fonts=5244
       skipped_legacy_extension=12
       skipped_structurally_unloadable=2
       style_leak_suspected=0
```

This makes CI logs and manual runs easier to interpret.

## Consequences

Positive:

- Cleaner logs during large font scans
- Deterministic reporting of skipped fonts
- Improved observability of discovery pipeline behavior
- Reduced confusion caused by repeated warnings

Negative:

- Some fonts present on the system will not appear in inventories
- Additional counters slightly increase code complexity

## Alternatives considered

### Filter emoji fonts by extension

Rejected.

Emoji fonts are valid `.ttf` files and future versions of the pipeline may
support them. Structural detection is more robust.

### Ignore unloadable fonts silently

Rejected.

Visibility of skipped fonts is important for debugging and reproducibility.

### Fail the dump process

Rejected.

Font inventories should remain robust even in heterogeneous environments.

## Related components

- `dump-fonts` command
- font discovery pipeline
- inventory generation
- logging subsystem

## Related issues

Issue #58 — Skip legacy font formats during discovery
