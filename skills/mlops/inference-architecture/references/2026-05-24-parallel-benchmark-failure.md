# Parallel Benchmark Failure (2026-05-24)

## What Happened

Agent launched all three Mac benchmarks simultaneously:
- `qwen3:8b` at 16K context
- `qwen3:14b` at 16K context
- `qwen2.5-coder:32b-instruct-q4_K_M` at 64K context

## Why It Failed

All three models loaded at once on a 32GB Mac:
- qwen3:8b = 5.2GB
- qwen3:14b = 9.3GB
- qwen2.5-coder:32b = 19.9GB
- **Total: 34.4GB — exceeds total RAM**

GPU contention (even CPU inference shares memory bandwidth) caused OOM kills.

## Lesson

**Sequential only.** One model at a time. Wait for completion, report, then next.
On Mac: max ~2 small models can coexist (8b + 14b = ~14.5GB).

## Decision

User confirmed: sequential benchmarks only. Kill any parallel launch.