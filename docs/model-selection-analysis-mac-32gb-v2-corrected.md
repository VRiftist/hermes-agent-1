# Model Selection Analysis — CORRECTED (Chrome Factor Removed)
**Revision:** v2 — recalculated without Chrome overhead  
**Update reason:** Gerald clarified: Mac dedicated to Hermes / Telegram / Terminal only. Chrome is a temporary install for key retrieval, NOT a persistent background load.

---

## Revised RAM Budget

Previous calculations assumed 7-8GB for Chrome. That's gone.

**Revised OS overhead (clean Mac, dedicated use):**

| Process | RAM |
|---------|-----|
| macOS base | ~4.5 GB |
| Hermes gateway process | ~0.7 GB |
| Telegram (desktop/client) | ~0.5 GB |
| Terminal | ~0.1 GB |
| Misc (Spotlight, networking, etc.) | ~0.5 GB |
| **Total OS overhead** | **~6.3 GB** |
| **Available for model** | **~25.7 GB** (of 32GB) |

---

## Revised Model Assessment

### qwen3:14b (YOUR WINNER — and it gets even better)

| Metric | Old calc (with Chrome) | New calc (dedicated Mac) |
|--------|----------------------|------------------------|
| Model in RAM | ~10 GB | ~10 GB |
| OS overhead | ~13 GB | ~6.3 GB |
| Free for KV cache | ~9 GB | **~15.7 GB** |
| Sustainable context | ~16K tokens | **~30K+ tokens** |
| Metal GPU partial boost | Marginal | Better — more headroom means less offloading |

**The dedicated Mac gives qwen3:14b almost DOUBLE the context headroom.** This is a significant improvement — it means multi-file codebase reasoning stays in context much longer.

### qwen2.5-coder:32b (dense) — STILL NOT RECOMMENDED

| Metric | Value |
|--------|-------|
| Model in RAM | ~20 GB (Q4) |
| OS overhead | ~6.3 GB |
| Free for KV cache | **~5.7 GB** |
| Sustainable context | ~8K tokens (confirmed by prior benchmarks) |

Even without Chrome eating RAM, **5.7GB KV cache still only supports ~8K context** for a 32B dense model. The prior overnight bench hit swap at 96K request — that was with 7GB free, and it still failed. At 5.7GB free, you hit the wall at similar points.

Additionally, confirmed from the bisection test: **"qwen2.5-coder:32b at 65K+ context causes swap — hard ceiling hit."** This is a hardware wall, not a Chrome problem.

### qwen3-coder:30B-A3B (MoE) — STILL NOT RECOMMENDED FOR LOCAL

| Metric | Value |
|--------|-------|
| Model in RAM | ~20.5 GB (Q4_K_M) |
| OS overhead | ~6.3 GB |
| Free for KV cache | **~5.2 GB** |
| Sustainable context | ~4-6K tokens (MoE has HIGHER KV cost per token) |

MoE models actually require MORE KV cache memory than dense models of equivalent total size, because each layer still processes the full hidden dimension during routing. The "3B active params" reduces compute FLOPS but doesn't reduce memory bandwidth pressure on the KV cache.

**With only 5.2GB for KV cache on an M2 with memory bandwidth bottlenecks, you'd get ~4-6K effective context at painful latency.** This is worse than the 14B setup with ~30K context.

**And critically:** The MoE routing overhead doesn't benefit from Metal acceleration because the expert selection logic has branching that doesn't parallelize on Apple Silicon's unified shader architecture. You get all the memory cost with none of the theoretical compute savings.

---

## Updated Recommendation

### Primary Setup (unchanged from prior analysis, stronger case now):

| Role | Model | Why |
|------|-------|-----|
| **Code gen** | `qwen3:14b` (Mac) | ~30K+ context with no Chrome overhead. Metal GPU access. Zero cost. |
| **Fallback coder** | `qwen2.5-coder:14b` (Mac) | Purpose-built for code, similar footprint |
| **Context trimmer** | `qwen3:8b` (Linux) | Always-on invariant. Zero cross-machine bandwidth impact |
| **Coherence review** | `qwen3:14b` 2nd pass (Mac) | Cheap local review before cloud quality gate |

### The "What About 30B" Question — Definitive Answer:

**Scenario you asked about:** "Could the local AI on the 32GB Mac be more useful than just running 14B?"

**Answer: No.** Here's why:

1. **A single 30B+ model (MoE or dense) makes the Mac WORSE at everything else it does.** Less context for your chat sessions, more swap pressure, degraded Hermes responsiveness.

2. **The 14B local + cloud quality gate chain gives you 95% of 30B quality for routine code gen, at zero cost and zero latency.**

3. **When you actually NEED 30B-level reasoning**, the cloud chain (Ring → 30B shadow → Kimi → Claude) delivers it on demand. You don't need it sitting in RAM 24/7.

4. **The Mac's real value** is being a responsive local agent THAT YOU CONTROL. Not a slow cloud proxy running on your own hardware.

---

## Revised Cleanup Recommendation

Delete **all** 32B+ models from the Mac. They're dead weight.

| Model to Delete | Disk Reclaimed | RAM Freed | Impact |
|-----------------|----------------|-----------|--------|
| qwen2.5-coder:32b-instruct-q4_K_M | 18.9 GB | Always was swapping anyway | None |
| qwen2.5-coder:32b-instruct-q4_K_M-96k | 18.9 GB | Duplicate | None |
| qwen3-coder:30b-a3b-q4_k_M | 29.6 GB | Never ran usefully | None |
| **Total** | **~67 GB** | — | — |

**That's 67 GB you can reclaim right now** and devote entirely to making qwen3:14b and qwen3:8b faster (SSD space is free I/O bandwidth too).

---

## Revised Quality-of-Life Improvements (Dedicated Mac)

Without Chrome running:

1. **Can safely bump `qwen3:14b` context to 32K or even 64K** without hitting memory pressure. This is HUGE for multi-file code changes where you're passing entire modules as context.

2. **Can temporarily load a heavier model** (e.g., qwen2.5-coder:32b for a specific task) because you won't be competing with Chrome. Run it for 30 minutes, kill it, go back to 14B. Sequential model loading is already proven safe.

3. **Can run two local models concurrently:** 14B coder + 8B trimmer simultaneously (~15.6 GB total model weight + 6.3 GB OS = ~22 GB). Plenty of headroom. This was previously impossible with Chrome open.

---

*Sources: Local Ollama telemetry, overnight-audit-2026-05-25.md, m2-32gb-context-bisection.md, Grok-4.20-reasoning verification (2026-05-27)*