# Copilot / AI assistant guidance for Fontshow

## Project Purpose

**Fontshow** is a command-line toolkit for **font discovery, analysis, validation, and catalog generation**. It creates structured inventories of system fonts and generates human-readable PDF catalogs via LuaLaTeX. Designed for reproducibility, testability, schema-driven workflows, and explicit execution contracts.

---

## Core Pipeline & Commands

Fontshow implements a strict **multi-stage pipeline**:

```
preflight → dump-fonts → parse-inventory → create-catalog
```

Each stage:
- Consumes structured JSON from the previous stage
- Does not re-inspect binaries unnecessarily
- Returns explicit `int` exit codes (not `sys.exit()`)

### Key CLI Modules

| Module | Purpose | Command |
|--------|---------|---------|
| `fontshow.discovery.dump_fonts` | Font enumeration via FontConfig | `fontshow dump-fonts` |
| `fontshow.inventory.parse_font_inventory` | Script/language inference & validation | `fontshow parse-inventory` |
| `fontshow.catalog.create_catalog` | LaTeX catalog generation | `fontshow create-catalog` |
| `fontshow.preflight.runner` | Dependency/environment validation | `fontshow preflight` |

### Quick Test Commands

```bash
# Full pipeline on test font set (first 10 fonts)
python -m fontshow --help

# Run individual stage
python -m fontshow dump-fonts --help
python -m fontshow parse-inventory --help

# Syntax check
python -m py_compile fontshow/dump_fonts.py
```

---

## Core APIs & Type System

### Key Public Functions to Preserve

| Function | Module | Returns | Role |
|----------|--------|---------|------|
| `dump_fonts()` | `dump_fonts.py` | `dict` | Enumerate system fonts (FontConfig) |
| `parse_font_inventory()` | `parse_font_inventory.py` | `dict` | Enrich inventory with inference |
| `generate_latex()` | `create_catalog.py` | `str` | LaTeX document generation |
| `validate_inventory_schema()` | `schema_validation.py` | result object | Structural validation (v1.2) |

**Do not change return types without discussion.**

### Type System (Canonical Forms)

**Script Identity** — Strict standardization (Phase 5):

```python
ScriptISO = NewType("ScriptISO", str)      # Uppercase: "LATN", "ARAB", "HANI"
ScriptTag = NewType("ScriptTag", str)      # Lowercase: "latn", "arab", "hani"

# Conversion functions (preserve signatures):
def iso_to_tag(script: ScriptISO) -> ScriptTag
def tag_to_iso(tag: ScriptTag) -> ScriptISO | None
def normalize_script_iso(value: str | ScriptISO | ...) -> ScriptISO | None
```

**Enums** — JSON boundary invariant (Critical):

```python
class Severity(Enum):
    INFO, OK, WARN, ERROR
    def to_json() -> str              # → lowercase string on-disk
    @classmethod
    def from_str(value: str) -> Severity

class ExecutionContext(Enum):         # NATIVE, WSL, CONTAINER, OTHER
    def to_json() -> str              # → lowercase: "native"
```

**Inventory TypedDicts** (schema v1.2):
- `CoverageV12` — scripts/unicode_blocks coverage data
- `InferenceV12` — script/language inference results
- `WarningInfo` — severity/code/message structured warnings
- `CatalogFontEntryV12` — complete font entry

See [fontshow/types.py](fontshow/types.py) and [fontshow/schema/](fontshow/schema/).

---

## Critical Architectural Constraints

### 1. JSON Boundary Invariant ⚠️

**Rule**: On-disk enums are strings; in-memory enums are `Enum` objects.

```python
# After json.load():
from fontshow.json_boundary import normalize_loaded_enums
data = json.load(fp)
normalize_loaded_enums(data)  # Converts "warning" strings → Severity enum

# Before json.dump():
for entry in inventory:
    if hasattr(entry.get("severity"), "to_json"):
        entry["severity"] = entry["severity"].to_json()  # Enum → string
json.dump(data, fp)
```

**Violation examples**:
- ❌ Serializing `Severity.WARN` directly → produces `Severity.WARN` (invalid JSON)
- ❌ Comparing loaded string `"warn"` to `Severity.WARN` → fails

See [fontshow/json_boundary.py](fontshow/json_boundary.py).

### 2. Schema Validation Tiers

| Function | Purpose | Strictness | Behavior |
|----------|---------|-----------|----------|
| `_validate_inventory_schema_strict()` | Structural rules | Strict | **Raises `ValidationError`** on failure |
| `validate_inventory_schema()` | Public wrapper | Configurable | May log warnings instead |

Schema version: **v1.2** (see `fontshow.constants.SCHEMA_VERSION`).

### 3. Semantic Validation (Post-Schema)

- Happens **after** schema validation passes
- Enforces business rules: language normalization, script coverage checks
- See [fontshow/inventory/semantic_validation.py](fontshow/inventory/semantic_validation.py)

### 4. Structured Warnings (Single Source of Truth)

All phases use canonical warning emitter:

```python
def add_structured_warning(
    container: dict,
    *,
    code: str,
    message: str,
    severity: Severity,
    extra: dict[str, Any] | None = None
) -> None:
```

Appends to `container["warnings"]` list. Use in dump, parse, and catalog stages.

### 5. CLI Dispatch Contract

```python
def dispatch_command(args: argparse.Namespace) -> int:
    """
    Returns:
    - 0 on success (or SystemExit(0))
    - int > 0 on failure
    - 2 for unhandled exceptions

    Handler must return int (not call sys.exit() directly).
    Emits TRACE "flow" events for start/completion/crash.
    """
```

### 6. Structured Logging (TRACE + Standard)

```python
from fontshow.logging_utils import log, log_trace_cat

log.info("message")                           # Standard logging
log_trace_cat(log, "inventory", "script_coverage",
              extra={"script": "LATN", "coverage": 0.95})
```

- TRACE level = 5 (below DEBUG)
- Disabled by default (safe no-op)
- Enable via `FONTSHOW_LOG_LEVEL=TRACE` env var
- JSON-formatted with category filtering

See [fontshow/logging_utils.py](fontshow/logging_utils.py).

---

## Module Navigation

| Module | File | Role |
|--------|------|------|
| **discovery** | `fontshow/discovery/` | FontConfig integration, platform detection |
| **inventory** | `fontshow/inventory/` | Script analysis, semantic validation |
| **schema** | `fontshow/schema/` | Schema definitions (v1.2 + legacy) |
| **json** | `fontshow/json/` | Enum/boundary normalization |
| **latex** | `fontshow/latex/` | LaTeX template & rendering |
| **logging** | `fontshow/logging/` | Structured logging (TRACE + standard) |
| **preflight** | `fontshow/preflight/` | Dependency checks (env, fontconfig, etc.) |
| **platform** | `fontshow/platform/` | Platform metadata & detection |
| **types** | `fontshow/types.py` | Canonical TypedDict & type aliases |
| **constants** | `fontshow/constants/` | Global config (SCHEMA_VERSION, EXCLUDED_FONTS) |

---

## Testing & Validation

### Before Committing

```bash
# Syntax check
python -m py_compile fontshow/*.py fontshow/**/*.py

# Structural tests
python -m pytest tests/ -k "schema" -v

# Type check (if using mypy)
mypy fontshow/ --strict
```

### When Modifying…

**Type system** (ScriptISO, enums, TypedDicts):
- Run `tests/test_json_boundary.py` to verify enum serialization
- Check `tests/test_semantic_validation.py` for business rule changes
- Include test for `from_str()` / `to_json()` round-trip

**Schema**:
- Bump `SCHEMA_VERSION` in `fontshow/constants/` if incompatible
- Add migration test in `tests/test_output_schema_invariants.py`
- Run: `pytest tests/test_output_schema_invariants.py -v`

**CLI**:
- Verify exit code contract: `tests/test_cli_invariants.py`
- Ensure `dispatch_command()` returns `int`, not `SystemExit`

**Logging**:
- Test TRACE events: `tests/test_fc_query_logging.py`
- Format must be: `log_trace_cat(log, "<category>", "<event>", extra={...})`

---

## Configuration Constants & Conventions

Key module-level constants to edit cautiously:

| Constant | Module | Purpose | When to Change |
|----------|--------|---------|----------------|
| `SCHEMA_VERSION` | `fontshow/constants/` | Schema contract | Never without migration plan |
| `EXCLUDED_FONTS` | `fontshow/constants/` | Fonts that break compilation | After reproducing failure + documenting |
| `SUBPROCESS_TIMEOUT_SECONDS` | `fontshow/platform/` | FontConfig safety limit | Rarely; discuss first |
| `UNICODE_BLOCK_RANGES` | `fontshow/unicode/` | Unicode block definitions | Never; read-only |

---

## Platform Considerations

- **Linux**: FontConfig via `fc-list` (primary platform)
- **Windows**: Requires fallback enumeration (see `fontshow/platform/platform_metadata.py`)
- **WSL**: Detected separately; may use container vs. native FontConfig

When proposing platform-specific changes:
- State the target OS clearly
- Include sample `fc-list` input/output if FontConfig-related
- Test on actual platform if possible (or CI/CD)

---

## PR Guidance for AI Agents

1. **Keep changes small & focused.** Single concern per change.
2. **If modifying type system**: Provide round-trip test (serialize/deserialize).
3. **If modifying schema**: Include version bump + migration plan.
4. **If modifying CLI**: Verify exit code contract + handler return type.
5. **Run syntax & type checks** before submitting (`python -m py_compile ...`).
6. **Include test cases** for new business logic (semantic validation, warnings, script coverage).
7. **Document enum changes** in the PR body with `from_str()` / `to_json()` examples.

---

## Files of Interest

- [fontshow/dump_fonts.py](fontshow/dump_fonts.py) — Font enumeration entrypoint
- [fontshow/parse_font_inventory.py](fontshow/parse_font_inventory.py) — Inference & parsing
- [fontshow/create_catalog.py](fontshow/create_catalog.py) — LaTeX generation
- [fontshow/schema_validation.py](fontshow/schema_validation.py) — Structural validation
- [fontshow/inventory/semantic_validation.py](fontshow/inventory/semantic_validation.py) — Business rule enforcement
- [fontshow/json_boundary.py](fontshow/json_boundary.py) — Enum normalization (critical)
- [fontshow/types.py](fontshow/types.py) — Type aliases & TypedDicts
- [fontshow/logging_utils.py](fontshow/logging_utils.py) — Structured logging

---

## If Unclear

- **Type system questions?** Ask to clarify `ScriptISO` vs. `ScriptTag` usage or when to use `NewType` vs. plain `str`.
- **Schema version?** Ask before changing `SCHEMA_VERSION` or breaking backward compatibility.
- **Platform-specific?** State target OS and include real `fc-list` samples or platform metadata examples.
- **Enum changes?** Provide `from_str()` and `to_json()` test cases.

---

**Last updated**: 2026-03-06. Based on v1.2 schema and current modular architecture.
