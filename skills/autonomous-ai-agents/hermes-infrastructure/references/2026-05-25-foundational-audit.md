# Foundational Audit — 2026-05-25

## What Happened
Full audit of every assumption, parameter, and decision in the Hermes foundational framework. Examined token budgets, compression strategy, VRAM math, model chain correctness, and credential status. Produced 14 corrective changes.

## Key Findings

### Corrections Made
| # | Area | Old State | Corrected State | Impact |
|---|------|-----------|-----------------|--------|
| 1 | Token budget | Fixed 12K for all models | Adaptive: Mac 12K, Linux 8K, DeepSeek 24K, Ring 32K+ | Ring can now actually review full context |
| 2 | Compression strategy | Pure deletion | Hybrid: T5 compress 10%, T4 extract semantic, T6 delete, T3 dedup | ~60-70% context reduction vs ~90% with pure delete |
| 3 | Linux model | qwen3-14b-128k / 128K | qwen3:8b / 16K (safe) or Q3_K_M / 32-64K (aggressive) | Fits in 12GB VRAM with headroom |
| 4 | Linux role name | "Long-context batch work" | "Fast local fallback" | Accurate — 8B for speed, not 14B for context |
| 5 | Ring context window | Assumed 16K | Confirmed 262K via API discovery | Quality gate viable for full conversation history |
| 6 | DeepSeek key | Old key never activated on platform | New key `sk-bca71f6fd...` pre-activated | HTTP 200 on both chat + models endpoints |
| 7 | Mac 35B-A3B | Not in routing table | Added at ~12GB weights, 8K-12K practical context | Deep reasoning option for Mac |

### VRAM Audit Results
- **Mac M2 (32GB unified):** qwen3:14b uses ~9GB + 3GB KV@16K = safe at 4-8K context. 35B-A3B uses ~12GB weight, ~12GB KV@16K = marginal, use ≤12K.
- **Linux RTX 3060 (12GB VRAM):** qwen3:8b Q4_K_M = 5GB + 4GB KV@16K = 9GB ✅. Q3_K_M = 3.5GB + 2.4GB KV@32K = 6GB ✅. 14B = 9GB + 3GB KV = 12GB, no headroom ⚠.

### Compression Strategy (Documented, Not Yet Coded)
- T0 (identity): Never touched
- T1 (active task): Never touched
- T2 (recent important): Never touched
- T3 (semantic): Dedup against memory palace, delete if duplicate
- T4 (background): Extract key facts → semantic memory, then delete
- T5 (tool output): Compress to ~10% summary, tag `[COMPRESSED]`
- T6 (old conversation): Pure delete (reconstructable from palace)

### Token Counting Warning
The 0.25×character estimate used for trim decisions is too rough. Actual token counts vary 2-4× depending on language and vocabulary. Should use model-specific tokenizers for accurate trim decisions.

## Deliverables This Session
1. `documentation/hermes-foundational-framework.md` — 31KB canonical framework v1.0
2. `context-architect.md` — corrected model chain, updated roles
3. All 4 skill library entries updated with audit findings
4. `key_guardian.py` — DeepSeek + OpenRouter model names fixed
5. Memory palace — 18 framework decisions logged (64KB DB, 17 episodes, 27 facts)

## Open P0 Items
1. Wire `context_orchestrator.py` into gateway message processing loop
2. Re-run `build_foundational_framework.py` pipeline (timed out at 137s)
3. Implement hybrid compression in `context_orchestrator.py`
4. Implement adaptive token budgets in gateway runtime