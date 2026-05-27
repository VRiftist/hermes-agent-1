# Model Selection Analysis: Mac M2 32GB (2026-05-27)

## Context
Gerald needed to finalize which local LLM should serve as the primary code generation model on his Mac Mini M2 (32GB unified memory). Multiple models were on disk from prior sessions; benchmarks and vendor specs were cross-referenced.

## Key Finding: MoE Models Are Worse Than Dense On Apple Silicon Metal

**Failure mode:** qwen3-coder:30b-a3b (MoE, 30B params, ~3B active per token) was expected to outperform qwen2.5-coder:32B (dense) because fewer active parameters = less compute. **This did not hold on Metal.**

Why:
- MoE expert routing requires cross-layer parallelism that Metal's GPU shader cores don't efficiently support
- Full model weights (20.5+ GB for Q4) must be loaded into unified memory regardless of active param count
- Apple's memory bandwidth bottleneck means routing overhead adds latency without the compute benefit seen on NVIDIA GPUs
- Result: **slower than the dense 32B model** in practice

**General rule (validated):** On Apple Silicon with unified memory, prefer dense smaller models over MoE larger models. MoE advantages require GPU architectures with fast inter-layer switching (NVIDIA H100/A100 class).

## Models Evaluated

| Model | Arch | Disk (Q4) | RAM Needed | Metal GPU | Verdict |
|-------|------|-----------|-----------|-----------|---------|
| qwen3:14b | Dense | 8.64 GB | ~10 GB | YES | WINNER |
| qwen2.5-coder:14b | Dense | 9.0 GB | ~10 GB | YES | Strong alternative |
| qwen3:8b | Dense | 4.87 GB | ~6 GB | YES | Context trimmer |
| qwen2.5-coder:7b | Dense | 4.7 GB | ~5 GB | YES | Fast tool use |
| qwen2.5-coder:32b | Dense | 18.9 GB | ~22 GB | NO (CPU) | Too slow, too big |
| qwen3-coder:30b-a3b | MoE | 29.6 GB | ~21 GB | NO (Metal-unfriendly) | MoE overhead kills perf |
| Codestral-22B | Dense | ~13 GB | ~16 GB | Likely yes | Unbenchmarked candidate |

## Recommended Routing (Mac)

```
Primary coder:      qwen3:14b (Metal GPU)
Fallback coder:     qwen2.5-coder:14b (Metal GPU)
Context trimmer:    qwen3:8b (Linux, always-on)
Coherence review:   qwen3:14b second pass
Fast tool use:      qwen3:8b
```

## Disk Cleanup: 67 GB Reclaimable

- qwen2.5-coder:32b-instruct-q4_K_M (18.9 GB)
- qwen2.5-coder:32b-instruct-q4_K_M-96k (18.9 GB)
- qwen3-coder:30b-a3b-q4_k_M (29.6 GB)

## Cloud Integration

30B-A3B belongs in the cloud quality gate chain, not local:
```
Local: qwen3:14b (gen) -> qwen3:14b (review)
  v promoted output only
Cloud: DeepSeek v4 flash -> Ring-2.6-1t @95% -> 30B-A3B shadow -> Kimi -> Claude merge
```

## Key Lessons

1. Never assume MoE = lighter on all hardware. Check whether target GPU supports expert parallelism.
2. Always benchmark on actual hardware — spec sheet RAM does not include OS overhead, Chrome, KV cache.
3. Parallel model loading on memory-constrained systems is a hard no. Sequential with explicit unload.
4. The best model is the one that fits with headroom. Marginal fits crash under real workloads.