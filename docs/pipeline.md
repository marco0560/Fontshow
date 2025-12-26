# Pipeline Fontshow

## Panoramica

La pipeline di Fontshow è progettata come una **sequenza di fasi distinte**, ciascuna con una responsabilità chiara e con output espliciti.

L’obiettivo della pipeline è:
- raccogliere informazioni sui font installati nel sistema;
- normalizzare e validare tali informazioni;
- produrre un catalogo finale utilizzabile (attualmente in formato LaTeX).

Il principio guida è la **separazione delle responsabilità**: ogni fase può essere eseguita, verificata e debuggata in modo indipendente.

---

## Flusso generale

La pipeline logica può essere riassunta come:

```
Sistema
  ↓
Dump dei font
  ↓
Inventario
  ↓
Parsing e validazione
  ↓
Normalizzazione
  ↓
Generazione catalogo
```

Ogni fase produce uno o più artefatti intermedi, che possono essere conservati per analisi successive.

---

## Fase 1 — Dump dei font di sistema

La prima fase consiste nella raccolta delle informazioni grezze sui font installati nel sistema.

Questa fase:
- interroga il sistema tramite `fontconfig`;
- raccoglie il percorso dei file dei font e i metadati disponibili;
- **non applica alcuna normalizzazione o correzione**.

Il risultato è un dump che riflette fedelmente lo stato del sistema in un determinato momento.

👉 Per i dettagli di implementazione, vedi:
- [`dump_fonts.md`](tools/dump_fonts.md)

---

## Fase 2 — Creazione dell’inventario

Il dump dei font viene trasformato in un **inventario strutturato**, che rappresenta una fotografia coerente dei font di sistema.

Caratteristiche dell’inventario:
- formato leggibile dall’uomo;
- struttura stabile;
- assenza di “correzioni silenziose”.

L’inventario può contenere:
- dati incompleti;
- nomi non normalizzati;
- irregolarità provenienti dal sistema.

Questo è intenzionale: l’inventario descrive la realtà, non una versione idealizzata.

---

## Fase 3 — Parsing e validazione dell’inventario

In questa fase l’inventario viene analizzato e trasformato in strutture dati più ricche.

Il parsing:
- interpreta le singole voci dell’inventario;
- associa i font ai rispettivi file;
- segnala errori e anomalie.

È disponibile una modalità di **validazione esplicita**, che:
- individua le righe problematiche;
- associa ogni errore al percorso del font coinvolto;
- consente di decidere se interrompere o meno l’elaborazione.

👉 Dettagli in:
- [`parse_font_inventory.md`](tools/parse_font_inventory.md)

---

## Fase 4 — Normalizzazione dei dati

Dopo il parsing, i dati vengono normalizzati per ridurre ambiguità e incoerenze.

La normalizzazione riguarda principalmente:
- nomi delle famiglie tipografiche;
- stili (Regular, Bold, Italic, ecc.);
- variazioni nominali equivalenti.

Una scelta progettuale importante è che:
- i valori originali vengono **conservati**;
- le versioni normalizzate vengono **aggiunte**, non sostituite.

Questo consente di mantenere tracciabilità e facilita il debugging.

---

## Fase 5 — Generazione del catalogo

L’ultima fase della pipeline è la generazione del catalogo finale, attualmente in formato **LaTeX**.

In questa fase:
- vengono selezionati i font effettivamente utilizzabili;
- i font incompatibili o problematici vengono esclusi o segnalati;
- viene generato un file `.tex` pronto per la compilazione.

È normale che:
- il numero di font nel catalogo finale sia inferiore a quello presente nel dump iniziale;
- alcuni font causino problemi in fase di compilazione LaTeX.

👉 Dettagli in:
- [`create_catalog.md`](tools/create_catalog.md)

---

## Artefatti della pipeline

La pipeline produce diversi artefatti intermedi, tra cui:
- dump dei font;
- inventari;
- file JSON intermedi;
- file LaTeX finali.

Questi artefatti:
- non sono solo output temporanei;
- possono essere utilizzati per confronti tra sistemi;
- facilitano test, debugging e validazione.

---

## Considerazioni sull’ambiente

Il comportamento della pipeline può variare in funzione dell’ambiente:
- Linux nativo;
- WSL;
- configurazione di `fontconfig`.

Per questo motivo:
- alcune funzionalità sono marcate come *experimental*;
- la validazione completa su Linux nativo è considerata un passo necessario.

---

## Collegamenti

Per approfondire i singoli componenti:

- Architettura generale:
  [`architecture.md`](architecture.md)

- Dizionario dei dati:
  [`data_dictionary.md`](data_dictionary.md)

- Dump dei font:
  [`dump_fonts.md`](tools/dump_fonts.md)

- Parsing dell’inventario:
  [`parse_font_inventory.md`](tools/parse_font_inventory.md)

- Creazione del catalogo:
  [`create_catalog.md`](tools/create_catalog.md)

---

## Stato della pipeline

La pipeline è considerata **funzionalmente completa**, ma ancora in evoluzione per quanto riguarda:
- robustezza su ambienti diversi;
- test automatici;
- gestione dei casi limite.

Le attività aperte sono tracciate tramite **GitHub Issues**.
