# Roadmap – Fontshow

Questa roadmap descrive lo stato attuale del progetto Fontshow,
le attività completate e il piano di lavoro per le prossime fasi.
È un documento vivo e verrà aggiornato manualmente nel tempo.

---

## ✅ Attività completate (da chiudere su GitHub)

Le seguenti issue possono essere chiuse in quanto assorbite o
risolte dal lavoro svolto fino a C4.3:

- #2 – parse_font_inventory: Validation & Resilience (baseline completata)
- #3 – parse_font_inventory: Validation & Resilience (`--validate-inventory` baseline)
- #14 – create_catalog (task troppo generico, da scomporre)

---

## 🔥 Priorità immediate (C4.4)

### 1. JSON Schema & Versioning
**Riferimento:** Issue #6

- Formalizzare `schema_version`
- Definire regole di backward compatibility (1.x)
- Distinguere campi obbligatori vs opzionali
- Fornire esempi JSON per ogni versione
- Allineare codice, documentazione e test

---

### 2. create_catalog & qualità LaTeX
**Riferimenti:** Issue #4, #5

- Migliorare diagnostica LaTeX
- Gestire font problematici
- Aggiungere opzioni di debug:
  - `--dump-tex-per-font`
  - `--keep-temp`
  - `--debug-font`

---

### 3. LuaLaTeX robustness tests
**Riferimento:** Issue #5

- Test su font:
  - solo simboli
  - senza ASCII
  - con encoding non comuni
  - noti per crash LuaTeX

---

## 🐧 Native Linux & System Testing

**Riferimenti:** Issue #1, #8
Derivato dalla conversazione “Linux System questions”.

### Obiettivi
- Test reali su Gentoo
- Confronto con Fedora e WSL
- Verifica comportamento `fc-query`
- Valutazione `--include-fc-charset`

### Output attesi
- Documentazione dei risultati
- Elenco di edge cases
- Raccomandazioni pratiche

---

## 🔁 Priorità media

- #7 – Tool versioning alignment
- #11 – Repository hygiene (enhancements)
- #8 – Manual testing documentation (completamento)

---

## 🕐 Attività future / parcheggiate

- #12 – CI & Automation
- #9 – Packaging & CLI UX
- #10 – CLI consistency

---

## 📌 Note finali

- Questa roadmap non sostituisce le issue GitHub
- Serve come visione d’insieme e strumento di pianificazione
- Le milestone (C4.4, C5, …) verranno aggiornate qui
