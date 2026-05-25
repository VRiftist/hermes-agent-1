# LumenHub Product Blueprint & Architecture Review
## Multi-Model Deep Review Specification

### Purpose
Comprehensive product-by-product blueprint covering every feature, menu, button, use case, and technology decision. Designed so future maintainers have ZERO confusion.

### Products in Scope
1. **LumenHub** — Flutter PKM (Personal Knowledge Management) application
2. **Hermes Agent** — Self-improving multi-model AI agent system
3. **LumenHub Server/Backend** — Sync, AI processing, multi-device coordination (future)

---

## 1. LUMENHUB — Full Product Blueprint

### 1.1 What is LumenHub?
A local-first, AI-augmented Personal Knowledge Management system that runs on Mac, Windows, Linux, Android, and iOS. It replaces scattered notes, bookmarks, and highlights with a unified, intelligent memory palace backed by deliberate AI model routing.

### 1.2 Target Users
- **Primary**: Knowledge workers, researchers, developers who manage large personal knowledge bases
- **Secondary**: Students, content creators, enterprise teams needing shared knowledge graphs
- **Tertiary**: Power users who want self-hosted, privacy-first AI-augmented memory

### 1.3 Core Differentiation
- **Local-first architecture** — all data lives on-device by default
- **AI-native memory management** — relevance scoring, automatic tagging, semantic search
- **Multi-platform sync** — eventual cloud sync with end-to-end encryption
- **Hermes integration** — direct access to multi-model AI for reasoning, summarization, Q&A
- **Privacy posture** — no telemetry, no cloud dependency for core features

### 1.4 Competitive Landscape
| Product | LumenHub Advantage | LumenHub Gap |
|---------|-------------------|--------------|
| Obsidian | Native AI integration, structured data | Plugin ecosystem maturity |
| Notion | Offline-first, local storage | Collaboration features |
| Logseq | Better UI polish, mobile apps | Graph view depth |
| Roam | Local storage option, AI features | Price point advantage |
| Apple Notes | Cross-platform sync | AI features, structured data |
| Bear | Export flexibility | AI integration |

### 1.5 Architecture Decisions (ADRs)

#### ADR-001: Storage Engine — SQLite + Drift
- **Decision**: SQLite via drift package for all persistent storage
- **Rationale**: ACID compliance, local-first, no server dependency, mature Flutter support
- **Trade-off**: No native full-text search (need FTS5 extension), migration complexity
- **Status**: ✅ Accepted

#### ADR-002: Platform Strategy — Flutter 3.44+
- **Decision**: Single Flutter codebase for all platforms
- **Rationale**: Code reuse, consistent UX, single team can maintain
- **Trade-off**: Performance ceiling on complex animations, platform-native feel tradeoffs
- **Status**: ✅ Accepted
- **Alternative considered**: Electron (rejected — higher memory footprint, worse mobile story)

#### ADR-003: AI Integration — Hermes Agent as Backend
- **Decision**: Hermes agent system handles all AI processing via deliberate model routing
- **Rationale**: Avoid vendor lock-in, optimize cost/latency per task type, privacy
- **Trade-off**: Complexity of multi-model orchestration
- **Status**: ✅ Accepted

#### ADR-004: Security Model — Tiered Capability
- **Decision**: Sandboxed tool execution, conservative permissions, redact_pii=true
- **Rationale**: Prevent data leaks, comply with enterprise security requirements
- **Trade-off**: Some AI capabilities restricted
- **Status**: ✅ Accepted

### 1.6 Feature Map (Complete)

#### Tier 1 — Core (MVP)
| Feature | Description | Status | Platform |
|---------|-------------|--------|----------|
| Memory Cards | Create/edit/delete knowledge items | Implemented (basic) | All |
| Relevance Scoring | AI-driven relevance scoring per item | Implemented (basic) | All |
| Hot/Cold Zones | Visual indicators for item importance | Implemented | All |
| Full-text Search | Search across all memories | Implemented (basic) | All |
| Local Storage | SQLite persistence via drift | Implemented | All |
| Dark Theme | Dark UI as primary theme | Implemented | All |
| Add Memory | + button to create new items | Implemented | All |

#### Tier 2 — Enhanced (v1.1)
| Feature | Description | Hermes Integration |
|---------|-------------|-------------------|
| Semantic Search | Vector similarity search across memories | Context orchestrator + memory palace |
| Auto-tagging | AI-generated tags on memory creation | Hermes task classification |
| Memory Summarization | Auto-generated summaries for long entries | DeepSeek v4-flash |
| Related Items | Suggest connections between memories | Knowledge graph + Grok |
| Smart Categories | AI-driven auto-organization | Athena (critic) verification |
| Import/Export | Markdown, JSON, OPML import/export | — |
| Tags & Collections | Manual + AI-organized tag system | — |

#### Tier 3 — AI-Native (v2.0)
| Feature | Description | Hermes Integration |
|---------|-------------|-------------------|
| Ask My Memory | Natural language queries across all stored knowledge | Full consult/merge cycle |
| Auto-Connect | AI identifies related memories across topics | Ring quality gate |
| Learning Path | AI-curated learning sequences from stored knowledge | Deliberate routing |
| Daily Digest | AI-generated daily review of important memories | Night Council cron |
| Context-aware Suggestions | Suggestions based on current work context | Context orchestrator |
| Spaced Repetition | SM-2/FSRS-based review scheduling | Memory palace + context scorer |
| Multi-document Synthesis | Combine multiple memories into research briefs | Consult/merge pipeline |

#### Tier 4 — Enterprise (v3.0)
| Feature | Description |
|---------|-------------|
| Team Spaces | Shared knowledge bases with permissions |
| E2E Encrypted Sync | Cloud sync with zero-knowledge encryption |
| Audit Trail | Complete change history per item |
| Admin Console | Usage analytics, policy management |
| API Access | REST/GraphQL API for integrations |
| SSO/SAML | Enterprise identity provider support |
| Compliance Export | GDPR/CCPA data export tools |

### 1.7 UI/UX — Screen-by-Screen Blueprint

#### Screen 1: Memory Palette (Main View)
```
┌──────────────────────────────────────────┐
│  🔍 [Search memories...]     [+] [⋮]    │
├──────────────────────────────────────────┤
│  ┌─ Hot Zone ─────────────────────────┐  │
│  │ 🔴 Item Title        [tag] [⋮]    │  │
│  │    Summary text...    0.95 ↗       │  │
│  ├────────────────────────────────────┤  │
│  │ 🔴 Another Item       [tag] [⋮]    │  │
│  │    Summary text...    0.88 ↗       │  │
│  └─────────────────────────────────────┘  │
│  ┌─ Warm Zone ────────────────────────┐  │
│  │ 🟡 Item Title        [tag] [⋮]    │  │
│  │    Summary text...    0.62 →       │  │
│  └─────────────────────────────────────┘  │
│  ┌─ Cold Zone ────────────────────────┐  │
│  │ ⚪ Item Title        [tag] [⋮]    │  │
│  │    Summary text...    0.23 →       │  │
│  └─────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  [Hot] [Warm] [Cold] [All]    📊 Stats   │
└──────────────────────────────────────────┘
```

**Interaction Details:**
- Tap memory card → expand to full view with edit, delete, tag, relate
- Long press → quick actions (share, pin, archive)
- Pull down → refresh relevance scores
- Swipe left on card → archive
- Swipe right on card → pin to hot zone

#### Screen 2: Memory Detail View
```
┌──────────────────────────────────────────┐
│  ← Back     Item Title           [⋮]    │
├──────────────────────────────────────────┤
│  Tags: [tag1] [tag2] [+add]              │
│  Zone: 🔴 Hot      Relevance: 0.95      │
│  Created: 2026-05-20   Last seen: today  │
├──────────────────────────────────────────┤
│                                          │
│  [Full content / notes area]             │
│                                          │
│                                          │
├──────────────────────────────────────────┤
│  [💬 Ask AI] [🔗 Connect] [📎 Attach]    │
│  [📝 Edit] [📤 Share] [🗑 Archive]       │
└──────────────────────────────────────────┘
```

#### Screen 3: Ask AI (Hermes Integration)
```
┌──────────────────────────────────────────┐
│  ← Ask My Memory                        │
│  ┌────────────────────────────────────┐  │
│  │ What did I learn about...       🔍 │  │
│  └────────────────────────────────────┘  │
│  ┌─ Model ────────────────────────────┐ │
│  │ ○ Auto (recommended)              │ │
│  │ ○ DeepSeek v4-flash (fast)        │ │
│  │ ○ Grok-4 (current events)         │ │
│  │ ○ Ring-2.6 (deep reasoning)       │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  ┌─ Results ──────────────────────────┐  │
│  │ 🔴 Memory Item 1 (relevance: 0.95)│  │
│  │ "Summary of how this relates..."  │  │
│  │                                    │  │
│  │ 🟡 Memory Item 2 (relevance: 0.72)│  │
│  │ "Connection to..."                 │  │
│  └─────────────────────────────────────┘  │
│  ┌─ AI Synthesis ────────────────────┐    │
│  │ "Based on your stored memories..."│    │
│  └───────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

#### Screen 4: Settings
```
┌──────────────────────────────────────────┐
│  Settings                               │
├──────────────────────────────────────────┤
│  🔒 Security                            │
│  ├─ Biometric lock                      │
│  ├─ E2E Encryption (Enterprise)         │
│  ├─ Redact PII in logs: [ON/OFF]        │
│  └─ Export & Delete Data                │
│                                         │
│  🤖 AI Settings                         │
│  ├─ Default Model: [Auto ▾]            │
│  ├─ Fallback Chain: [Edit ▾]           │
│  └─ Auto-tag on create: [ON/OFF]       │
│                                         │
│  📊 Sync & Storage                      │
│  ├─ Cloud Sync: [Setup ▾]              │
│  ├─ Local Export: Markdown / JSON       │
│  └─ Storage Usage: 2.4 MB              │
│                                         │
│  🎨 Appearance                          │
│  ├─ Theme: [Dark / Light / System]     │
│  └─ Accent Color: [Picker]             │
└──────────────────────────────────────────┘
```

### 1.8 Technology Stack — Justification

| Component | Choice | Why Not Alternative |
|-----------|--------|-------------------|
| UI Framework | Flutter 3.44 | Electron: too heavy for mobile; native: x3 codebases |
| State Management | Riverpod | More testable than Provider, less boilerplate than BLoC |
| Local DB | SQLite + drift | Hive: no relational queries; Moor: deprecated |
| Vector Search | SQLite FTS5 + embeddings | Chroma/Pinecone: requires server; pgvector: no local |
| AI Backend | Hermes agent (local models + cloud fallback) | Direct OpenAI: vendor lock-in, cost |
| Sync Protocol | CRDT-based (future) | Firebase: vendor lock-in; raw REST: conflict-prone |
| Desktop Packaging | Flutter desktop + UTM for CI | Electron: memory overhead; Tauri: Rust dependency |

### 1.9 Context Trimming Architecture

The **context orchestrator** manages what the AI sees and what gets discarded:

```
┌───────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW (12K tokens)            │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  T0: Identity (NEVER trim)                               │
│  ├─ System prompt                                         │
│  ├─ Agent name, purpose, capabilities                    │
│  └─ Operating principles                                  │
│                                                           │
│  T1: Active Task (preserved until task complete)          │
│  ├─ Current user request                                  │
│  ├─ Task state / progress                                 │
│  └─ Intermediate results                                  │
│                                                           │
│  T2: Recent High-Importance (persisted 50 turns)         │
│  ├─ Critical decisions made                               │
│  ├─ User preferences stated                               │
│  └─ Error conditions encountered                          │
│                                                           │
│  T3: Semantic Memory (checked against Palace)             │
│  ├─ Long-term knowledge items                             │
│  ├─ Archived conversation summaries                       │
│  └─ Cross-references to memory palace                    │
│                                                           │
│  T4: Background Context (compressed at 9K)                │
│  ├─ Older conversation history                            │
│  ├─ Tool output summaries                                 │
│  └─ ➤ Compressed with [COMPRESSED] tag                   │
│                                                           │
│  T5: Tool Output (compressed + tagged)                    │
│  ├─ Command outputs                                       │
│  ├─ API responses                                         │
│  └─ ➤ Compressed with [COMPRESSED] tag                   │
│                                                           │
│  T6: Conversation Filler (DELETED first)                  │
│  └─ Greetings, small talk, acknowledgments               │
│                                                           │
├───────────────────────────────────────────────────────────┤
│  BUDGET: 12K tokens │ WARNING: 9K │ HARD TRIM: 6K       │
│  Nightly maintenance: 03:00 UTC via Night Council cron    │
└───────────────────────────────────────────────────────────┘
```

### 1.10 Spaced Repetition Integration

```
          ┌──────────────────────────────┐
          │     Memory Item Created       │
          └──────────────┬───────────────┘
                         │
                    ┌────▼────┐
                    │  Hot    │ Review: 1h, 4h, 12h
                    │ Zone    │
                    └────┬────┘
                         │ (passed reviews)
                    ┌────▼────┐
                    │  Warm   │ Review: 1d, 3d, 7d
                    │ Zone    │
                    └────┬────┘
                         │ (passed reviews)
                    ┌────▼────┐
                    │  Cold   │ Review: 14d, 30d, 90d
                    │ Zone    │
                    └────┬────┘
                         │ (passed all reviews)
                    ┌────▼────┐
                    │Archive  │ Review: 180d
                    └─────────┘
```

- **Algorithm**: Modified FSRS (Free Spaced Repetition Scheduler)
- **Integration**: Context scorer provides relevance decay; memory palace tracks review history
- **Trigger**: Night Council cron checks due items; user can trigger manual review session
- **UI**: Items approaching due date get a subtle pulsing indicator in the Memory Palette

---

## 2. HERMES AGENT — Full System Blueprint

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HERMES AGENT SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               LUMENHUB FLUTTER APP                    │   │
│  │  (UI + State + Local DB)                              │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │              GATEWAY INTEGRATION                      │   │
│  │  (gateway_integration.py — bridge layer)              │   │
│  └──────┬──────────────┬──────────────┬───────────────┘   │
│         │              │              │                    │
│  ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼──────────────┐   │
│  │  Context    │ │  Model    │ │  Memory Palace       │   │
│  │  Orchestr.  │ │  Routing  │ │  (SQLite + Akashic)  │   │
│  │  6-tier     │ │  Deliber. │ │  Episodic/Semantic   │   │
│  │  lifecycle  │ │  routing  │ │  Working memory      │   │
│  └──────┬──────┘ └─────┬─────┘ └────────────────────┘   │
│         │              │                                  │
│  ┌──────▼──────────────▼──────────────────────────────┐   │
│  │            CONSULT / MERGE ENGINE                   │   │
│  │  (classify → route → consult → quality gate)       │   │
│  └──────┬──────┬──────┬──────┬──────┬───────────────┘   │
│         │      │      │      │      │                    │
│  ┌──────▼┐ ┌──▼───┐ ┌▼────┐ ┌▼────┐ ┌▼────────────┐  │
│  │Deep- │ │Grok  │ │Ring │ │Kimi │ │  Local       │  │
│  │Seek  │ │4.20  │ │2.6  │ │v1-8k│ │  Qwen3       │  │
│  │v4    │ │rea- │ │-1t  │ │K    │ │  14b/30b-a3b  │  │
│  │flash/│ │sonin │ │     │ │     │ │              │  │
│  │pro   │ │g     │ │     │ │     │ │              │  │
│  └──────┘ └──────┘ └─────┘ └─────┘ └──────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │          CIRCUIT BREAKER + KEY GUARDIAN           │   │
│  │     Health monitoring + failover + alerts         │   │
│  └──────────────────────────────────────────────────┘   │
│         │                                         │      │
│  ┌──────▼─────────────────────────────────────────▼──┐  │
│  │            NIGHT COUNCIL CRON (03:00 UTC)          │  │
│  │  Key health │ Memory maintenance │ Self-review     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Model Chain (Final, with roles)

| Priority | Model | Provider | Role | Context Budget | Use When |
|----------|-------|----------|------|---------------|----------|
| 1 (local) | qwen3:14b | Ollama Mac | Default fast model | 8K | General tasks, quick answers |
| 2 (local) | qwen3-coder:30b-a3b | Ollama Mac | Reasoning/consult | 12K+ | Code, review, complex analysis |
| 3 (local) | qwen3:8b | Ollama Linux | Long context local | 32K | Long documents, bulk processing |
| 4 (cloud) | deepseek-v4-flash | DeepSeek API | Fast deep reasoning | 24K | Code analysis, logic tasks |
| 5 (cloud) | grok-4.20-reasoning | xAI API | Current events, web | 16K | Research requiring fresh data |
| 6 (cloud) | inclusionai/ring-2.6-1t | OpenRouter | Quality gate / final merge | 262K | Final review, complex merging |
| 7 (cloud) | moonshot:kimi-v1-8k | Moonshot API | Creative tasks | 8K | Brainstorming, creative writing |
| — | deepseek-v4-pro | DeepSeek API | Deep analysis (standby) | 24K | Complex analysis when flash insufficient |

### 2.3 Consult/Merge Protocol

```
USER REQUEST
    │
    ▼
┌─────────────┐
│ CLASSIFY    │ → 7 categories: code_generation, review, reasoning,
│ (weighted)  │   creative, research, quick_answer, multi_step
└──────┬──────┘
       │
    ┌──▼───┐
    │ ROUTE│ → Match category + token budget to best model
    └──┬───┘
       │
    ┌──▼──────────────────────────┐
    │ CONSULT (Athena persona)     │
    │ Generate answer + critique   │
    └──┬──────────────────────────┘
       │
    ┌──▼──────────────────────────┐
    │ QUALITY GATE (Ring model)    │
    │ Review, correct, improve     │
    └──┬──────────────────────────┘
       │
    ┌──▼──────────────────────────┐
    │ DELIVER to user              │
    └─────────────────────────────┘
```

### 2.4 Decision Framework (All Decisions Finalized)

1. **Fallback chain**: Local-first (Mac 14b → Mac 30b-a3b → Linux 8b) → Cloud (DeepSeek → Grok → Ring)
2. **Kimi role**: Creative specialist (#1 for creative category), DIRECT Moonshot API, not OpenRouter
3. **Ring role**: Quality gate / final merge — ALWAYS the last step for complex queries
4. **Compression**: T5 gets `[COMPRESSED]` tag + rephrasing; T6 gets pure deletion
5. **Emergency fallback**: All cloud dead → local-only mode + Telegram alert
6. **Key management**: Centralized `.env` vault + key_guardian.py daily check + 90-day rotation
7. **Security**: `redact_pii: true` in config, sandbox all tool execution, no autonomous state changes
8. **Context budget**: Adaptive per-model (8K–262K), trim warning at 90% budget
9. **Pantheon scope**: Only Hermes + Athena active; rest deferred
10. **Memory Palace**: Functional tool (not decoration), holds identity + role map + capability matrix

---

## 3. MISSING ITEMS & GAPS ANALYSIS

### 3.1 What's Missing from White Papers
- ❌ Kimi input not yet included (will be added)
- ❌ Tools/architecture decisions not fully documented (ADRs cover but need more detail)
- ❌ Flutter vs Electron comparison needs to be in a formal ADR (ADR-002 covers the decision but reasoning is thin)
- ❌ Mac vs Linux vs Windows vs Android vs iOS feature parity matrix
- ❌ Performance benchmarks per model on each platform

### 3.2 Questions to Ask Each Model

**Grok (via X — pain points & user wishes):**
1. What are the top pain points users report about PKM apps (Obsidian, Notion, Logseq)?
2. What features do users most wish existed in knowledge management tools?
3. What are the biggest complaints about AI-integrated note apps?
4. What do enterprise teams want that consumer apps don't provide?
5. What's the gap between "AI note-taking demos" and "daily driver" reality?

**DeepSeek v4-pro (detail-oriented review):**
1. Review all architectural decisions for logical consistency
2. Find edge cases and failure modes in the consult/merge protocol
3. Audit the context trimming strategy for data loss risks
4. Identify performance bottlenecks in the proposed architecture
5. Challenge every assumption — what did we get wrong?

**Claude (final architectural review):**
1. System-level design review: is this architecture sound?
2. Security audit: where are the vulnerabilities?
3. Scalability concerns: what breaks when data grows 100x?
4. Model routing: are we choosing the right model for each task type?
5. Long-term maintainability: what's the tech debt we're creating?

**Kimi (creative + user experience):**
1. What makes PKM tools delightful (not just functional)?
2. UX patterns from successful consumer apps we should adopt
3. Onboarding flow for a new user — what do they see first?
4. Feature prioritization from user value perspective
5. What are we missing that would make this "sticky"?

---

## 4. ENTERPRISE vs CONSUMER REQUIREMENTS

### Enterprise
| Requirement | Priority | Impl. Approach |
|-------------|----------|----------------|
| Team Spaces / shared KB | P1 | CRDT sync + role-based permissions |
| Audit trail | P1 | Immutable change log in SQLite |
| E2E encryption | P1 | Encrypt sync payloads, keys never leave device |
| SSO/SAML | P2 | OAuth2/SAML2 integration |
| Admin console | P2 | Web dashboard (future) |
| API access | P2 | REST/GraphQL endpoints |
| Compliance export | P2 | GDPR/CCPA self-service export |
| Data residency | P3 | Configurable sync region |

### Consumer
| Requirement | Priority | Impl. Approach |
|-------------|----------|----------------|
| Zero-setup experience | P1 | First-run wizard, defaults sensible |
| Cross-device sync | P1 | E2E encrypted cloud sync |
| Mobile experience | P1 | Responsive Flutter UI |
| AI suggestions | P2 | Hermes-powered context-aware tips |
| Import from other tools | P2 | Markdown, Notion, Obsidian import |
| Offline-first reliability | P1 | All core features work without internet |
| Privacy transparency | P2 | Clear data handling docs |

---

## 5. SCOPE & TIMELINE

### Sprint 0 — Foundation (COMPLETE ✅)
- [x] Basic Flutter app shell
- [x] Context scorer + hot/cold zones
- [x] Memory palace backend
- [x] Hermes agent infrastructure
- [x] Config + key management
- [x] Circuit breaker + failover
- [x] Night Council cron

### Sprint 1 — Core LumenHub (IN PROGRESS)
- [ ] Enhanced memory detail view
- [ ] AI-powered "Ask My Memory"
- [ ] Semantic search integration
- [ ] Import/Export (Markdown, JSON)
- [ ] Settings page with AI configuration
- [ ] Spaced repetition engine

### Sprint 2 — AI Depth
- [ ] Full consult/merge in-app
- [ ] Auto-tagging on creation
- [ ] Memory connection suggestions
- [ ] Daily AI digest
- [ ] Memory palace search integration

### Sprint 3-4 — Polish & Expansion
- [ ] Team features (enterprise)
- [ ] Cloud sync (E2E encrypted)
- [ ] Mobile responsiveness
- [ ] Performance optimization
- [ ] Analytics dashboard
- [ ] Plugin/external API integration