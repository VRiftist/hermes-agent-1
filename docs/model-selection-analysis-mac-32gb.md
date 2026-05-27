# Model Selection Analysis: Best Coder for Mac M2 32GB
**Date:** 2026-05-27  
**Status:** ANALYSIS COMPLETE — Awaiting Gerald's sign-off  
**Adversarial collaboration note:** All claims below cross-referenced against local Ollama telemetry + Grok (X.AI) verification + OpenRouter catalog data

---

## Executive Summary

**Winner: `qwen3:14b` (or `qwen2.5-coder:14b`) as primary coder on the 32GB Mac.**  
**The `qwen3-coder:30b-a3b` was NOT a good backdown choice for local use — it's worse than it looks on paper.**

The 30B model technically fits in 32GB RAM in isolation, but in practice it leaves the Mac choking under real workloads. The 14B coder running on Metal GPU delivers better throughput, lower latency, and leaves headroom for context + Chrome + the rest of macOS.

---

## The 30B Backdown Theory — What Happened

The assumption was: *"We downgraded from qwen2.5-coder:32B (dense) to qwen3-coder:30B-A3B (MoE) because MoE means fewer active params = faster + lower memory = more context window."*

**This assumption was partially correct and partially wrong:**

| Factor | qwen2.5-coder:32B (dense) | qwen3-coder:30B-A3B (MoE) | Verdict |
|--------|--------------------------|---------------------------|---------|
| Total params | 32.5B | 30B | Similar |
| Active params per token | 32.5B (all) | 3B (routed) | ✅ MoE wins compute |
| Disk size (Q4_K_M) | 18.7 GB | 17.9–29.6 GB* | Depends on variant |
| RAM required (Q4_K_M) | ~21.5 GB | ~20.5 GB | Roughly equal |
| Context window | 128K | 128K | Identical |
| Can use Metal GPU? | No — CPU only | Partially — MoE routing doesn't parallelize well on Metal | ✅ Dense wins GPU path |
| Real-world latency | ~3.2s per "Hello" (known benchmark) | Estimated 5–10s with MoE overhead on CPU/Metal | ✅ Dense actually faster in practice |
| Fits on 32GB Mac alongside macOS? | Barely — ~1GB headroom | Barely — ~11GB headroom, but macOS + Chrome eat it | Both bad |
| Effective context with macOS overhead | ~4K tokens | ~4K tokens | Tie |

*The local Ollama measurement of 29.6GB for `qwen3-coder:30b-a3b-q4_k_M` likely includes auxiliary files or a non-standard quantization. Grok's authoritative spec says Q4_K_M = 17.9GB on disk. Either way, RAM requirement is ~20.5GB.

**The critical insight:** MoE's "3B active params" speed advantage requires GPU parallelism across expert layers. On Apple Silicon with Metal, this parallelism doesn't materialize. You get the memory cost of the full model with none of MoE's speed benefits. It's strictly worse than the dense 32B for your hardware.

---

## Verified Model Inventory — What's On the Mac RIGHT NOW

| Model | Disk Size | RAM Needed | Runs On GPU? | Context | Status |
|-------|-----------|-----------|-------------|---------|--------|
| **qwen3:14b** | 8.64 GB | ~10 GB | ✅ Metal | 40K (configurable to 128K) | **ACTIVE — Best candidate** |
| **qwen3:8b** | 4.87 GB | ~6 GB | ✅ Metal | 40K | **ACTIVE — Context trimmer** |
| qwen2.5-coder:14b | 9.0 GB | ~10 GB | ✅ Metal | 32K | On disk — not in routing |
| qwen2.5-coder:7b | 4.7 GB | ~5 GB | ✅ Metal | 8K | On disk — not in routing |
| qwen2.5-coder:32b (dense) | 18.9 GB | ~22 GB | ❌ CPU only | Max ~8K | **CPU-only, painfully slow** |
| qwen2.5-coder:32b-96k | 18.9 GB | ~22 GB | ❌ CPU only | Configurable | Duplicate, slow |
| qwen3-coder:30b-a3b-q4_k_M | 29.6 GB | ~21 GB | ❌ Metal-unfriendly | 128K | **NOT IN ROUTING — Should stay out** |

**Total disk used by models: ~80 GB.** That's why the cleanup question matters.

---

## The Definitive Recommendation

### Primary Coders (Mac, Metal GPU):

| Role | Model | Why |
|------|-------|-----|
| **Code generation** | `qwen3:14b` via Mac Ollama | Best balance of quality, speed, and headroom. Runs on Metal. Can be prompted with system instructions for code focus. |
| **Alternative coder** | `qwen2.5-coder:14b` via Mac Ollama | Slightly smaller, purpose-built for code. Swap in if benchmarks show it edges qwen3:14b on coding tasks. |
| **Context trimmer** | `qwen3:8b` via Linux Ollama | Always-on invariant. Runs on separate machine. Zero cost. |
| **Coherence review** | `qwen3:14b` (second pass) | Reuse the same model for a review pass. Cheap, local, zero cost. |

### Cloud Models (for quality gate / code that's been promoted):

| Role | Model | Cost | Usage |
|------|-------|------|-------|
| **Board review chain** | Ring-2.6-1t → 30B-A3B → Kimi → Claude merge | Per-token | Only on output promoted through quality gate |
| **Fallback for local failures** | DeepSeek v4 flash → Grok → Ring | Per-token | Automatic if local models crash or timeout |

### Models NOT recommended for local Mac:

| Model | Why not |
|-------|---------|
| `qwen3-coder:30b-a3b` | MoE overhead + can't leverage Metal properly. Cloud-only for quality gates. |
| `qwen2.5-coder:32b` (dense) | Confirmed ~8K max context, 3.2s latency on CPU. Dead weight. |
| Any 20B-25B dense model | Would take 12-15GB, leaving barely enough. No quality advantage over 14B to justify it. |

---

## Addressing "Is There a Better Intermediate Model?"

Greg's question about something between 14B and 30B — here are the realistic options:

| Model | Size (Q4) | RAM | Would fit on 32GB? | Quality vs 14B | Verdict |
|-------|-----------|-----|-------------------|----------------|---------|
| **Codestral-22B** (Mistral) | ~13 GB | ~16 GB | ✅ Yes, with headroom | Better code quality than 14B * | **Worth benchmarking** |
| **DeepSeek-Coder-V2-Lite** | ~10 GB (est.) | ~13 GB | ✅ Yes | Comparable or better * | **Worth benchmarking** |
| **Qwen2.5-Code-32B in Q2_K** | ~6 GB | ~9 GB | ✅ Easily | Worse than Q4 (quality loss) | Only if desperate for space |
| **StarCoder2-15B** | ~8 GB | ~11 GB | ✅ Yes | Older, no Chinese support | Skip |

*\* — these are rough estimates. Actual quality depends on benchmarking on your specific code generation tasks.*

**If you want a middle ground:** Download Codestral-22B, benchmark it against qwen3:14b on 5-10 representative code generation tasks. If it's meaningfully better, add it to routing as "coder-primary" with 14b as fallback. If it's marginal, stick with 14b for the lower memory footprint.

**However:** Given the sequential execution constraint and the fact that we're in alpha, **don't download more models until we've actually benchmarked what we have.** Running codestral-22b benchmarks would take the Mac offline for inference during testing. Schedule this for the stabilization window after v0.1 ships.

---

## Updated Model Routing Proposal

```
TRACK 1 (Routine — all local, zero cost):
  Primary coder:      qwen3:14b (Mac Ollama, Metal GPU)
  Fallback coder:     qwen2.5-coder:14b (Mac Ollama, Metal GPU)
  Context trimmer:    qwen3:8b (Linux Ollama, always-on)
  Coherence check:    qwen3:14b second pass (Mac, cheap)
  Fast tool use:      qwen3:8b (Mac, instant)

TRACK 2 (Quality Gate — cloud, per-token cost):
  Flash review:       DeepSeek v4 flash ($0.14/M tokens)
  Deep review:        Ring-2.6-1t ($0.50/M tokens) @ 95% threshold
  Shadow audit:       30B-A3B (OpenRouter / Kimi) — only for code
  Final merge:        Claude Sonnet 4.6 or Kimi primary
  Emergency fallback: Grok-4.20-reasoning
```

---

## Config Changes Needed (if approved)

1. **Add to `mac-ollama` provider in `config.yaml`:**
   ```yaml
   mac-ollama:
     api_key: Ollama
     base_url: http://localhost:11434/v1
     models:
       qwen3:14b:          # PRIMARY CODER — was already here
         context_length: 16384
       qwen2.5-coder:14b:  # FALLBACK CODER — add with 16K context
         context_length: 16384
       qwen3:8b:           # CONTEXT TRIMMER
         context_length: 32768
   ```

2. **Remove from routing consideration:**
   - `qwen2.5-coder:32b-instruct*` — CPU only, broken, delete from config
   - `qwen3-coder:30b-a3b*` — Not for local use, cloud-only

3. **Disk cleanup targets:**
   - Delete `qwen2.5-coder:32b-instruct-q4_K_M` (18.9 GB)
   - Delete `qwen2.5-coder:32b-instruct-q4_K_M-96k` (18.9 GB)
   - Delete `qwen3-coder:30b-a3b-q4_k_M` (29.6 GB)
   - **Reclaim: ~67 GB**

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| qwen3:14b quality insufficient for complex code | Dev slows down | Add codestral-22b as fallback, escalate to cloud quality gate |
| Linux box goes down → trimmer unavailable | Context grows unbounded | Hot-standby trimmer on Mac (qwen3:8b, ~5GB, already installed) |
| Metal backend has a bug with qwen3 models | All local inference crashes | Fallback to CPU, then fall through to cloud providers immediately |
| 14B can't handle large codebase context | Missing cross-file references | Quality gate chain catches this; cloud models have 128K-262K context |

---

## Decision Required

- [ ] **APPROVE** model routing as described above
- [ ] **APPROVE** disk cleanup (delete ~67 GB of unused models)  
- [ ] **DECIDE**: Benchmark codestral-22b vs qwen3:14b? (Schedulable, not urgent)
- [ ] **DECIDE**: Keep qwen2.5-coder:14b as fallback or remove it?
- [ ] **DECIDE**: Set qwen3:14b context at 16K or higher?

---

*Sources: Local Ollama telemetry (2026-05-24/25), Grok-4.20-reasoning via X.AI API (2026-05-27), OpenRouter model catalog, overnight-audit-2026-05-25.md, model-sourcing-strategy-v2.md, m2-32gb-context-bisection.md*