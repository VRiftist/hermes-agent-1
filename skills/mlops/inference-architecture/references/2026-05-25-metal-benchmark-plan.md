# 2026-05-25: Metal Backend Realities & Overnight Benchmark Plan

## Key Discoveries

### 1. Ollama on Mac Already Uses Metal
Switching from Ollama to raw MLX does NOT change performance. Both hit the same unified-memory bandwidth ceiling on M2 Pro. The framework is not the bottleneck — memory topology is.

### 2. MLX API Versioning Gotcha
`mx.metal.device_properties()` does not exist in MLX 0.31.2. Fix:
```python
try:
    memory = mx.metal.device_properties()['memory_size']
except:
    memory = 10 * 1024 * 1024 * 1024  # M2 Pro ~10GB GPU fallback
```

### 3. M2 Pro Memory Topology (Confirmed)
- Total unified memory: 32GB
- GPU high-bandwidth region: ~10GB
- Models >10GB constantly page between fast and slow memory
- `qwen2.5-coder:32b` Q4 = ~19.9GB → ~4GB left for KV → ~3.5K practical context
- Explains why 32B on Mac maxed at ~8K with heavy swapping

### 4. Chrome Kills Inference (Confirmed)
20+ Chrome renderer processes consume ~4.8GB. Effective inference RAM drops 15-20%. Always kill Chrome before benchmarking.

### 5. Parallel Benchmarking Causes Crashes
Confirmed 2026-05-24: multiple models simultaneously on 32GB Mac causes GPU contention, OOM, process kills. Sequential only with explicit unload + `mx.metal.clear_cache()`.

## Overnight Benchmark Plan

| Order | Model | Method | Context Range | Why |
|-------|-------|--------|---------------|-----|
| 1 | qwen2.5-coder:7B | Ollama (Metal) | 8K, 16K, 24K, 32K, 40K | Lightweight, stays on GPU |
| 2 | qwen2.5-coder:14B | Ollama (Metal) | 4K, 8K, 12K, 16K, 20K | Best GPU sweet spot |
| 3 | qwen2.5-coder:32B | Ollama (CPU) | 2K, 4K, 8K | Baseline (known ~8K) |
| 4 | qwen3:8b | Ollama (Metal) | 4K, 8K, 12K | Control baseline |

- Sequential: load → quality prompt → context climb → unload → clear cache → 10s gap
- Auto-save after each model to `~/.hermes/mac_gpu_benchmark.json`
- Fully unattended, exit code 0 always
- Est. total: ~2-3 hours

**Expected winner:** 14B at 8K-16K context — best quality-to-resource ratio.