# Issue 68 - Loadability Batch Benchmark Results

## Scope

Issue `#68` evaluates whether the persisted LuaLaTeX loadability probe
should run multiple candidate batches in parallel.

Normal `dump-fonts` behavior remains serial by default. The benchmark
path added for this issue exercises a benchmark-only `jobs` parameter in
the inventory loadability helper through:

```bash
scripts/benchmark_loadability_batches.sh light 1 2
scripts/benchmark_loadability_batches.sh medium 1 2
scripts/benchmark_loadability_batches.sh heavy 1 2
```

For a full local inventory, generate a dedicated ignored input and use
Hyperfine to compare explicit job counts:

```bash
fontshow dump-fonts \
  --paths /path/to/fonts \
  --cache-dir tests/fixtures/benchmark_results/full-input-cache \
  --output tests/fixtures/full_loadability_benchmark_inventory.json

hyperfine \
  --warmup 1 \
  --runs 3 \
  --export-json tests/fixtures/benchmark_results/loadability-full-jobs.json \
  --command-name "loadability jobs=1" \
  "python scripts/run_loadability_probe.py tests/fixtures/full_loadability_benchmark_inventory.json --output /tmp/loadability-full-jobs-1.json --jobs 1" \
  --command-name "loadability jobs=2" \
  "python scripts/run_loadability_probe.py tests/fixtures/full_loadability_benchmark_inventory.json --output /tmp/loadability-full-jobs-2.json --jobs 2" \
  --command-name "loadability jobs=4" \
  "python scripts/run_loadability_probe.py tests/fixtures/full_loadability_benchmark_inventory.json --output /tmp/loadability-full-jobs-4.json --jobs 4" \
  --command-name "loadability jobs=8" \
  "python scripts/run_loadability_probe.py tests/fixtures/full_loadability_benchmark_inventory.json --output /tmp/loadability-full-jobs-8.json --jobs 8" \
  --command-name "loadability jobs=12" \
  "python scripts/run_loadability_probe.py tests/fixtures/full_loadability_benchmark_inventory.json --output /tmp/loadability-full-jobs-12.json --jobs 12"
```

The generated Hyperfine JSON files are intentionally ignored:

```text
tests/fixtures/benchmark_results/loadability-light.json
tests/fixtures/benchmark_results/loadability-medium.json
tests/fixtures/benchmark_results/loadability-heavy.json
tests/fixtures/benchmark_results/loadability-full-jobs.json
```

## Local Measurement Context

- Date: 2026-04-18
- Host: `verona`
- Kernel: Linux 6.18.18-gentoo-dist
- CPU: Intel Core i7-8700K, 6 cores / 12 threads
- TeX engine: LuaHBTeX 1.18.0, TeX Live 2024 Gentoo Linux
- Hyperfine settings: 1 warmup, 3 measured runs
- Batch size: 32 candidates

## Results

| Profile | Fonts | Jobs | Mean | Stddev | User | System |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| light | 8 | 1 | 1.486 s | 0.029 s | 1.369 s | 0.115 s |
| light | 8 | 2 | 1.429 s | 0.158 s | 1.330 s | 0.098 s |
| medium | 32 | 1 | 4.810 s | 0.236 s | 4.624 s | 0.178 s |
| medium | 32 | 2 | 4.847 s | 0.258 s | 4.672 s | 0.160 s |
| heavy | 72 | 1 | 10.660 s | 0.265 s | 10.222 s | 0.396 s |
| heavy | 72 | 2 | 6.412 s | 0.228 s | 10.998 s | 0.393 s |

## Full Local Inventory Results

The full local inventory run used the same host and TeX context as the
fixture measurements, but with the user's complete font tree.

| Jobs | Mean | Stddev | User | System | Speedup vs serial |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 245.164 s | 0.643 s | 226.619 s | 17.975 s | 1.00x |
| 2 | 127.385 s | 1.601 s | 234.325 s | 18.076 s | 1.92x |
| 4 | 70.060 s | 2.776 s | 254.046 s | 18.998 s | 3.50x |
| 8 | 47.287 s | 1.578 s | 335.482 s | 22.840 s | 5.18x |
| 12 | 40.762 s | 2.350 s | 396.046 s | 27.467 s | 6.01x |

All replay outputs had the same SHA-256 digest:

```text
524ba602d5b08cd82a480bc937861c96c01dfec793ca569518d0ccc20a4a9d28
```

## Interpretation

The light profile is too small to justify parallel scheduling. The
medium profile has exactly one default-size candidate chunk, so `jobs=2`
cannot create useful parallel work and is effectively neutral.

The heavy profile creates multiple candidate chunks and `jobs=2`
reduced wall-clock time by about 1.66x on this machine. User CPU time
increased, which is expected when two LuaLaTeX processes run
concurrently. System time remained stable, and this run did not expose
TeX-cache failures.

The full local inventory shows near-linear scaling through `jobs=4`,
continued useful scaling at `jobs=8`, and a smaller but still real gain
at `jobs=12`. The `jobs=12` result is the fastest on this 12-thread
machine, reducing wall-clock time from about 245 s to about 41 s while
preserving byte-identical output. CPU time and system time increase at
higher job counts, so `jobs=12` is suitable when throughput is the
priority and the machine can be dedicated to the run.

## Recommendation

Keep `jobs=1` as the production default. The measured benefit appears
only once an inventory has more than one loadability chunk, and the
parallel path remains workload- and machine-dependent.

If a future user-facing control is added, make it explicitly opt-in and
bounded:

- default: `jobs=1`
- first useful opt-in value: `jobs=2`
- recommended full-inventory starting points: `jobs=4` or `jobs=8`
- use `jobs=12` only when benchmarked locally and the machine can absorb
  the CPU load
- only apply parallelism when candidate count exceeds the configured
  batch size
- require deterministic result collation by candidate index
- document TeX-cache contention as the main operational risk
