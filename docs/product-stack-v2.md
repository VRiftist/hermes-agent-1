# LumenHub Product Stack (v2 — Skill Engine Architecture)

> Generated: 2026-05-25 | Status: Architecture Blueprint (Updated)
> AI Backend: Hermes Agent (local-first, cloud fallback, skill engine built-in)
> Key change: **OpenClaw eliminated. All skills live inside Hermes.**

## Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 LUMENHUB PRODUCT STACK                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Flutter 3.44 + Riverpod                 │    │
│  │  ┌────────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌──────┐ │    │
│  │  │  Core  │ │  AI  │ │ Sync │ │Platfrm │ │Admin │ │    │
│  │  │        │ │      │ │      │ │        │ │      │ │    │
│  │  └───┬────┘ └──┬───┘ └──┬───┘ └───┬────┘ └──┬───┘ │    │
│  │      │         │        │          │         │      │    │
│  │  ┌───▼─────────▼────────▼──────────▼─────────▼────┐│    │
│  │  │           Hermes Agent Backend                 ││    │
│  │  │                                               ││    │
│  │  │  ┌─────────────┐    ┌──────────────────────┐  ││    │
│  │  │  │  Skill      │    │  Model Routing +     │  ││    │
│  │  │  │  Engine     │◄──►│  Context Orchestrator │  ││    │
│  │  │  │  (JSON      │    │  + Memory Palace      │  ││    │
│  │  │  │   defined)  │    │                      │  ││    │
│  │  │  └──────┬──────┘    └──────────┬───────────┘  ││    │
│  │  │         │                      │              ││    │
│  │  │  ┌──────▼──────┐       ┌───────▼───────┐     ││    │
│  │  │  │  Skill      │       │  Local LLMs   │     ││    │
│  │  │  │  Registry   │       │  qwen3:14b/8b │     ││    │
│  │  │  └─────────────┘       │  qwen3-coder  │     ││    │
│  │  └─────────────────────────┼────────────────┘     ││    │
│  └────────────────────────────┼──────────────────────┘│    │
│                               │                       │    │
│  ┌────────────────────────────▼──────────────────────┐ │    │
│  │              Subscription Tiers                    │ │    │
│  │  Free → Starter ($8) → Pro ($20) → Enterprise     │ │    │
│  └───────────────────────────────────────────────────┘ │    │
└─────────────────────────────────────────────────────────┘
```

## API Surface

**One entry point per client.** All clients (Flutter, Cursor plugin, web) call the same Hermes HTTP API.

```
POST /v1/chat/completions      → Model routing + context assembly
POST /v1/memory/query          → Memory palace search
POST /v1/memory/store          → Memory palace persist
POST /v1/skills/execute        → Execute a named skill
GET  /v1/skills                → List available skills
GET  /v1/context/status        → Context health + tier usage
GET  /v1/models/status         → Model availability
```

See `docs/hermes-api-spec-v1.md` for full details.

## Core

**Priority:** 1 | **Status:** planned

- `app_shell` (navigation, routing, theme)
- `auth_flow` (onboarding, account linking, biometrics)
- `home_dashboard` (daily review, quick capture, AI suggestions)
- `note_editor` (rich text, markdown, voice, sketches)
- `memory_palace_ui` (spatial memory visualization)
- `context_chrome` (shows active context, trimming status, tier usage)

## AI Backend

**Priority:** 2 | **Status:** planned

### Hermes Core
- `hermes_connector` — HTTP/SSE bridge to Hermes Agent backend
- `skill_engine` — Executes JSON-defined skills (replaces OpenClaw entirely)
- `model_routing` — Deliberate model selection, not reactive failover
- `context_orchestrator` — 6-tier context lifecycle, 12K token budget
- `memory_palace` — SQLite-backed persistent memory, infinite effective context
- `resource_guard` — Pre-launch RAM/process checks for 30B+ models
- `circuit_breaker` — Health monitoring + automatic failover
- `night_council` — Daily automated review + maintenance

### Client-facing AI Modules
- `smart_compose` — AI writing assistance via `smart_compose` skill
- `auto_tag` — Semantic tagging on create via `auto_tag` skill
- `daily_digest` — AI daily review via `daily_digest` skill
- `ask_memory` — Natural language memory search via `memory_search` skill
- `context_manager` — Tier visibility, manual trim controls via `context_health` skill
- `archive_review` — Nightly consolidation via `archive_review` skill
- `consolidate_notes` — Merge related notes via `consolidate_notes` skill

### How Skills Replace OpenClaw

Before (OpenClaw model):
```
User → Cursor/IDE → OpenClaw → Skills (external, separate system)
                              → Memory (separate)
                              → Context (separate)
```

After (Hermes model):
```
User → Cursor plugin / Flutter app → Hermes Agent
                                   ├── skill_engine (skills defined in JSON)
                                   ├── model_routing (deliberate selection)
                                   ├── memory_palace (persistent, shared)
                                   ├── context_orchestrator (tier-based trim)
                                   └── resource_guard (safety gate)

→ One API key. No separate skill system needed.
```

## Tiers

**Priority:** 3 | **Status:** refining (pending pricing finalization)

| Tier | Price | What You Get |
|------|-------|------|
| **Free** | $0 | Local only, basic notes, no AI, 50 notes, 2K context |
| **Starter** | $8/mo | AI compose, auto-tag, 8K context, 500 notes |
| **Pro** | $20/mo | All AI (7 skills), 16K context, unlimited notes, memory palace, priority models |
| **Enterprise** | $50/user/mo | Teams, admin, API, priority models, custom skills |

Launch pricing: Months 1-3 Pro at $12/mo (40% off), Months 4-6 at $16/mo (20% off), Month 7+ at $20/mo.

## Skill Registry

Built-in skills (all JSON-defined in `~/.hermes/skills/`):

| Skill | Trigger | Model | Purpose |
|-------|---------|-------|---------|
| `daily_digest` | cron 08:00 | qwen3:14b | Summarizes yesterday's notes and decisions |
| `auto_tag` | on_create | qwen3:8b | Semantic tagging on new notes |
| `context_health` | on_request | qwen3:8b | Context window status report |
| `archive_review` | cron 03:00 | qwen3:14b | Night Council maintenance |
| `memory_search` | on_request | qwen3:14b | Natural language memory query |
| `smart_compose` | on_request | qwen3:14b | AI writing assistance |
| `consolidate_notes` | on_request | qwen3:14b | Merge related notes into knowledge |

Custom skills can be added as JSON files — no code changes needed for simple workflows.

## Sync Infra

**Priority:** 4 | **Status:** planned

- `sync_engine` (CRDT or operational transform)
- `cloud_relay` (encrypted sync server)
- `offline_queue` (conflict resolution)
- `device_registry` (device management)

## Platforms

**Priority:** 5 | **Status:** iOS/Android pending

- **macOS**: Primary dev target (Flutter desktop)
- **Windows**: Flutter desktop
- **iOS**: Flutter mobile, TestFlight beta
- **Android**: Flutter mobile, Play Store
- **Web**: PWA, progressive enhancement

## Build Sequence

```
Phase 1 (Weeks 1-4): Core MVP
  → app_shell, note_editor, home_dashboard
  → Basic Hermes connector (manual trigger)
  → Free tier only

Phase 2 (Weeks 5-8): AI Integration
  → All 7 built-in skills active
  → Tiered feature gating (Free/Starter/Pro)
  → Daily digest + context chrome
  → Cursor plugin (thin client, ~200 lines)

Phase 3 (Weeks 9-12): Sync + Platforms
  → sync_engine, cloud_relay
  → iOS + Android builds
  → Enterprise tier + admin panel
  → User-defined custom skills (JSON editor)

Phase 4 (Weeks 13-16): Polish + Launch
  → Memory palace UI
  → Performance optimization
  → Marketing blitz + launch
```

## OpenClaw Elimination Checklist

- [x] All 7 skills defined as JSON in `~/.hermes/skills/`
- [x] Skill engine built (`scripts/skill_engine.py`) with caching + param validation
- [x] Skills use Hermes' own model routing (not external)
- [x] Skills access memory palace directly
- [x] API spec defines `/v1/skills/execute` endpoint
- [ ] Cursor plugin implementation (~200 lines, pending)
- [ ] Flutter app skill UI (pending Phase 2)
- [ ] Custom skill JSON editor (pending Phase 3)