# Active Project Decisions

This document lists the **currently active project decisions** for Fontshow.

It does **not** include:
- historical background;
- discarded alternatives;
- past motivations.

For historical context and the evolution of decisions, refer to the **Development Diary**.

---

## Language and project structure

- **Python** is the primary language of the project.
- The project is structured as a **package**, not as a collection of standalone scripts.
- Module execution is preferably performed using:
  - `python -m <module>`

---

## Pipeline architecture

- The pipeline is divided into **independent stages**.
- Each stage has:
  - explicit inputs;
  - explicit outputs;
  - well-defined responsibilities.
- Intermediate artifacts (inventories, JSON files, LaTeX files) are considered an **integral part of the project**, not temporary by-products.

---

## Data handling

- Raw data is not modified or “cleaned” silently.
- Normalization:
  - does **not replace** original values;
  - adds normalized versions alongside the original data.
- The **Data Dictionary** is the normative reference for the meaning of data fields.

---

## Documentation

- Official project documentation is maintained using **MkDocs**.
- Markdown files under `docs/` constitute the **operational manual**.
- Automatically generated documentation based on code extraction is **not used**.
- The README and cheat-sheets are derived from the MkDocs documentation.

---

## Testing and quality

- Automated tests are based on **pytest**.
- Quality checks include linting and static validation tools.
- CI is considered the final authority on code quality.

---

## Work tracking and technical debt

- TODOs, bugs, and technical debt are tracked **exclusively via GitHub Issues**.
- Static TODO files in the repository are not used.
- Issues represent the operational state of the work.

---

## Development environment

- Development takes place in Linux and Linux-like environments (including WSL).
- Differences between environments are considered part of the problem domain.
- Validation on native Linux is considered necessary for critical functionality.

---

## Decision status

The decisions listed in this document are to be considered **binding** for current project development.

Any changes to these decisions must be:
- explicitly discussed;
- reflected in this document;
- traceable through dedicated commits.
