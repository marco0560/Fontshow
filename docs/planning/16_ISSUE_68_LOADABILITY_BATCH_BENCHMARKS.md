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

The generated Hyperfine JSON files are intentionally ignored:

```text
tests/fixtures/benchmark_results/loadability-light.json
tests/fixtures/benchmark_results/loadability-medium.json
tests/fixtures/benchmark_results/loadability-heavy.json
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

## Interpretation

The light profile is too small to justify parallel scheduling. The
medium profile has exactly one default-size candidate chunk, so `jobs=2`
cannot create useful parallel work and is effectively neutral.

The heavy profile creates multiple candidate chunks and `jobs=2`
reduced wall-clock time by about 1.66x on this machine. User CPU time
increased, which is expected when two LuaLaTeX processes run
concurrently. System time remained stable, and this run did not expose
TeX-cache failures.

## Recommendation

Keep `jobs=1` as the production default. The measured benefit appears
only once an inventory has more than one loadability chunk, and the
parallel path needs more cross-machine evidence before becoming a
default.

If a future user-facing control is added, make it explicitly opt-in and
bounded:

- default: `jobs=1`
- first useful opt-in value: `jobs=2`
- only apply parallelism when candidate count exceeds the configured
  batch size
- require deterministic result collation by candidate index
- document TeX-cache contention as the main operational risk
