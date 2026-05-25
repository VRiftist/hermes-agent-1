# LUMENHUB × HERMES — FULL DIMENSIONAL ANALYSIS

> Generated 2026-05-25 | Comprehensive top-to-bottom review of every project dimension

---

## DIMENSION MAP (13 Dimensions)

```
DIM 01  Product Vision & Strategy
DIM 02  Application Architecture
DIM 03  Data Model & Storage
DIM 04  AI / ML Integration
DIM 05  Agent Infrastructure (Hermes)
DIM 06  Platform Coverage
DIM 07  UI / UX / Design System
DIM 08  Dev Environment & Tooling
DIM 09  Security & Privacy
DIM 10  DevOps & Infrastructure
DIM 11  Testing & Quality
DIM 12  Documentation & Knowledge
DIM 13  Business & Sustainability
```

---

## DIM 01: PRODUCT VISION & STRATEGY

### Current State
- Flutter app called "LumenHub" — seed/prototype
- Core UI: MemoryPalette — card-based memory items with hot/cold zones + relevance scoring
- Underlying thesis: A context-aware personal knowledge management system powered by AI

### What's Clear
- User wants a PKM tool with AI augmentation
- Memory items are the core entity (not notes, not tasks)
- Zones (hot/cold) suggest prioritization/attention management
- Relevance scoring suggests automated triage

### What's Missing
- **Elevator pitch** — "LumenHub is a ___ for ___" is undefined
- **Target persona** — Solo developer? Knowledge workers? Students? Creatives?
- **Wedge/unique mechanism** — What makes people switch from Obsidian/Notion/Logseq?
- **Monetization hypothesis** — Free? One-time? Subscription? Open source + hosted?
- **Success metric** — How do we know if LumenHub is working? (DAU? Items created? Time in app?)
- **North Star** — What's the one metric that matters right now?

### Gaps Found
| Gap | Severity | Action |
|-----|----------|--------|
| No product positioning statement | P1 | Write 3 positioning options, pick one |
| No target persona defined | P1 | Define primary + secondary user |
| No competitive moat identified | P1 | Identify what LumenHub does that others can't easily replicate |
| No success metrics | P2 | Define 3 KPIs for MVP launch |
| Monetization undefined | P2 | At minimum, state philosophy (free/open-source vs paid) |

---

## DIM 02: APPLICATION ARCHITECTURE

### Current State
- Flutter 3.44.0, Riverpod for state
- 3 source files, 368 lines
- macOS desktop enabled, Windows desktop just enabled
- Android/iOS/Web not enabled yet
- No storage backend, no persistence

### Architecture Decisions Made (ADRs)
| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | SQLite + drift, hybrid with optional cloud | PROPOSED |
| ADR-002 | Phased AI: passive → active → conversational | PROPOSED |
| ADR-003 | Platform order: macOS → Windows → Android → iOS → Web | PROPOSED |
| ADR-004 | MVP: CRUD + zones + tags + search + scoring | PROPOSED |

### What's Missing
- **No project structure defined** — Where do new features go? What's the folder convention?
- **No dependency strategy** — What packages are allowed? What's the approval process?
- **No build configuration** — flavors, environments, signing
- **No CI/CD pipeline** — manual deploys forever
- **No version management strategy** — how do versions map to sprints?
- **No error handling strategy** — global error boundary, logging, crash reporting
- **No accessibility strategy** — WCAG compliance not considered
- **No i18n strategy** — English only, no l10n setup

### Action Items
| Item | Severity | Sprint |
|------|----------|--------|
| Define project structure convention | P1 | Sprint 0 |
| Set up drift/SQLite with basic entities | P0 | Sprint 1 |
| Enable Android platform properly | P1 | Sprint 1 |
| Define error handling patterns | P1 | Sprint 1 |
| Add crash reporting (Sentry/firebase) | P2 | Sprint 2 |
| Set up CI (GitHub Actions for build/test) | P2 | Sprint 2 |
| Accessibility audit | P3 | Sprint 4 |
| i18n foundation | P3 | Sprint 4 |

---

## DIM 03: DATA MODEL & STORAGE

### Current State
- In-memory only via `ContextScorer` (StateNotifier<List<MemoryItem>>)
- `MemoryItem` class: id, title, summary, lastAccessed, relevanceScore, zone
- No persistence, no database, no migrations

### Proposed Data Model (ADR-004)
```
MemoryItem:
  - id (UUID)
  - title (String)
  - summary (String, nullable, auto-generated)
  - content (Text, nullable)
  - zone (enum: hot, warm, cold, archive)
  - relevanceScore (Double, 0.0–1.0)
  - tags (many-to-many → Tag)
  - relationships (edges → other MemoryItems)
  - createdAt, updatedAt, lastAccessedAt (DateTime)
  - source (enum: manual, ai_generated, bookmark, import)
  - metadata (JSON, flexible)

Tag:
  - id (UUID)
  - name (String, unique)
  - color (String, hex)
  - parentId (UUID, nullable — hierarchical tags)

Relationship:
  - sourceId (UUID)
  - targetId (UUID)
  - type (enum: related_to, part_of, depends_on, contradicts, builds_on)
  - weight (Double, 0.0–1.0)
  - createdAt

SearchIndex:
  - FTS5 virtual table for full-text search on title, summary, content
```

### What's Missing
- **No drift entities written** — pure Dart classes exist, but no DB layer
- **No migration strategy** — schema will evolve, need forward migration plan
- **No backup/restore** — no export format defined
- **No data validation** — no constraints on title length, content size, etc.
- **No bulk operations** — adding 100 items at a time not considered
- **No query patterns defined** — what queries will the UI need? (by zone, by tag, by date, by relevance, by relationship, full-text, combinations)
- **No data retention policy** — items grow forever? Archive? Auto-delete?
- **No encryption at rest** — SQLCipher not yet configured

### Action Items
| Item | Severity | Sprint |
|------|----------|--------|
| Write drift entities for MemoryItem, Tag, Relationship | P0 | Sprint 1 |
| Implement database helper + migrations | P0 | Sprint 1 |
| Wire ContextScorer to use real database instead of in-memory | P0 | Sprint 1 |
| Implement FTS5 search | P0 | Sprint 1 |
| Define backup format (JSON export) | P1 | Sprint 1 |
| Data validation layer | P1 | Sprint 2 |
| Encryption at rest (SQLCipher) | P2 | Sprint 3 |
| Bulk import from JSON/Markdown | P2 | Sprint 3 |

---

## DIM 04: AI / ML INTEGRATION

### Current State
- Hermes agent stack exists and runs standalone
- Model routing works: 8 models, 7 categories, deliberate routing
- Consult/Merge/quality-gate cycle validated end-to-end
- ContextScorer has basic keyword relevance (not AI-powered)
- **ZERO integration between Hermes and the Flutter app**

### Integration Points Needed
| Integration | Description | Priority |
|-------------|-------------|----------|
| Auto-tagging | When item created, Hermes suggests tags | P1 MVP+ |
| Relevance scoring upgrade | Replace keyword match with LLM-based relevance | P1 MVP+ |
| NL search | User types "what did I read about X?" → semantic search | P2 V1 |
| Content summarization | AI generates summary field | P2 V1 |
| Relationship suggestion | AI suggests "this is related to that" | P2 V1 |
| Conversational interface | Full chat-based memory exploration | P3 V2 |
| Interruption recovery | AI helps resume context after app restart | P3 V2 |

### What's Missing
- **No API bridge between Flutter and Hermes** — need HTTP/local socket/gRPC interface
- **No latency budget** — AI calls must be <500ms or async to not block UI
- **No error/fallback strategy** — what happens when Hermes is down?
- **No cost tracking** — AI calls cost money, need usage monitoring
- **No user control** — can user disable AI features? Opt out of data sending?
- **Embeddings not considered** — for semantic search, need vector embeddings (local: `llama.cpp`? cloud: DeepSeek embeddings?)

### Action Items
| Item | Severity | Sprint |
|------|----------|--------|
| Define Hermes↔Flutter communication protocol | P1 | Sprint 0 |
| Implement auto-tag via Hermes (async, non-blocking) | P1 | Sprint 2 |
| Upgrade ContextScorer to use LLM embeddings | P1 | Sprint 2 |
| Add NL search prototype | P2 | Sprint 2 |
| Implement local embedding inference (ollama) | P2 | Sprint 3 |
| Conversational interface design | P3 | Sprint 4 |

---

## DIM 05: AGENT INFRASTRUCTURE (HERMES)

### Current State
- **11/13 layers operational**
- Memory Palace: SQLite, 90 episodes, 66 facts, 104KB
- Context Orchestrator: 6-tier, 12K budget, 3-phase lifecycle — STANDALONE ONLY
- Model Routing: 8 models, 7 categories, deliberate routing ✅
- Circuit Breaker: 5 models, failover chain ✅
- Key Guardian: Daily cron, 3/5 keys validated ✅
- Night Council: Cron at 03:00 UTC ✅
- Consult/Merge: 4-step cycle validated ✅
- Wiki: 4 pages initialized ✅
- Documentation: 5 docs, 69KB ✅
- Gateway Integration: Built standalone, NOT wired into CLI loop ❌
- Kimi Client: Dual-key loaded, Moonshot returns 401 ⚠️

### What's Working
Almost everything works — the engineering is solid. The problem is integration.

### What's Broken / Incomplete (CRITICAL)
| Issue | Type | Fix |
|-------|------|-----|
| Gateway integration not in CLI loop | Architecture | Wire `gateway_integration.py` into message handler |
| `gateway_trim_check()` missing defensive default | Bug | Add `current_tokens=0` default param |
| Dual health tracking (CB + MR) | Architecture | Unify — CB as authority |
| Telegram tokens missing | Config | Add to `.env` + test |
| `redact_pii: false` | Security | Set to `true`, audit logs |
| Kimi auth dead | External | Accept or fix Moonshot platform |
| DeepSeek partially verified | External | Full endpoint validation |
| Memory Palace 99% full | Capacity | Add purge logic to Night Council |
| T5 compression not implemented | Feature | Implement hybrid compression |
| Wiki not auto-activated | Config | Add `WIKI_PATH` to `.env` |
| `qwen3-coder` not in routing | Config | Add to models dict + categories |
| Night Council missing OC maintenance | Config | Add context orchestrator cleanup step |

---

## DIM 06: PLATFORM COVERAGE

| Platform | Status | Notes |
|----------|--------|-------|
| macOS Desktop | ✅ Enabled | Primary dev environment |
| Windows Desktop | ✅ Enabled | UTM VM downloading (Win11 ARM64) |
| Linux Desktop | ⚠️ ARM build needs verification | RTX 3060 box alive, needs DO droplet |
| Android | ⚠️ SDK exists, platform not fully enabled | Needs flutter config --enable-android |
| iOS | ⚠️ Simulator should work via Xcode | Needs flutter config --enable-ios |
| Web | ⚠️ Not enabled | Needs flutter config --enable-web |
| Linux (LXC/Container) | ❌ Not considered | Future: self-hosted backend? |

### Platform Priority (ADR-003): macOS → Windows → Android → iOS → Web

### Action Items
| Item | Severity | Sprint |
|------|----------|--------|
| Verify Win11 VM builds after ISO lands | P0 | Sprint 0 |
| Test `flutter build windows` on Mac cross-compile | P0 | Sprint 1 |
| Enable Android properly + test emulator | P1 | Sprint 1 |
| Verify iOS simulator builds | P1 | Sprint 2 |
| Enable web for demo/sharing | P2 | Sprint 3 |
| Linux desktop build from Linux box | P2 | Sprint 4 |

---

## DIM 07: UI / UX / DESIGN SYSTEM

### Current State
- Dark theme with `Color(0xFF1A1A2E)` base, `Color(0xFF00D4AA)` accent
- MemoryPalette: search bar, add button, card list with hot/cold zone badges
- Cards show: title, summary snippet, relevance score, last-accessed time
- Hot cards have brighter background + green border, cold cards are dimmer

### What's Working
- Visual hierarchy is clear
- Dark theme is cohesive
- Card-based layout is standard for PKM tools

### What's Missing
- **No onboarding screen** — blank slate is confusing
- **No empty states** — what does it look like with 0 items? 1000 items?
- **No tooltips or help** — what do zones mean? What is relevance?
- **No keyboard shortcuts** — power users need these
- **No responsive layout** — desktop proportions won't work on mobile
- **No animation/micro-interactions** — feels static
- **No theming options** — dark only, no light theme, no custom colors
- **No notification/toast system** — no feedback for actions
- **No undo/redo** — destructive actions are permanent
- **No drag-and-drop** — for reordering, assigning zones, creating relationships

---

## DIM 08: DEV ENVIRONMENT & TOOLING

### Current State
- **Mac M2 32GB**: Flutter 3.44, Xcode, Android SDK, VS Code (assumed), all dev tools present
- **Win11 ARM64 VM**: UTM installed, ISO downloading, needs creation
- **Linux RTX 3060**: Confirmed alive via SSH, needs DO droplet for cloud access
- **Git**: VRiftist on GitHub, repo pushed
- **Hermes**: Full stack at `~/.hermes/`, 9/13 layers operational
- **IDE**: Not verified — VS Code? Android Studio? IntelliJ?

### What's Missing
- **IDE config not verified** — extensions, settings, launch configs
- **Flutter version management** — single version now, but may need multi-version
- **Dependency cache management** — `.dart_tool/` is 51 files already
- **Build artifact management** — `build/` has 1,383 files, no clean strategy
- **Git workflow** — no branching strategy, no PR template, no commit convention
- **Secrets management** — `.env` exists but no rotation procedure beyond Night Council
- **Docker?** — not considered for reproducible dev environments

---

## DIM 09: SECURITY & PRIVACY

### Current State
- `.env` vault: chmod 600, gitignored ✅
- `.env.template` for rotation ✅
- `.gitignore` excludes secrets, logs, memory palace ✅
- `redact_pii: false` in config ⚠️ **CONCERN**
- Memory palace is unencrypted SQLite ⚠️
- No auth layer on the app itself (single-user assumed)

### Issues Matrix
| Issue | Risk | Likelihood | Impact |
|-------|------|-----------|--------|
| PII in logs | HIGH | Medium | Data leak if logs shared/uploaded |
| Unencrypted SQLite | HIGH | Low (local only) | Device theft → data breach |
| No app-level auth | MEDIUM | Low (single-user) | Unauthorized access if device shared |
| Cloud sync = unencrypted transit | HIGH | Future | MitM on sync traffic |
| API keys in env vars | MEDIUM | Low | Already mitigated by gitignore |
| No audit logging | MEDIUM | Medium | Can't trace data access |

### Action Items
| Item | Severity | Sprint |
|------|----------|--------|
| Set `redact_pii: true` | P0 | Now |
| Enable SQLCipher on memory palace | P1 | Sprint 2 |
| Add app-level auth (biometrics/keychain) | P2 | Sprint 3 |
| Encrypt cloud sync payload | P2 | Sprint 3 |
| Add audit trail for data access | P3 | Sprint 4 |

---

## DIM 10: DEVOPS & INFRASTRUCTURE

### Current State
- GitHub: repo live, push access ✅
- SSH agent: running, keys loaded ✅
- Night Council cron: `0 3 * * *` ✅
- Key Guardian: daily check ✅
- Wiki: initialized ✅
- No CI/CD ❌
- No deployment pipeline ❌
- No monitoring/alerting (Telegram tokens missing) ❌
- No logging infrastructure ❌

### Action Items
| Item | Severity | Sprint |
|------|----------|--------|
| Add Telegram bot tokens to `.env` | P0 | Now |
| GitHub Actions: lint + test on PR | P1 | Sprint 1 |
| GitHub Actions: build artifacts on tag | P2 | Sprint 2 |
| Centralized log aggregation | P3 | Sprint 4 |
| Uptime monitoring for Hermes cron | P2 | Sprint 3 |

---

## DIM 11: TESTING & QUALITY

### Current State
- `test/widget_test.dart`: boilerplate only
- `scripts/full_selftest.py`: 9/9 modules passing ✅
- Hermes stack self-tests: all passing ✅
- **No unit tests for Flutter business logic**
- **No widget tests for MemoryPalette**
- **No integration tests**
- **No golden tests**

### Test Strategy Needed
| Level | Scope | Tool | Priority |
|-------|-------|------|----------|
| Unit | ContextScorer, model_routing, memory_palace | flutter_test / pytest | P0 |
| Widget | MemoryPalette cards, search, zones | flutter_test | P1 |
| Integration | Full app flow: create → save → restart → load | integration_test | P2 |
| End-to-end | Hermes + Flutter + storage + AI | custom scripts | P3 |
| Performance | Memory usage, build times, startup | flutter drive | P2 |

---

## DIM 12: DOCUMENTATION & KNOWLEDGE

### Current State
- **69KB docs** (5 files in `documentation/`)
- **Wiki**: 4 pages at `~/.hermes/wiki/`
- **ADRs**: 4 drafted (storage, AI, platform, MVP)
- **Sprint plan**: drafted
- **Coherency audit**: exists from prior session
- **Board review**: just completed
- **368 lines of code** vs 69KB docs → ratio 188:1 ⚠️

### What's Missing
- **README** needs complete rewrite (currently boilerplate)
- **Architecture overview diagram**
- **Developer onboarding guide** (how to set up dev env)
- **User documentation** (what is LumenHub, how to use it)
- **API documentation** (Hermes tools, scripts)
- **Contributing guide**
- **Changelog**
- **Decision log** (separate from ADRs — day-to-day decisions)

---

## DIM 13: BUSINESS & SUSTAINABILITY

### Current State
- Solo developer (lumenhubai)
- No business entity, no monetization
- No marketing, no landing page
- No user research conducted
- Open-source? Closed-source? Not decided

### Questions That Need Answers
1. **Is this a product or a tool?** (Product = sell to users; Tool = use internally)
2. **Monetization:** If product, how? (SaaS subscription, one-time purchase, freemium?)
3. **Open-source strategy:** Core open + hosted premium? Fully closed?
4. **Time investment:** How many hours/week can sustain development?
5. **Revenue timeline:** When does this need to generate income?
6. **Team:** Solo forever, or planning to onboard others?
7. **Legal:** Terms of service, privacy policy, licensing (MIT? proprietary?)

---

## THINGS WE SHOULD BE ASKING BUT AREN'T

1. What happens with 10,000 memories in the UI?
2. How do we handle conflicting memories?
3. What's the data portability / exit strategy?
4. Single-user or multi-user architecture?
5. Mobile touch targets in a desktop-first UI?
6. What's our AI cost ceiling per user per month?
7. What happens when Hermes goes down mid-session?
8. Is the relevance score actually useful or decorative?
9. What privacy guarantees do we commit to?
10. Power users vs casual users — who's the real target?
11. What's the "aha moment" for a new user?
12. How do we measure if memory augmentation actually works?
13. Retention: do users come back after day 1?
14. What data do we NEVER want to send to the cloud?
15. What's our plan if a key cloud provider disappears?

---

## SEVERITY-RANKED FINDINGS (ALL 13 DIMENSIONS)

| # | Dimension | Finding | Severity | Fix |
|---|-----------|---------|----------|-----|
| 1 | App | No persistent storage — everything is in-memory | P0 | Implement SQLite + drift Sprint 1 |
| 2 | Hermes | Gateway integration not wired to CLI loop | P0 | Identify + wire integration point |
| 3 | Hermes | Dual health tracking (CB + MR) diverge | P0 | Unify with CB as authority |
| 4 | Security | `redact_pii: false` + verbose logs = data leak | P0 | Set `true`, audit logs |
| 5 | Security | Memory palace SQLite unencrypted | P1 | SQLCipher upgrade |
| 6 | Product | No product positioning or target persona | P1 | Write positioning doc |
| 7 | DevOps | No Telegram tokens → all alerts silently dead | P1 | Add tokens + test |
| 8 | Platform | Win11 VM not yet created | P1 | Finish ISO + create VM |
| 9 | Data | No data model implementation (only Dart classes) | P0 | Write drift entities Sprint 1 |
| 10 | AI | Zero Hermes↔Flutter integration | P1 | Define protocol + implement bridge |
| 11 | Config | `qwen3-coder:30b-a3b` not in routing | P1 | Add to model_routing.py |
| 12 | Testing | Zero app-level tests | P1 | Add unit tests Sprint 1 |
| 13 | Config | WIKI_PATH not in `.env` | P2 | Add to vault |
| 14 | Data | T5 compression not implemented | P2 | Implement in OC |
| 15 | UX | No onboarding, no empty states, no help | P2 | Design + implement |
| 16 | DevOps | No CI/CD pipeline | P2 | GitHub Actions |
| 17 | Business | No monetization hypothesis | P2 | Define philosophy |
| 18 | Security | No crash reporting | P2 | Add Sentry/Firebase |
| 19 | Docs | Docs:code ratio 188:1 — stop writing, start building | P1 | Prioritize implementation |
| 20 | AI | No cost tracking or rate limiting for AI calls | P2 | Add usage monitoring |

---

## RECOMMENDED ACTION SEQUENCE

### NOW (Before Product Design Discussion)
- [ ] Fix `redact_pii` → `true`
- [ ] Add Telegram tokens to `.env`
- [ ] Defensive default on `gateway_trim_check`
- [ ] Finish Win11 VM creation (waiting on ISO)
- [ ] Log this entire analysis to memory palace

### SPRINT 0 (2-3 days)
- [ ] Wire gateway_integration into CLI loop
- [ ] Unify health tracking
- [ ] Finish dev environment verification
- [ ] Project structure convention

### SPRINT 1 (2 weeks) — MVP Foundation
- [ ] SQLite + drift database with entities
- [ ] CRUD operations
- [ ] Port ContextScorer to real storage
- [ ] Zone management
- [ ] Tag system
- [ ] FTS5 search
- [ ] Flat tests pass
- Push to GitHub with CI

### SPRINT 2 (2 weeks) — Intelligence
- [ ] Hermes↔Flutter bridge
- [ ] AI auto-tagging
- [ ] Upgraded relevance scoring
- [ ] Android + iOS platform enable
- [ ] Settings/preferences
- [ ] Markdown export

### SPRINT 3-4 — Polish & V2
As defined in sprint plan doc.