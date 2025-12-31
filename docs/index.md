# Fontshow

Fontshow is a Python project for the analysis, normalization, and cataloging of fonts installed on a system.

The project was created with the following goals:
- obtain a structured overview of system fonts;
- identify inconsistencies and anomalies in font metadata;
- generate a usable final catalog (currently in LaTeX format);
- keep raw data, normalized data, and final output clearly separated.

The documentation is organized in a modular way, reflecting the different stages of the pipeline and the main components of the project.

---

## Pipeline overview

The Fontshow pipeline is composed of several independent stages, each with a clearly defined responsibility.

A complete conceptual description of the workflow is available in:

- [Fontshow Pipeline](pipeline.md)

---

## Project architecture

The overall project structure, module responsibilities, and architectural decisions are described in:

- [Architecture](architecture.md)

---

## Pipeline components

Each pipeline stage is documented separately:

- [System font dump](tools/dump_fonts.md)
  Collection of raw information about installed system fonts.

- [Inventory parsing](tools/parse_font_inventory.md)
  Analysis, validation, and structuring of inventory data.

- [Catalog creation](tools/create_catalog.md)
  Generation of the final catalog from normalized data.

---

## Data model

The format and meaning of the data used within the project are described in the data dictionary:

- [Data Dictionary](data_dictionary.md)

---

## Testing and quality

Testing strategies, validation procedures, and quality control are described in:

- [Testing](testing.md)

---

## Development & Security

Guidelines for contributors can be found in:

- [General contribution guidelines](CONTRIBUTING.md)
- [Development environment](development_security/dev-environment.md)
- [Security and Commit Policy](development_security/security-policy.md)
- [Key rotation policy](development_security/key-rotation.md)

---

## Project status

The project is under active development.

Open tasks, technical debt, and planned evolutions are tracked via **GitHub Issues**.
The documentation is progressively updated to reflect the current state of the project.

---

## Documentation notes

This documentation represents the **operational manual of the project**.

Historical design decisions, encountered issues, and development context are documented
separately in the **Development Log**, which is not part of the public documentation of the repository.
