# Decision 0010 - Separation between CLI verbosity and debug-only inference output

Date: 23/01/2026
Status: Accepted

## Context

During the normalization of CLI output behavior (stdout / stderr / quiet / verbose),
it was observed that some diagnostic output related to font inference is already
guarded by the environment variable:

```bash
    FONTSHOW_DEBUG_INFERENCE=1
```

This mechanism predates the current CLI verbosity model and is intentionally used
to enable **deep, developer-oriented diagnostics** that are not meant for normal
CLI usage.

At the same time, the project defines a CLI-level verbosity flag (`--verbose`)
intended for user-facing diagnostic output.

This raises the question of whether the two mechanisms should be unified.

---

## Decision

The two mechanisms are **intentionally kept separate**.

### 1. `--verbose`

- Controls **CLI-level diagnostic output**
- Intended for users
- Affects normal execution visibility
- Must not expose internal or experimental data

### 2. `FONTSHOW_DEBUG_INFERENCE`

- Controls **internal inference debugging**
- Intended for developers only
- Enables deep inspection of font inference logic
- May produce verbose, low-level, or unstable output
- Is **not** part of the CLI contract

These two mechanisms serve different audiences and purposes and **must not be merged**.

---

## Consequences

### What this means

- Debug inference output remains gated only by:

```bash
  FONTSHOW_DEBUG_INFERENCE=1
```

- `--verbose` does **not** enable inference debugging
- CLI normalization work must **not modify or wrap** inference debug output
- No additional verbosity checks are introduced in this area

### What this avoids

- Accidental exposure of internal diagnostics to end users
- Semantic overloading of `--verbose`
- Behavior changes during CLI normalization
- Future ambiguity about debug vs diagnostic output

---

## Verbosity and command class distinction

Verbosity levels (`--quiet`, `--verbose`) do not imply identical output
semantics across all CLI commands.

In particular:

- **Machine-oriented commands** (e.g. `preflight`, `dump-fonts`)
  may emit minimal success tokens such as `OK`, as their primary role
  is automation and scripting.

- **User-facing diagnostic commands** (e.g. `parse-inventory`)
  MUST emit descriptive, human-readable output.
  They MUST NOT replace success messages with generic tokens like `OK`.

This distinction is intentional and aligns with
Decision 0009 (CLI verbosity contract).

Verbosity controls *amount of information*, not *semantic class of output*.

---

## Related Work

- CLI stdout/stderr normalization (M1)
- Issue #46 — CLI output audit
- Refactoring of print vs logging behavior
- Debug inference logic in `parse_font_inventory.py`

---

## Non-Goals

- Replace environment-based debugging
- Introduce logging levels for inference
- Merge debug and verbose semantics
- Refactor inference logic

---

## Rationale

This decision preserves:

- backward compatibility
- clarity of intent
- separation of concerns
- predictable CLI behavior

It also ensures that CLI normalization remains a **mechanical change** and not a
semantic redesign.

---

## Intentional output Decision: `--list-test-fonts` ignores `--quiet`

### Context of `--list-test-fonts`

The `--list-test-fonts` option is designed as an inspection / query command.
Its sole purpose is to display information to the user.

Unlike other execution paths, it does not perform processing or produce side effects.

### Decision about `--list-test-fonts`

The `--list-test-fonts` command intentionally ignores the `--quiet` flag.

### Rationale for `--list-test-fonts`

- `--quiet` is meant to suppress progress and diagnostic output
- `--list-test-fonts` *is* the output
- Suppressing it would make the command meaningless
- Aligns with the behavior of similar “list / show” commands in CLI tools

### Consequences of `--list-test-fonts`

- `--quiet` suppresses pipeline output
- `--quiet` does **not** suppress `--list-test-fonts`
- This behavior is intentional and documented

---

## Future Considerations

If a unified verbosity model is desired in the future, it must be addressed via:

- a dedicated design proposal
- explicit deprecation strategy
- clear user-facing documentation

Not within the scope of the current work.
