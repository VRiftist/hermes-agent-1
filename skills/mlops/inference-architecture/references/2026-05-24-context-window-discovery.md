# 2026-05-24 — Context Window Discovery (from session 2026-05-24)

Hardware constraints define everything on this setup.

## Mac Mini M2 (32GB unified memory, no discrete GPU)

- Q4_K model weights consume most of the budget
- qwen2.5-coder:32b at 65K+ context causes swap — hard ceiling hit
- Best local model for context depth: qwen3:8b at 16K-24K tokens
- Bisection testing planned but deferred; cloud-first adopted for 32B workloads

| Model | Weights (Q4_K) | Eff. RAM Left | KV/Token | Max Context | Sweet Spot |
|-------|---------------|---------------|----------|-------------|------------|
| qwen3:8b | 5.2GB | ~20GB | ~0.63MB | ~24K | 8K-16K |
| qwen3:14b | 9.3GB | ~15GB | ~0.94MB | ~14K | 4K-8K |
| qwen2.5-coder:32b | 19.9GB | ~4GB | ~1.13MB | ~6K | ❌ unusable |

## Linux Box (RTX 3060 12GB VRAM, 45GB RAM, 8 cores)

- VRAM is the bottleneck, not system RAM
- qwen3:8b fits entirely in GPU memory → fast inference, long context
- qwen3:14b barely fits in 12GB VRAM (9.3GB weights + KV cache)
- 32B models too large for 12GB → CPU fallback, slower than Mac even
- Has `qwen3-14b-128k:latest` (native 128K context variant) — worth benchmarking

## The "Infinite Context" Implication

With local hardware maxing at ~24K tokens best case, the Memory Palace / active trimming / smart loading strategy isn't optional — it's the only path to long-session coherence.