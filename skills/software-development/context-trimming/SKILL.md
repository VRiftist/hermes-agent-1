---
name: context-trimming
category: software-development
description: Active context window lifecycle management — 6-tier priority trimming, adaptive budgets, compression vs deletion, gateway + skill engine integration for Hermes Agent.
tags:
  - "context"
  - "trimming"
  - "memory"
  - "lifecycle"
  - "budget"
  - "compression"
  - "priority"
  - "resource-guard"
  - "skill-engine"
version: "1.5.0"
updated: "2026-05-25T23:45"
related_skills:
  - hermes-infrastructure
  - model-consulting
  - key-management
  - resource-guard
  - system-testing
  - hermes-agent
references:
  - references/2026-05-25-trimming-philosophy.md
  - references/context-orchestrator-integration.md
  - references/2026-05-25-session-wiring-update.md
  - references/gateway-integration-design.md
---

# Context Trimming — Active Window Lifecycle (v1.5)

The context window is not a passive buffer. It is actively managed with a 6-tier priority system, adaptive per-model budgets, and a hard cap that triggers trimming — not overflow.

## The Problem

LLM context windows are finite. Without active management:
- Identity and system instructions get pushed out
- Long conversations silently degrade model coherence
- Tool output accumulates and drowns the active task
- Every session starts cold, losing all prior work

## Architecture

### Three-Phase Lifecycle (`context_orchestrator.py`)

1. **Session Prep** — Loads identity + memory into context at conversation start
2. **Mid-Session Trim** — Monitors token usage, drops/compresses low-priority blocks when approaching budget
3. **Session End** — Persists high-value working state to SQLite for next-session recovery

### 6-Tier Priority System

| Tier | Content | Trim Behavior |
|------|---------|---------------|
| T0 | Identity (who we are, capabilities, constraints) | **NEVER trimmed** |
| T1 | Active task state (current goal, sub-tasks, decisions) | Trim last, compress first |
| T2 | Recent high-importance exchanges | Compress then drop |
| T3 | Semantic facts from Memory Palace | Dedup-check against Palace, then compress |
| T4 | Background/reference material | Compress aggressively |
| T5 | Tool output (raw results, logs) | **Compress + `[COMPRESSED]` tag** |
| T6 | Conversation history (oldest turns) | **Pure deletion** |

### Adaptive Budgets (per model)

| Model | Budget | Warning | Hard Trim |
|-------|--------|---------|-----------|
| Mac qwen3:14b | 12K tokens | 9K | 6K |
| Mac qwen3:8b | 12K tokens | 9K | 6K |
| Linux qwen3:8b | 8K tokens | 6K | 4K |
| DeepSeek v4-flash | 24K tokens | 18K | 12K |
| Ring-2.6-1t | 262K tokens | 196K | 131K |

### Compression vs Deletion — The Key Decision (CONFIRMED 2026-05-25)

**Hybrid approach — FINAL DECISION:**
- **T4 (background/reference):** COMPRESS — rephrase into summaries, preserve key details
- **T5 (tool output):** COMPRESS — rephrase + `[COMPRESSED]` tag, preserve actionable results
- **T6 (conversation history):** DELETE — pure deletion, lowest information density per token
- **T0 (identity) / T1 (active task):** NEVER deleted; T1 compress only if budget is critical
- Dedup against Memory Palace before compressing T3/T4

**Why hybrid?**
- Deletion is fast but loses nuance; compression preserves density at compute cost
- Tool output (T5) is highly compressible (structured, redundant)
- Conversation turns (T6) encode least unique information per token
- **Compression ≠ model-downsizing** — it removes redundant tokens from context, not replacing a model

### 8B Model Role (CONFIRMED 2026-05-25)

`qwen3:8b` is **NOT a context compressor**. Its role:
- **Fast local tool use** — terminal, filesystem, git (latency-critical)
- **General Q&A** — quick questions not needing deep reasoning
- **Emergency fallback** — when all cloud + larger local models unavailable
- **Budget-friendly routing** — for "quick" classified tasks (<200 tokens target)

Context trimming happens INDEPENDENTLY of model selection. The orchestrator trims regardless of which model is active.

### Interaction with Skill Engine (2026-05-25)

The skill engine and context orchestrator share the same gateway integration pathway:
- Skills execute WITHIN the context window assembled by the orchestrator
- `gateway_message_start()` builds context → skill executes → `gateway_trim_check()` evaluates → `gateway_message_end()` persists
- Skills do NOT bypass trimming — they inherit the same context budget
- High-importance skill outputs (e.g., `daily_digest` decisions) can be stored to Memory Palace before trim via the `memory_store` action

### Interaction with Resource Guard

The context orchestrator and resource guard (added 2026-05-25) interact:
- **Before `session_prep`**: Gate checks if the model passes RAM requirements
- **If blocked**: Fallback model is selected BEFORE context prep loads — no wasted tokens
- **Mid-session**: If trim drops below model's minimum viable context, flag to orchestrator for fallback

### Gateway Integration Status (2026-05-25)

`context_orchestrator.py` works standalone (all 3 phases tested ✅) but is **NOT yet wired** into the Hermes CLI message loop. Also NOT yet wired: `skill_engine.py` — its `llm_call` action returns simulated responses. Both need the same integration point.

Wiring plan (single change):
1. Gateway calls `gateway_message_start()` → context orchestrator builds context window
2. Gateway sends prompt to `skill_engine.execute()` OR `model_routing.select_model()` depending on intent
3. Each turn: `gateway_register_turn()` → `gateway_trim_check()`
4. Gateway calls `gateway_message_end()` → persist + cleanup

This means skills automatically inherit context trimming, memory palace, and model routing.

### Known Issues
- `skill_engine.py` `llm_call` action simulates responses — needs gateway integration to go live
- Compression function not yet implemented (architecture decided, code pending)
- `session_interrupt()` checkpoint mechanism proposed but not built
- Token counting uses 0.25×char estimate — should use model-specific tokenizers (tiktoken)
- T3 dedup against Palace uses naive matching — needs semantic similarity