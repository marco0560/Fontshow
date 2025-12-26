# Fontshow

Fontshow è un progetto Python per l’analisi, la normalizzazione e la catalogazione dei font installati su un sistema.

Il progetto nasce con l’obiettivo di:
- ottenere una visione strutturata dei font di sistema;
- individuare incoerenze e anomalie nei metadati;
- generare un catalogo finale utilizzabile (attualmente in formato LaTeX);
- mantenere separati dati grezzi, dati normalizzati e output finale.

La documentazione è organizzata in modo modulare, seguendo le diverse fasi della pipeline e i componenti principali del progetto.

---

## Panoramica della pipeline

La pipeline di Fontshow è composta da più fasi indipendenti, ciascuna con una responsabilità chiara.

Una descrizione concettuale e completa del flusso è disponibile in:

- [Pipeline Fontshow](pipeline.md)

---

## Architettura del progetto

La struttura generale del progetto, le responsabilità dei moduli e le scelte architetturali sono descritte in:

- [Architettura](architecture.md)

---

## Componenti della pipeline

Ogni fase della pipeline è documentata separatamente:

- [Dump dei font di sistema](tools/dump_fonts.md)
  Raccolta delle informazioni grezze sui font installati.

- [Parsing dell’inventario](tools/parse_font_inventory.md)
  Analisi, validazione e strutturazione dei dati dell’inventario.

- [Creazione del catalogo](tools/create_catalog.md)
  Generazione del catalogo finale a partire dai dati normalizzati.

---

## Modello dei dati

Il formato e il significato dei dati utilizzati all’interno del progetto sono descritti nel dizionario dei dati:

- [Data Dictionary](data_dictionary.md)

---

## Testing e qualità

Le modalità di test, validazione e controllo qualità del progetto sono descritte in:

- [Testing](testing.md)

---

## Stato del progetto

Il progetto è in sviluppo attivo.

Le attività aperte, il debito tecnico e le evoluzioni pianificate sono tracciate tramite **GitHub Issues**.
La documentazione viene aggiornata progressivamente per riflettere lo stato corrente del progetto.

---

## Note sulla documentazione

Questa documentazione rappresenta il **manuale operativo del progetto**.

Le decisioni progettuali storiche, i problemi incontrati e il contesto di sviluppo sono documentati separatamente nel **Diario di sviluppo**, che non fa parte della documentazione pubblica del repository.
