---
name: hermes-infrastructure
category: autonomous-ai-agents
description: The complete infrastructure layer for Hermes Agent — persistent memory, structured logging, deliberate model routing, circuit breakers, hallucination detection, cost tracking, nightly reviews, daemon spawning, and security sandboxing.
tags:
  - "infrastructure"
  - "memory"
  - "logging"
  - "routing"
  - "circuit-breaker"
  - "pantheon"
  - "akashic"
  - "cost-tracking"
  - "security"
version: "1.4.0"
updated: "2026-05-25T23:30"
related_skills:
  - hermes-agent
  - model-consulting
  - inference-architecture
  - system-testing
references:
  - references/2026-05-25-foundational-audit.md
  - references/2026-05-25-architecture-overview.md
  - references/2026-05-25-coherency-audit.md
  - references/project-list-and-status.md
  - references/routing-decision-tree.md
  - references/security-model.md
  - references/gateway-integration-design.md
  - references/2026-05-25-session-wiring-update.md
---

# Hermes Infrastructure Layer

The complete infrastructure layer powering the consult/merge protocol, context lifecycle management, persistent memory, structured logging, deliberate model routing, circuit breakers, hallucination detection, cost tracking, nightly reviews, daemon spawning, and security sandboxing.

## ⚠ Current Status (2026-05-25): Phase Shift — BUILD → USE & TUNE

The foundation is **structurally sound but operationally disconnected**. Individual components work in isolation; wiring between them is incomplete. See `documentation/coherency-audit-20260525.md` for 30-item audit with prioritized fixes.

## What This Is

12 Python modules + 2 policy documents + 1 protocol definition replacing Hermes' fragile, in-memory, stateless operation with a persistent, auditable, deliberately-routed multi-model agent system.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HERMES AGENT                          │
│                    (User Interface)                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │         CONSULT/MERGE ORCHESTRATOR                │   │
│  │  (Task classification → Model routing → Protocol) │   │
│  └──────────┬───────────┬───────────┬────────────────┘   │
│             │           │           │                     │
│    ┌────────▼───┐ ┌─────▼─────┐ ┌───▼───────────┐       │
│    │ Memory     │ │ Structured│ │ Model Routing │       │
│    │ Palace     │ │ Logging   │ │ + Circuit     │       │
│    │ (SQLite)   │ │ (JSONL)   │ │   Breaker     │       │
│    └────────────┘ └───────────┘ └───────────────┘       │
│                                                          │
│  ┌──────────────┐ ┌───────────┐ ┌──────────────────┐    │
│  │ Hallucination│ │ Cost      │ │ Night Council    │    │
│  │ Detector     │ │ Tracker   │ │ (Cron Job)       │    │
│  └──────────────┘ └───────────┘ └──────────────────┘    │
│                                                          │
│  ┌──────────┐ ┌─────────────┐ ┌────────────────────┐    │
│  │ Akashic  │ │ Daemon      │ │ Security Model     │    │
│  │ Engine   │ │ Forge       │ │ (4-Tier Access)    │    │
│  └──────────┘ └─────────────┘ └────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SKILL ENGINE *(NEW — replaces OpenClaw)*         │   │
│  │  JSON-defined skills, cached, param-validated    │   │
│  │  7 built-in: daily_digest, auto_tag, context_     │   │
│  │  health, archive_review, memory_search,           │   │
│  │  smart_compose, consolidate_notes                  │   │
│  └──────────┬───────────┬───────────┬────────────────┘   │
│             │           │           │                     │
│             ▼           ▼           ▼                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  CONTEXT ORCHESTRATOR *(not yet in gateway loop)* │   │
│  │  3-phase lifecycle: prep → mid-trim → session-end │   │
│  │  6-tier priority (T0-T6), adaptive budgets       │   │
│  └──────────┬───────────┬───────────┬────────────────┘   │
│             │           │           │                     │
│             ▼           ▼           ▼                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │           PANTHEON PERSONAS                      │   │
│  │  Hermes (Coordinator) + Athena (Critic/Verifier) │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│         5-MODEL CHAIN (local-first, verified 2026-05-25) │
│  Mac qwen3:14b (16K) → Linux qwen3:8b (16K)*            │
│  → DeepSeek v4-flash (32K) → Grok-4.20 (16K)            │
│  → Ring-2.6-1t (262K)                                   │
│  * Linux offline (Hetzner retired, DO pending)           │
└─────────────────────────────────────────────────────────┘
```

## Module Summary

### Skill Engine — `skill_engine.py` *(NEW — 2026-05-25, replaces OpenClaw)*
JSON-defined action chain executor. Skills are `.json` files in `~/.hermes/skills/` with declarative triggers, params, and multi-step execution plans.

**Key features:**
- 3 trigger types: `cron`, `on_event`, `on_request`
- Built-in param validation with type coercion
- Result caching with configurable TTL per skill
- Template variable resolution (`{{param_name}}`)
- Conditional branching and wait actions
- All LLM calls route through Hermes' model routing (not external)
- `POST /v1/skills/execute` API endpoint for all clients

**Built-in skills:**

| Skill | Trigger | Model | Purpose |
|-------|---------|-------|---------|
| `daily_digest` | cron 08:00 | qwen3:14b | AI-generated daily review |
| `auto_tag` | on_create | qwen3:8b | Semantic tagging on new notes |
| `context_health` | on_request | qwen3:8b | Context window status report |
| `archive_review` | cron 03:00 | qwen3:14b | Night Council maintenance |
| `memory_search` | on_request | qwen3:14b | Natural language memory search |
| `smart_compose` | on_request | qwen3:14b | AI writing assistance |
| `consolidate_notes` | on_request | qwen3:14b | Merge related notes into knowledge |

**Custom skills:** Drop a JSON file into `~/.hermes/skills/` — no code changes needed for simple workflows.

**Current limitation:** `llm_call` action returns simulated responses in sandbox. Requires gateway integration to reach real models.

### Persistent Memory — `memory_palace.py`
SQLite database replacing the 2,200-char in-memory limit. Three layers:
- **Episodic:** Timestamped events with importance scores, tags, expiry
- **Semantic:** Concept relationships and extracted facts with confidence
- **Working:** Active session key-value store with time-based expiry
- Auto-prune for expired entries. Location: `~/.hermes/memory-palace/palace.db`
- **⚠ Known issue:** `_extract_facts()` is naive (newline split + char slice) — produces garbage from code/structured content. Recommendation: disable auto-extraction and only store manually tagged facts until an LLM-based extractor is added.
- **⚠ Known issue:** DB has no encryption at rest and no permissions guard beyond filesystem. Add `chmod 600` on creation; consider SQLCipher.

### Gateway Integration Layer — `gateway_integration.py` *(NEW — 2026-05-25)*
Bridge module connecting `context_orchestrator.py` to the Hermes CLI message processing loop. Exposes five public functions the gateway should call at each lifecycle point:
- `gateway_message_start(user_input, task_category)` → prepends identity + memory context
- `gateway_register_turn(role, content)` → logs each exchange
- `gateway_register_tool(tool_name, tool_result)` → captures tool outputs
- `gateway_trim_check(current_tokens)` → triggers mid-session trimming
- `gateway_message_end(summary)` → persists state + runs maintenance

**⚠ Self-tested but NOT YET INVOKED by the CLI message loop.** Integration requires modifying the gateway's message handling entry point to call these lifecycle hooks.

### Structured Logging — `hermes_logging.py`
JSONL audit trail for every operation. Location: `~/.hermes/logs/hermes_*.jsonl`

### Model Routing — `model_routing.py`
Deliberate model selection (not passive failover):
- Task classification: code / reasoning / research / creative / review / tool
- Health-aware, budget-aware, context-aware
- Routing logic: Local first → cheap cloud → expensive cloud → quality gate

### Circuit Breaker — `circuit_breaker.py`
Automatic dead model detection and failover:
- 3 consecutive failures → mark model dead for 5-minute cooldown
- Auto-retry after cooldown expires
- Health persistence to `~/.hermes/logs/model_health.json`

### Resource Guard — `resource_guard.py` *(New — 2026-05-25)*
Pre-launch gate preventing heavyweight model launches when system resources insufficient:
- RAM checks against per-model thresholds
- macOS page size parsed dynamically from vm_stat
- Safari XPC helpers filtered
- Silent mode in routing
- JSON logging

### Foundation Decision Framework *(New — 2026-05-25)*
All 5 foundational questions decided and stored to Memory Palace.

### Consult/Merge Protocol — `consult_merge.py`
Full protocol state machine with three patterns: CONSULT, MERGE/BECOME, FULL DELEGATE.

### AKASHIC Engine — `akashic_engine.py`
Multi-layer memory wrapper: Surface Palace, Ingest, Recall, Session activation, Maintenance.

### Hallucination Detection — `hallucination_detector.py`
Output quality verification with risk level scoring.

### Cost Tracking — `cost_tracker.py`
Real-time spend monitoring with budget alerts.

### Night Council — `night_council.py`
Automated nightly review (designed for 3:33 AM cron).

### Daemon Forge — `daemon_forge.py`
Templated sub-agent creation system with pre-built templates.

## Verified Status (2026-05-25): Phase Shift

- ✅ 13-layer infrastructure audit completed — **9✅ 2⚠️ 0❌**
- ✅ All self-test suites passing — 42/42 unit tests + 9/9 module integration
- ✅ All 3 ACTIVE cloud API keys verified live
- ✅ Mac Ollama: qwen3:14b responding; qwen3-coder:30b-a3b on disk
- ⚠ Linux Ollama: selected, Hetzner retired, DO pending
- ✅ Memory palace operational (90 episodes, 66 facts)
- ✅ Consult/Merge protocol validated
- ✅ **Skill Engine built and loaded — 7 skills active** *(NEW)*
- ✅ Cost tracker initialized
- ✅ Night Council generating reports
- ⚠ Context orchestrator: standalone ✅, gateway integration P0
- ⚠ Telegram alerting: credentials missing from .env

## Open Items

### P0 — Blocking
1. **Wire context_orchestrator + skill_engine into gateway message loop** — single integration point needed for both
2. **Add TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID to .env**
3. **Merge dual health tracking into single source of truth**

### P1 — This Week
4. Add `qwen3-coder:30b-a3b` to routing config
5. Fix key_guardian: test actual model slugs
6. Add working memory session isolation
7. Fix security model documentation vs reality gaps

### P2 — Next Sprint
8. Implement hybrid compression (T5 compress, T4 extract, T6 delete)
9. Add model-specific tokenizers
10. Implement session_interrupt checkpoint
11. Build metrics dashboard
12. Decide "Lauderdale" status

### P3 — Ongoing
13. Night Council: add context orchestrator + skill engine maintenance
14. Integration test suite
15. Dead letter queue + message replay
16. Encrypt memory DB
17. Activate Pantheon personas
18. Wire additional keys
19. Enterprise white paper
20. Kimi: activate when key available