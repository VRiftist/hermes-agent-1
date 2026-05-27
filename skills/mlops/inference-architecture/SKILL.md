---
name: inference-architecture
category: mlops
description: Strategies for multi-provider inference chains, local vs cloud model decisions, and context window optimization. Updated for 5-model local-first chain (2026-05-25).
tags:
  - "model-routing"
  - "cost-optimization"
  - "context-window"
  - "local-inference"
  - "hardware"
version: "1.2.0"
updated: "2026-05-25T20:00"
related_skills:
  - remote-access
  - hermes-agent
  - hermes-infrastructure
  - model-consulting
  - key-management
references:
  - references/hermes-dot-notation-bug.md
  - references/m2-32gb-context-bisection.md
  - references/session-2026-05-24-architecture.md
  - references/xai-model-names.md
  - references/2026-05-24-context-window-discovery.md
  - references/2026-05-24-parallel-benchmark-failure.md
  - references/2026-05-25-remote-context-window-verification.md
  - references/2026-05-25-metal-benchmark-plan.md
  - references/routing-decision-tree.md
  - references/2026-05-25-model-specs-confirmed.md
  - references/2026-05-27-model-selection-32gb.md
scripts:
  - scripts/bench_model.py
---

# Inference Architecture (Updated 2026-05-25)

Strategies for designing multi-provider inference chains, choosing between local and cloud models, and optimizing context windows for cost and reliability.

## When to Use This Skill

- Designing or updating a Hermes `config.yaml` provider chain
- Deciding whether a model should run locally (Ollama) or via cloud API
- Diagnosing context window / OOM issues on local hardware
- Optimizing cost by splitting work across cheap and expensive models
- Planning distributed Hermes control across multiple machines

---

## Core Principles

### 1. Local-First Architecture

Models run locally first. Cloud is an **upgrade path**, not a default.

```
User Request
    │
    ▼
┌─────────────────────────┐
│  mac-ollama:qwen3:14b   │  ← Try local first (free, 16K ctx, fast)
│  Linux:qwen3-14b-128k   │  ← Need more context? (free, 128K ctx)
│  deepseek-v4-flash      │  ← Need reasoning quality? ($0.14/1M)
│  grok-4.20-reasoning    │  ← Creative/architecture work ($1.25/1M)
│  ring-2.6-1t            │  ← Final quality gate ($0.88/1M)
└─────────────────────────┘
```

Put a model in the primary chain **only** when:
- The runner is stable (no OOM crashes, no unexpected stops)
- The context window has been bisection-tested at the target size
- The model serves a role cloud can't (zero-cost high-volume token work)
- The machine is confirmed powered on and accessible

**If a local model is unstable:** Keep configured but OUT of the active chain.

### 2. Deliberate Routing (Not Passive Fallback)

The routing decision tree determines model selection:

```
TASK RECEIVED
    │
    ├─ Classify: code / reasoning / research / creative / review / tool
    │
    ├─ Quick (<200 tokens)? → qwen3:8b (fastest)
    │
    ├─ Need specific capability?
    │   ├─ Code gen/review  → qwen3:14b or deepseek-v4-flash
    │   ├─ Deep reasoning   → deepseek-v4-pro or grok-4.20
    │   ├─ Long context     → linux qwen3-14b-128k
    │   ├─ Creative/syntax  → grok-4.20
    │   └─ Final review     → ring-2.6-1t
    │
    └─ Budget check: can we afford cloud?
        ├─ YES → route to best cloud match
        └─ NO → stay local
```

### 3. Multi-Tier Provider Chain

| Priority | Provider | Model | Context | Cost/1M tokens | Use Case |
|----------|----------|-------|---------|-----------------|----------|
| 1 | mac-ollama | qwen3:14b | 16K | Free | Default workhorse |
| 2 | mac-ollama | qwen3:8b | 32K | Free | Quick tasks |
| 3 | linux-ollama | qwen3-14b-128k | 128K | Free | Long analysis |
| 4 | deepseek | v4-flash | 32K | $0.14 in / $0.28 out | Code + reasoning |
| 5 | deepseek | v4-pro | 32K | $0.28 in / $0.56 out | Deep research |
| 6 | x-ai | grok-4.20-reasoning | 16K | $1.25 in / $10.00 out | Architecture, synthesis |
| 7 | openrouter | ring-2.6-1t | 16K | $0.88 in / $0.88 out | Quality gate |
| — | kimi | moonshot | — | — | Dead (awaiting key) |

**Why this order:**
- Free local models first (zero cost, zero latency)
- DeepSeek Flash: best cost/reasoning ratio for its price
- Grok: expensive but unmatched for creative/structural thinking
- Ring: always last for verification (balanced pricing)

## 4. Context Window Sizing by Hardware

#### Apple M2 (32GB unified, no discrete GPU)
*Close Chrome before heavy local inference — 20+ renderer processes consume ~4.8GB.*

| Model | Weights (Q4) | Eff. RAM | KV/Token | Max Context | Practical |
|-------|-------------|----------|----------|-------------|-----------|
| qwen3:8b | ~5GB | ~20GB | ~0.63MB | ~24K | **8K-16K** ✅ |
| qwen3:14b | ~9GB | ~15GB | ~0.94MB | ~14K | **4K-8K** ✅ |
| qwen3:8b Q3_K_M | ~3.5GB | ~22GB | ~0.47MB | ~32K+ | **16K-32K** ✅ |
| qwen2.5-coder:32b | ~20GB | ~4GB | ~1.13MB | ~3.5K | **2K-4K** ⚠ |
| qwen2.5-35B-A3B | ~12GB | ~16GB | ~1.3MB | ~12K | **8K-12K** ⚠ |

> ⚠ **32B on 32GB Mac:** Swaps aggressively. Only ~4GB free for KV cache. Use Linux or cloud for 32B workloads.
>
> 💡 **New option (2026-05-25):** qwen3:8b Q3_K_M on Mac gives ~3.5GB weights, leaving massive headroom for 32K+ context. Good for high-context tasks where 8b quality is sufficient.
>
> 💡 **Mac deep reasoning:** qwen2.5-35B-A3B is already on disk (~12GB). Add to routing table for deep thinking tasks where context size matters less than reasoning depth. Budget ~8K-12K context max.

#### Linux RTX 3060 (12GB VRAM, 45GB RAM)
*Currently offline — Hetzner retired, Digital Ocean droplet pending.*

| Model | VRAM Usage | Practical Context |
|-------|-----------|-------------------|
| qwen3:8b Q4_K_M | ~5GB VRAM | **16K** ✅ |
| qwen3:8b Q3_K_M | ~3.5GB VRAM | **32-64K** ✅ (aggressive) |
| qwen3-14b-128k | ~9GB VRAM | **8K-32K** ✅ |
| qwen3:14b | ~9GB VRAM | **8K-16K** ✅ |
| 32B models | >12GB VRAM | ❌ Use cloud |

> **VRAM audit (2026-05-25):** Linux's 12GB VRAM makes qwen3:8b Q3_K_M viable at 32-64K context — a major upgrade from the original 16K-only recommendation. Use this aggressive config only once DO droplet is provisioned with sufficient RAM.
>
> **Old recommendation corrected:** qwen3-14b-128k was the original Linux model. VRAM math confirmed qwen3:8b is the better fit — smaller weights leave more room for KV cache, enabling longer context windows. Decision: **qwen3:8b as primary Linux model** with Q3_K_M for aggressive workloads.

### 5. Provider Separation (Resilience)

The 3rd-tier model must use a **different API host** than the primary:

| Provider | API Host | Role | Survives if... |
|----------|----------|------|-----------------|
| OpenRouter | openrouter.ai | ring-2.6-1t | xAI is up |
| xAI | api.x.ai | grok-4.20 | OpenRouter OR DeepSeek down |
| DeepSeek | api.deepseek.com | v4-flash | OpenRouter OR xAI down |
| Local Ollama | localhost | qwen3 | Everything external down |

### 6. Anti-Patterns

- Running parallel benchmarks on 32GB hardware (causes GPU contention, OOM, process kills)
- Stacking fallback tiers by model size instead of failure mode coverage
- Setting 1M context as default "because it's supported" — every turn bills full context
- Assuming Linux Ollama port matches Mac (verify independently)
- Running unstable local models in the active chain
- Using cloud for tasks local handles fine (unnecessary cost)

### 7. Cost per Typical Turn (16K in, 4K out)

| Model | Total/Turn |
|-------|-----------|
| qwen3:14b (local) | $0.00 |
| qwen3-14b-128k (local) | $0.00 |
| deepseek-v4-flash | ~$0.02 |
| grok-4.20-reasoning | ~$0.10 |
| ring-2.6-1t | ~$0.08 |

Budget target: $5/day, $100/month.