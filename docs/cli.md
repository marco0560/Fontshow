# Command-line interface

Fontshow currently provides a preflight-only CLI.

## Common flags

| Flag | Description |
|-----|------------|
| `--help` | Show usage information |
| `--verbose` | Show informational and successful checks |
| `--quiet` | Suppress all output, rely on exit code |

## Exit codes

- `0`: preflight passed (with or without warnings)
- `1`: preflight failed (one or more errors)

## Examples

Fontshow is currently invoked as a Python module:

```bash
python -m fontshow
python -m fontshow --help
python -m fontshow --version
python -m fontshow --verbose
python -m fontshow --quiet
```
Note: a standalone fontshow command will be provided in a future release.

---
