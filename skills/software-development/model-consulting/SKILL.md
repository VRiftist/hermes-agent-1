---
name: model-consulting
category: software-development
description: Deliberate model routing, consult/merge/become patterns, and cross-model coherence management for multi-provider agent workflows.
tags:
  - "model-routing"
  - "consult-merge"
  - "multi-model"
  - "deliberate-switching"
  - "resource-guard"
version: "2.4.0"
updated: "2026-05-25T23:00"
related_skills:
  - hermes-agent
  - hermes-infrastructure
  - inference-architecture
  - subagent-driven-development
  - context-trimming
  - resource-guard
references:
  - references/2026-05-25-model-switching-framework.md
  - references/2026-05-25-forced-model-routing.md
  - references/2026-05-25-api-key-validation-results.md
  - references/2026-05-25-coherency-audit.md
  - references/2026-05-25-model-specs-confirmed.md
---

# Model Consulting & Merging (v2.2 — 2026-05-25 Rebuild)

Three deliberate model-switching patterns. These are **not** fallback (reactive). These are **active decisions** you make during work: "this task needs X model → route to X."

## Current 5-Model Chain (All Verified 2026-05-25)

**Tier 2 (Heavy):** `linux-ollama:qwen3:8b` — 16K context, free, Linux RTX 3060 *(offline — Hetzner retired 2026-05-25, DigitalOcean droplet pending. Recommended: qwen3:8b Q4_K_M ~9GB VRAM, ~30-40 t/s)*
**Tier 2b (Mac Aggressive):** `mac-ollama:qwen3-coder:30b-a3b` — 16K context, free, already on disk (18.6GB). Dedicated reasoning model for consult/merge phases. ✅ NOW INCLUDED in routing matrix and model_routing.py config.
**Tier 3 (Reasoning):** `deepseek:v4-flash` — 32K context, $0.14/1M in ✅
**Tier 4 (Creative):** `x-ai:grok-4.20-reasoning` — 16K context, $1.25/1M in ✅
**Tier 5 (Quality Gate):** `openrouter:ring-2.6-1t` — **262K** context, $0.88/1M in ✅
**Dead:** kimi-coding (moonshot, 401 — cold standby)

> **Key discovery:** Ring's actual context is **262K**, not the 16K on OpenRouter's model card. Discovered via API discovery. This makes Ring viable as a quality gate for very long conversations.

> **New:** qwen3-coder:30b-a3b is already on disk (18.6GB on Mac). Add to `MODELS`, `CATEGORY_BEST`, and `PREFERENCE_ORDER` in `model_routing.py` for dedicated reasoning tasks.

**Fallback chain (deliberate, local-first, diverse failure domains):**
`mac qwen3:14b → mac qwen3-coder:30b-a3b → linux qwen3:8b → deepseek-v4-flash → grok-4.20-reasoning → ring-2.6-1t`

## Merge Routing Matrix (Task Phase → Model + Pattern)

| Task Phase | Best Model | Pattern | Rationale |
|-----------|------------|---------|-----------|
| Architecture/planning | grok-4.20-reasoning | MERGE | Structural thinking, cross-system design |
| Code generation | mac-ollama:qwen3:14b | MERGE | Free, fast, sufficient for most code |
| Complex code review | deepseek-v4-flash | CONSULT | Strong logic analysis, cheap cost |
| Code-heavy deep review | mac-ollama:qwen3-coder:30b-a3b | CONSULT | Local, free, A3B reasoning depth |
| Debugging | deepseek-v4-flash | CONSULT | Precise error identification, stack traces |
| Editorial/critique | grok-4.20-reasoning | CONSULT | Sharp analytical perspective |
| Final verification | openrouter:ring-2.6-1t | QUALITY_GATE | Always last step before delivery |
| Long research | linux-ollama:qwen3:8b Q3_K_M | MERGE | 32-64K context fits large source material (aggressive config when DO provisioned) |
| Quick tasks (<200 tokens) | mac-ollama:qwen3:8b | DIRECT | Fastest local model, no overhead |
| Parallel independent work | Multiple available | DELEGATE | Isolated sub-agents, concurrent |

### Escalation triggers:
- **Context overflow**: Current model can't fit the conversation → next tier up
- **Quality gap**: Output keeps needing revision → stronger model
- **Capability need**: Need tool use/reasoning the current model can't do
- **Cost is justified**: Task value exceeds cost of higher tier
- **Resource guard blocks current model**: Automatically fall to next candidate

## Three Patterns

### Pattern 1: CONSULT
**What:** Bring in a specialist to advise. The primary model continues executing.

**Use when:**
- Task requires expertise the active model lacks (security review, architecture critique)
- You need a second opinion on reasoning before committing
- Debugging complex issues where fresh eyes help
- The active model is producing incoherent or low-quality output

**How it works:**
1. Active model identifies it needs specialist input
2. Routes to consultant model with **focused context** (not full history)
3. Consultant produces analysis/recommendation only
4. Active model incorporates findings and continues

**Key constraint:** The consultant does NOT produce final output. It advises only.

### Pattern 2: MERGE (Become)
**What:** Temporarily adopt a different model for the current task phase, then switch back.

**Use when:**
- Switching from analysis mode → code generation mode
- Needing different context window characteristics
- Task phase matches a specific model's strengths

**How it works:**
1. Identify which model's strengths the current phase needs
2. Route the current task to that model
3. That model produces output in its own style
4. Route back to primary model for integration

**Always inject an identity block at model handoff:**
```
[IDENTITY]
Agent role: Hermes Agent — orchestrator
Human: lumenhubai (Mac M2 + Linux RTX3060)
Current phase: [PHASE]
Active objective: [OBJECTIVE]
Powers: [capabilities available]
Constraints: [what you cannot do]
```

### Pattern 3: FULL DELEGATE
**What:** Hand off an entire independent sub-task to a different model/provider with isolated context.

**Use when:** Workstreams are independent and don't share context, or parallelizable heavy work.

**How it works:**
1. Decompose work into independent tasks
2. Route each to appropriate model (via delegate_task)
3. Each subagent runs in isolated context
4. Results merge back into primary session

## Context Coherence Rules (Non-Negotiable)

### 1. Top-of-Context Identity Block
First entries in any model's context must be the identity block. Injected EVERY time a model switches.

### 2. Context Handoff Protocol
When switching models:
1. Summarize what's been done (3-5 bullets max)
2. State the current question/decision needed
3. Explicitly say what the new model should focus on
4. Do NOT copy-paste full conversation history

### 3. Coherence Re-read
After any model switch, the receiving model must:
1. Read the summary from previous model
2. Confirm understanding ("continuing from X, focusing on Y")
3. Ask clarifying questions if anything is ambiguous

### 4. Post-Switch Re-sync
After merge/become, the primary model must re-read context-architect.md to maintain identity coherence.

## Anti-Patterns

- **Passive-only fallback:** Switching only when a key breaks (was the old default — fixed)
- **No context handoff:** Throwing the full conversation at a new model
- **Identity drift:** Model forgets who it is after switching (solved by identity block)
- **Switching without purpose:** "Let me try Grok instead" with no reason why
- **Using biggest/most expensive model as default:** Often less coherent than smaller focused models
- **Ignoring cost:** Every switch bills full context window. Plan to minimize total tokens
- **File-size hallucination:** Assume model X's rated context = usable context. Deduct ~30% for system overhead.
- **Linux offline assumption:** Any routing that assumes linux-ollama availability will silently fall back to next tier. Monitor health chain.
- **SSH breakage cascade:** If Mac SSH is unreachable, cross-platform debugging halts. Keep `remote-access` skill current.
- **qwen3-coder:30b-a3b ON DISK but not routed:** Model is at 18.6GB on Mac. ✅ FIXED 2026-05-25 — now included in routing matrix, MODEL_DETAILS, CATEGORY_BEST, and PREFERENCE_ORDER in `model_routing.py`. Verify with `select_model("code")` test.
- **Windows/macOS security:** `redact_pii: false` in config + verbose logging = potential data leak. Needs mitigation.

## Decision Flow

```
TASK RECEIVED
    │
    ├─ Classify: code / reasoning / research / creative / review / tool
    │
    ├─ Quick task (<200 tokens, obvious path)?
    │   └─ YES → Route directly to qwen3:8b, no consult needed
    │   └─ NO  → Continue
    │
    ├─ Resource gate check (if model is guarded):
    │   ├─ PASS → Proceed
    │   └─ BLOCK → Next candidate in chain
    │
    ├─ Impact assessment: Destructive? Expensive? Irreversible?
    │   └─ YES → Athena review REQUIRED before action
    │   └─ NO  → Hermes handles, Athena optional
    │
    ├─ Invoke Consult (if complex):
    │   ├─ Spawn sub-agent with Athena persona
    │   ├─ Sub-agent returns structured critique
    │   └─ Hermes synthesizes critique into action plan
    │
    ├─ Invoke Merge/Become (if persona shift needed):
    │   ├─ Prepend persona system prompt
    │   ├─ Switch model preference
    │   ├─ Execute in persona mode
    │   └─ Re-read context-architect.md to re-sync
    │
    └─ Final Quality Gate:
        ├─ Route to Ring for verification
        └─ Ring confirms or flags issues before delivery
```

## Loading This Skill

```
/skill model-consulting
```

Load before any session that involves multi-model orchestration.