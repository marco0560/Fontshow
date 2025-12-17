import sys
from pathlib import Path

version = sys.argv[1]
pyproject = Path("pyproject.toml")

text = pyproject.read_text(encoding="utf-8").splitlines()

out = []
for line in text:
    if line.strip().startswith("version ="):
        out.append(f'version = "{version}"')
    else:
        out.append(line)

pyproject.write_text("\n".join(out) + "\n", encoding="utf-8")

print(f"Updated pyproject.toml to version {version}")
