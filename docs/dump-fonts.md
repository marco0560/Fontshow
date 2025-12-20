# dump_fonts.py – Supporto TrueType Collections (.ttc)

## Panoramica

A partire da questa versione, `dump_fonts.py` supporta **completamente i file
TrueType Collection (`.ttc`)**.

Un file `.ttc` non rappresenta un singolo font, ma un **contenitore di più font
indipendenti** (detti *faces*). Ogni face ha:
- tabelle OpenType proprie
- name table distinta
- copertura Unicode potenzialmente diversa

Per questo motivo, Fontshow **espande ogni `.ttc` in più voci di inventario**.

---

## Espansione delle collection

Durante il dump:

- 1 file `.ttc`
- ⟶ N descrittori di font
- ⟶ uno per ciascun `ttc_index`

Esempio concettuale:

```
NotoSansCJK.ttc
 ├─ index 0 → Noto Sans CJK JP
 ├─ index 1 → Noto Sans CJK KR
 ├─ index 2 → Noto Sans CJK SC
 └─ index 3 → Noto Sans CJK TC
```

---

## Identificazione delle facce

Ogni font derivato da una collection contiene:

```json
"identity": {
  "file": "/path/to/NotoSansCJK.ttc",
  "ttc_index": 2,
  "family": "Noto Sans CJK SC"
}
```

Il campo `ttc_index`:
- identifica in modo univoco la faccia
- è `null` per i font non provenienti da `.ttc`
- **deve essere preservato** da tutti i consumer dell’inventario

---

## Cache fontTools

Il caching di fontTools avviene a livello di *faccia*, non di file:

```
cache key = (path, mtime, size, ttc_index)
```

Questo evita:
- rianalisi inutili
- decompressioni ripetute di grandi collection (es. Noto CJK)

---

## Implicazioni per i consumer

Gli strumenti a valle (parser, generatori LaTeX, ecc.) devono:

- trattare ogni entry come un font indipendente
- usare `ttc_index` quando necessario per selezionare la faccia corretta

In LaTeX con `fontspec`, questo significa usare:

```latex
\fontspec[Index=<ttc_index>]{<Family Name>}
```

---

## Compatibilità

- Linux: supporto completo (fc-list + fontTools)
- Windows: supporto completo (filesystem + fontTools)
- macOS: non testato, ma il supporto fontTools per TTC è equivalente
