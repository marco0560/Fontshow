# Estensione dello schema: TrueType Collections (.ttc)

Questa sezione documenta i campi aggiuntivi introdotti per supportare
i file TrueType Collection (`.ttc`) nello schema di `font_inventory.json`.

---

## identity.ttc_index

```json
"identity": {
  "file": "string",
  "ttc_index": "integer | null"
}
```

- `ttc_index` è l’indice della faccia all’interno della collection
- vale `null` per font non provenienti da `.ttc`
- insieme a `file`, identifica **univocamente** un font reale

---

## format.ttc_index e format.ttc_count

```json
"format": {
  "container": "TTC",
  "ttc_index": "integer",
  "ttc_count": "integer"
}
```

- `container == "TTC"` indica una TrueType Collection
- `ttc_index`:
  - indice della faccia corrente
- `ttc_count`:
  - numero totale di facce nella collection

---

## Invarianti semantiche

- Ogni entry in `fonts[]` rappresenta **un font reale**
- I file `.ttc` non sono mai trattati come singolo font
- `ttc_index` è obbligatorio quando `container == "TTC"`

---

## Uso nei consumer (LaTeX / fontspec)

I consumer **devono** usare `ttc_index` per selezionare la faccia corretta.

Esempio:

```latex
\fontspec[Index=3]{Noto Sans CJK}
```

Ignorare `ttc_index` comporta:
- selezione implicita della faccia 0
- risultati errati per la maggior parte delle collection
