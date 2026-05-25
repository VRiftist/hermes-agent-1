---
name: hermes-agent
category: autonomous-ai-agents
description: Configure, extend, and operate Hermes Agent in this environment — multi-machine, local-first, with deliberate model consulting, Pantheon personas, AKASHIC memory, skill engine, and security sandboxing.
tags:
  - "hermes"
  - "setup"
  - "configuration"
  - "multi-agent"
  - "local-first"
  - "model-switching"
  - "consult"
  - "merge"
  - "pantheon"
  - "akashic"
  - "skill-engine"
version: "3.5.0"
updated: "2026-05-25T23:30"
related_skills:
  - claude-code
  - codex
  - opencode
  - model-consulting
  - inference-architecture
  - hermes-infrastructure
  - hermes-gateway-ops
  - key-management
  - system-testing
references:
  - references/api-key-rotation.md
  - references/remote-ollama-networking.md
  - references/headless-linux-setup.md
  - references/session-diagnostics-2026-05-24.md
  - references/config-corruption-recovery.md
  - references/context-orchestrator-design.md
  - references/security-model.md
  - references/2026-05-25-architecture-overview.md
  - references/gateway-integration-design.md
  - references/2026-05-25-session-wiring-update.md
---

# Hermes Agent (v3.5 — Skill Engine Integration)

Hermes Agent runs in your terminal, messaging platforms, and IDEs. This documents this specific environment's setup and operating procedures.

## This Environment

**Hardware:**
- Mac Mini M2 32GB (LumenHubs-Mini, macOS 26.5) — primary interactive node
- Linux box @ 192.168.1.230 (user: gerald, RTX 3060, 45GB RAM) — GPU inference node (⬜ offline, Hetzner retired)

**Communication:** Telegram → @Gmano_bot

**5-Model Chain (all live 2026-05-25):**
1. mac-ollama:qwen3:14b (16K, free) — default
2. ~~linux-ollama:qwen3-14b-128k (128K, free) — long context~~ ⬜ Offline
3. deepseek:deepseek-v4-flash (32K, $0.14/M) — reasoning
4. x-ai:grok-4.20-reasoning (16K, $1.25/M) — creative/architecture
5. openrouter:ring-2.6-1t (**262K**, $0.88/M) — quality gate

**Dead:** kimi-coding (awaiting valid API key)

---

## Quick Reference

```bash
hermes                      # Interactive chat
hermes chat -q "question"   # Single query
hermes setup                # Setup wizard
hermes model                # Model/provider picker
hermes doctor               # Health check
hermes status --all         # Component status
```

---

## Foreground Discipline — Operating Agreement (v3.1)

### Absolute Rules

1. **Foreground = foreground.** No autonomous state changes during active conversation.
2. **Explicit decision points** before any destructive or infra-altering action.
3. **Announce before action.** Operator approves via Telegram before execution.
4. **Doc-first.** Progress written to files so it survives interruption.
5. **No autonomous spawning.** Subagents require explicit user request.
6. **No parallel benchmarks** on 32GB hardware without explicit per-instance approval.

### Decision Protocol

1. Every decision point requires explicit user approval — even small ones
2. Before starting anything time-consuming: state what, why, how long — then wait
3. **"When in doubt: STOP AND ASK."** No filling in gaps.
4. Full context at every point — complete picture before being asked to decide
5. User physically near a different machine → minimal tool use on current machine

### Model Switching Protocol

6. Model switches are **deliberate user decisions**, not automatic fallback
7. Agent proposes: "I'd like to route this to [model] using [pattern] — reason: [why]. Continue?"
8. Identity blocks injected at every model handoff point. No exceptions.
9. Coherence re-read required after every switch
10. Cost awareness: every model switch bills the full context window

### Incident Log

- **Parallel benchmark incident (2026-05-24):** 3 benchmarks simultaneously on 32GB Mac → GPU contention, OOM. Lesson: literal compliance with "not simultaneous."
- **Config corruption (2026-05-24):** Duplicate `fallback_providers: []` silently wiped the fallback chain. Lesson: validate configs actively.
- **Context orchestrator integration (2026-05-25):** Built, tested, awaiting gateway wiring. Lesson: self-contained modules can pass tests without live integration — don't confuse unit tests with operational readiness.
- **Dead cron cleanup (2026-05-25):** SSH tunnel cron to retired Hetzner box running every 5 minutes undetected. Lesson: When infrastructure is retired, delete ALL associated artifacts at the same time.
- **Wiki initialization (2026-05-25):** Karpathy-pattern llm-wiki created at `~/.hermes/wiki/`. Lesson: Knowledge base should be initialized alongside infrastructure.
- **13-layer audit (2026-05-25):** `full_infra_audit.py` + `full_selftest.py`. 9✅ 2⚠️ 0❌.
- **Skill Engine build (2026-05-25):** 7 JSON-defined skills loaded and tested. OpenClaw eliminated. Lesson: declarative skills > scripts for maintainability.

---

## Pantheon Framework (Added 2026-05-25)

| Persona | Model Preference | Role | Tool Access | Output Style |
|---------|-----------------|------|-------------|-------------|
| **Hermes** (Coordinator) | qwen3:14b, grok-4.20-reasoning | Operating mind — pragmatic, direct | All tools | Prose + structured plans |
| **Athena** (Critic) | deepseek-v4-pro, ring-2.6-1t | Analyst — skeptical, precise | Read, web, memory only | FINDING \|\| EVIDENCE \|\| RECOMMENDATION \|\| CONFIDENCE |

### Behavior Patterns

- **CONSULT:** Spawn Athena as sub-agent for specific analysis, then reintegrate
- **MERGE:** Adopt Athena's analytical mindset temporarily for a task phase
- **BECOME:** Full persona swap for one complete turn cycle
- **Always** re-read context-architect.md after any persona switch

### Use Triggers

```
Code review task          → Become Athena, route to deepseek-v4-pro
Architecture decision     → Become Athena, then Hermes+Athena dialectic
Debugging                 → Become Athena with deepseek-v4-pro
Creative writing/design   → Become Hermes with grok-4.20-reasoning
Final verification        → Always become Ring quality gate
```

---

## Security Model (4-Tier Access)

| Tier | Capabilities | Approval |
|------|-------------|----------|
| SAFE | Read ~/.hermes, web search, memory, logging, Telegram | Always |
| APPROVED | Write files, code execution, SSH, git, Ollama | Operator confirmation |
| RESTRICTED | Network shells, file deletion, package installs, new Telegram targets | Per-action approval |
| FORBIDDEN | Arbitrary binaries, direct config edits, key sharing, root/sudo | Never |

**Data rules:** PII hashed in logs, API keys masked (last 4 chars), HTTPS-only network, sandboxed execution with resource limits.

---

## Context Orchestrator (Added 2026-05-25)

The active context trimming system, solving the "infinite context" problem:

- **3-phase lifecycle:** Session Prep → Mid-Session Trim → Session End
- **6-tier priority:** T0=identity (never trim), T1=active task, T2=recent_high, T3=semantic, T4=background, T5=tool_output, T6=conversation (first to go)
- **12K token budget** — warning at 9K, hard trim to 6K
- **Auto-persist:** High-value trimmed blocks saved to SQLite before eviction
- **Location:** `scripts/context_orchestrator.py`

---

## AKASHIC Engine (Added 2026-05-25)

Multi-layer persistent memory replacing the 2,200-char limit:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Surface Palace | Compressed state | Top-of-context identity, active task, constraints |
| Episodic | SQLite | Timestamped events with importance scores |
| Semantic | SQLite | Concepts, relationships, extracted facts |
| Working | SQLite | Active session key-value store with expiry |
| Mythic | Quarterly narrative | Long-term patterns and stories |

**Location:** `~/.hermes/memory-palace/palace.db`
**Capacity:** Unlimited (vs. previous 2,200 char hard limit)

---

## ⭐ Skill Engine (NEW — 2026-05-25, replaces OpenClaw)

All skills are JSON-defined in `~/.hermes/skills/*.json` and executed by `scripts/skill_engine.py`. This **completely replaces OpenClaw** — no external skill system needed.

**Why this matters:** Previously we built skills as external scripts or through OpenClaw. Now everything lives inside Hermes as declarative JSON. The Flutter app, Cursor plugin, and CLI all hit the same `/v1/skills/execute` endpoint.

**Built-in skills:**

| Skill | Trigger | Model | Purpose |
|-------|---------|-------|---------|
| `daily_digest` | cron 08:00 | qwen3:14b | AI-generated daily review |
| `auto_tag` | on_create | qwen3:8b | Semantic tagging on new notes |
| `context_health` | on_request | qwen3:8b | Context window status |
| `archive_review` | cron 03:00 | qwen3:14b | Night Council maintenance |
| `memory_search` | on_request | qwen3:14b | Natural language memory query |
| `smart_compose` | on_request | qwen3:14b | AI writing assistance |
| `consolidate_notes` | on_request | qwen3:14b | Merge related notes |

**Adding custom skills:** Drop a JSON file into `~/.hermes/skills/`. No code changes. See `docs/hermes-api-spec-v1.md` for the JSON schema.

**Current status:** Skills load and execute correctly in sandbox. LLM calls will go live once gateway integration is complete.

---

## Infrastructure Scripts

All code lives in `~/.hermes/scripts/` — 13 modules, all self-testing:

| Module | Purpose | Key Feature |
|--------|---------|-------------|
| `skill_engine.py` | NEW — Skill execution engine | JSON-defined skills, caching, validation |
| `context_orchestrator.py` | Context lifecycle manager | 6-tier trim, 12K budget |
| `memory_palace.py` | SQLite persistent memory | Episodic + Semantic + Working |
| `hermes_logging.py` | JSONL structured logging | 4 log streams |
| `model_routing.py` | Deliberate model selection | Task classification, budgets |
| `circuit_breaker.py` | Dead model detection | 3-failure break, 5-min cooldown |
| `consult_merge.py` | Consult/merge/quality-gate | Protocol state machine |
| `akashic_engine.py` | Multi-layer memory wrapper | Ingest, recall, session activation |
| `hallucination_detector.py` | Output quality verification | Self-consistency scoring |
| `cost_tracker.py` | Spend monitoring | Per-model, budget alerts |
| `night_council.py` | Nightly review automation | 3:33 AM cron |
| `daemon_forge.py` | Templated sub-agent creation | 4 pre-built templates |
| `gateway_integration.py` | Gateway ↔ orchestrator bridge | 5 lifecycle hooks |

All tests passing: **42/42 unit tests**, 9/9 module integration, skill engine 7/7 skills loaded.

---

## Load This Skill

```
/skill hermes-agent
```

Loads identity block, operating agreement, capability matrix, and safety constraints into system prompt.