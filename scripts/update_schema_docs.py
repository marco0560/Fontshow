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

pattern = re.compile(
    rf"{START}.*?{END}",
    re.DOTALL,
)

new_text = pattern.sub(replacement, text)

DOC.write_text(new_text)
