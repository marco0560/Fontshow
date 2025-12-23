# Architettura: gestione delle TrueType Collections

## Posizionamento nella pipeline

La gestione delle TrueType Collection avviene **nel primo stadio** della pipeline:

```
font files
   ↓
dump_fonts.py
   ├─ .ttf / .otf  → 1 font descriptor
   └─ .ttc         → N font descriptors (per-face)
   ↓
font_inventory.json
   ↓
parse_font_inventory.py
   ↓
create_catalog.py / pipeline LaTeX
```

---

## Razionale architetturale

La decisione di espandere le collection nel `dump` (e non a valle) garantisce:

- inventario canonico e normalizzato
- parsing uniforme
- assenza di logica specifica `.ttc` nei livelli successivi

---

## Responsabilità dei componenti

| Componente | Responsabilità |
|-----------|----------------|
| dump_fonts.py | Espansione `.ttc`, estrazione per-face |
| parse_font_inventory.py | Inferenza script/lingua |
| create_catalog.py | Rendering corretto (Index=…) |

---

## Nota sulla retrocompatibilità

L’aggiunta di `ttc_index` è:
- backward compatible per font non-TTC
- obbligatoria per i consumer che gestiscono collection
