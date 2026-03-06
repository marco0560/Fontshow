#!/usr/bin/env python3

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCHEMA = ROOT / "fontshow/schema/inventory_v1_2.json"
DOC = ROOT / "docs/schema/inventory_v1_2.md"

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
        "ERROR: schema markers not found or malformed in docs/schema/inventory_v1_2.md"
    )
    raise SystemExit(msg)

pattern = re.compile(
    rf"{re.escape(START)}.*?{re.escape(END)}",
    re.DOTALL,
)

new_text = pattern.sub(replacement, text)

if new_text != text:
    DOC.write_text(new_text)
    print("Updated docs/schema/inventory_v1_2.md")
else:
    print("Schema documentation already up to date")
