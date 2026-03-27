#!/usr/bin/env python3
"""
Synchronize schema documentation with the canonical JSON schema.

This maintenance script updates the embedded JSON schema section in the
inventory schema documentation so the rendered markdown stays aligned
with the authoritative schema file in the repository.

Responsibilities
----------------
- Read the canonical inventory schema JSON document.
- Replace the marked schema block inside the schema markdown document.
- Write updated documentation only when the rendered schema changes.

Design principles
-----------------
Schema documentation must be derived from the canonical schema source
rather than edited manually. The script performs a marker-bounded update
so documentation remains synchronized while preserving surrounding prose.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a
documentation-maintenance utility for schema-related project artifacts.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

constants_text = (ROOT / "src/fontshow/core/global_constants.py").read_text(
    encoding="utf-8"
)
match = re.search(r'SCHEMA_VERSION = "([^"]+)"', constants_text)
if match is None:
    msg = "ERROR: could not determine SCHEMA_VERSION from core constants"
    raise SystemExit(msg)
SCHEMA_VERSION = match.group(1)

SCHEMA = (
    ROOT / f"src/fontshow/schema/inventory_v{SCHEMA_VERSION.replace('.', '_')}.json"
)
DOC = ROOT / f"docs/schema/inventory_v{SCHEMA_VERSION.replace('.', '_')}.md"

START = "<!-- SCHEMA_JSON_START -->"
END = "<!-- SCHEMA_JSON_END -->"

schema = json.loads(SCHEMA.read_text())
pretty = json.dumps(schema, indent=2, ensure_ascii=False)

replacement = f"""{START}

```json
{pretty}
```

{END}"""

text = DOC.read_text()

if START not in text or END not in text:
    msg = (
        "ERROR: schema markers not found or malformed in "
        f"docs/schema/inventory_v{SCHEMA_VERSION.replace('.', '_')}.md"
    )
    raise SystemExit(msg)

pattern = re.compile(
    rf"{re.escape(START)}.*?{re.escape(END)}",
    re.DOTALL,
)

new_text = pattern.sub(replacement, text)

if new_text != text:
    DOC.write_text(new_text)
    print(f"Updated {DOC.relative_to(ROOT)}")
else:
    print("Schema documentation already up to date")
