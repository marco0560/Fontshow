# dump_fonts.py – TrueType Collections (.ttc) Support

## Overview

As of this version, `dump_fonts.py` **fully supports TrueType Collection (`.ttc`) files**.

A `.ttc` file does not represent a single font, but rather a **container for multiple independent fonts** (called *faces*). Each face has:
- Its own OpenType tables
- A distinct name table
- Potentially different Unicode coverage

For this reason, Fontshow **expands each `.ttc` into multiple inventory entries**.

---

## Collection Expansion

During the dump:

- 1 `.ttc` file
- ⟶ N font descriptors
- ⟶ one for each `ttc_index`

Conceptual example:

```
NotoSansCJK.ttc
 ├─ index 0 → Noto Sans CJK JP
 ├─ index 1 → Noto Sans CJK KR
 ├─ index 2 → Noto Sans CJK SC
 └─ index 3 → Noto Sans CJK TC
```

---

## Face Identification

Each font derived from a collection contains:

```json
"identity": {
  "file": "/path/to/NotoSansCJK.ttc",
  "ttc_index": 2,
  "family": "Noto Sans CJK SC"
}
```

The `ttc_index` field:
- Uniquely identifies the face
- Is `null` for fonts not originating from a `.ttc`
- **Must be preserved** by all inventory consumers

---

## fontTools Cache

fontTools caching occurs at the *face* level, not the file level:

```
cache key = (path, mtime, size, ttc_index)
```

This avoids:
- Unnecessary re-analysis
- Repeated decompressions of large collections (e.g., Noto CJK)

---

## Implications for Consumers

Downstream tools (parsers, LaTeX generators, etc.) must:

- Treat each entry as an independent font
- Use `ttc_index` when necessary to select the correct face

In LaTeX with `fontspec`, this means using:

```latex
\fontspec[Index=<ttc_index>]{<Family Name>}
```

---

## Compatibility

- Linux: full support (fc-list + fontTools)
- Windows: full support (filesystem + fontTools)
- macOS: untested, but fontTools support for TTC is equivalent

---

## Dependencies

- fontTools:
    - **optional**
    - Enables: Unicode coverage, unicode_blocks, OpenType features
    - If absent:
        - coverage.unicode is empty
        - coverage.unicode_blocks is empty
        - Inference quality degrades
- fontconfig:
    - Linux-only
    - Optional
