# Performance Benchmarks

Fontshow performance benchmarks are local, on demand, and intentionally
outside CI. They use fixed downloaded fixtures, temporary output
directories, and Hyperfine JSON export.

No font dataset is committed to the repository.

## Requirements

Install Hyperfine outside the Python project dependencies:

```bash
sudo apt install hyperfine
```

Activate the repository virtual environment before running benchmarks:

```bash
source .venv/bin/activate
```

The benchmark runner hard-fails when `VIRTUAL_ENV` is not the repository
`.venv` or when `hyperfine` is not available on `PATH`.

## Fixture Setup

Generate the light fixture set:

```bash
scripts/setup_benchmark_fonts.sh light
```

Generate the heavy fixture set:

```bash
scripts/setup_benchmark_fonts.sh heavy
```

Both profiles write generated fonts under:

```text
tests/fixtures/fonts_dir/
```

The light profile downloads eight pinned font files from the Google Fonts
repository. The files are selected from `ofl/` directories, pinned to a
specific Google Fonts commit, and verified by SHA-256.

Pinned Google Fonts commit:

```text
47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b
```

Light profile families:

| Fixture | Source family |
| --- | --- |
| `Roboto.ttf` | `ofl/roboto` |
| `Roboto-Italic.ttf` | `ofl/roboto` |
| `OpenSans.ttf` | `ofl/opensans` |
| `NotoSans.ttf` | `ofl/notosans` |
| `NotoSerif.ttf` | `ofl/notoserif` |
| `Lato-Regular.ttf` | `ofl/lato` |
| `SourceCodePro.ttf` | `ofl/sourcecodepro` |
| `Inconsolata.ttf` | `ofl/inconsolata` |

The heavy profile starts from the same files and adds replicated local
copies under `tests/fixtures/fonts_dir/.heavy/`. This gives a larger
deterministic stress input without committing or redistributing fonts.

The generated fixture directory is ignored by Git.

## Running Benchmarks

Run the light profile:

```bash
scripts/benchmark.sh light
```

Run the heavy profile:

```bash
scripts/benchmark.sh heavy
```

The runner prepares fixed pipeline inputs before measuring:

```bash
fontshow dump-fonts \
  --paths tests/fixtures/fonts_dir \
  --output tests/fixtures/raw_inventory.json

fontshow parse-inventory \
  tests/fixtures/raw_inventory.json \
  --output tests/fixtures/sample_inventory.json
```

Then Hyperfine measures these stages independently:

```bash
fontshow dump-fonts --paths tests/fixtures/fonts_dir
fontshow parse-inventory tests/fixtures/raw_inventory.json
fontshow create-catalog --inventory tests/fixtures/sample_inventory.json
```

Each command uses one warmup run and three measured runs.

Measured command outputs are written to temporary directories. Hyperfine
results are exported to:

```text
tests/fixtures/benchmark_results/fontshow-light.json
tests/fixtures/benchmark_results/fontshow-heavy.json
```

Those result files are ignored by Git.

## Readiness Checks

The normal pytest suite does not run benchmarks and does not require
Hyperfine or downloaded fonts.

To verify local benchmark readiness without executing benchmarks:

```bash
FONTSHOW_BENCHMARK_READINESS=1 pytest -q tests/test_benchmark_workflow.py
```

These checks only verify:

- Hyperfine is available on `PATH`
- the generated fixture directory exists and contains font files

## Interpreting Results

Use the Hyperfine summary for quick comparisons and the JSON export for
recorded measurements. Compare profiles separately:

- `light` is for fast iteration and command-shape checks
- `heavy` is for stress and pre-release measurements

Do not compare results across machines without recording CPU, storage,
operating system, TeX installation state, and whether caches were warm.

No performance thresholds are enforced by tests.
