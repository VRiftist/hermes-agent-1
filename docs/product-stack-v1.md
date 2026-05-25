# LumenHub Product Stack (v1)

> Generated: 2026-05-25 | Status: Architecture Blueprint
> AI Backend: Hermes Agent (local-first, cloud fallback)

## Stack Overview

```
┌─────────────────────────────────────────────────┐
│              LUMENHUB PRODUCT STACK              │
├─────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────┐  │
│  │           Flutter 3.44 + Riverpod          │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐ │  │
│  │  │ Core │ │ AI   │ │ Sync │ │ Platforms │ │  │
│  │  │      │ │      │ │      │ │          │ │  │
│  │  └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘ │  │
│  │     │        │        │           │       │  │
│  │  ┌──▼────────▼────────▼───────────▼────┐ │  │
│  │  │         Hermes Agent Backend         │ │  │
│  │  │  Model Routing | Context | Memory    │ │  │
│  │  └──────────────────────────────────────┘ │  │
│  │           │                    │            │  │
│  │     ┌─────▼─────┐    ┌────────▼────────┐   │  │
│  │     │ Local LLMs│    │  Cloud Models    │   │  │
│  │     │ qwen3     │    │ DeepSeek|Grok|Ring│   │  │
│  │     │ Ollama    │    │ OpenRouter       │   │  │
│  │     └───────────┘    └─────────────────┘   │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Core

**Priority:** 1 | **Status:** planned

**Description:** Flutter 3.44 + Riverpod BLoC state management

### Modules

- `app_shell (navigation, routing, theme)`
- `auth_flow (onboarding, account linking, biometrics)`
- `home_dashboard (daily review, quick capture, AI suggestions)`
- `note_editor (rich text, markdown, voice, sketches)`
- `memory_palace_ui (spatial memory visualization)`
- `context_chrome (shows active context, trimming status)`

---

## Ai Backend

**Priority:** 2 | **Status:** planned

**Description:** Hermes Agent integration — model routing, context, memory

### Modules

- `hermes_connector (API bridge to Hermes Agent)`
- `smart_compose (AI writing assistance)`
- `auto_tag (semantic tagging on create)`
- `daily_digest (AI-generated daily review)`
- `ask_memory (natural language memory search)`
- `context_manager (tier visibility, manual trim controls)`

---

## Tiers

**Priority:** 3 | **Status:** planning

**Description:** Feature gating by subscription tier

### Tier Definitions

- **Free**: Basic note-taking, local only, 2K context, no AI features, 50 notes max
- **Starter**: $X/mo — AI compose, auto-tag, 8K context, 500 notes
- **Pro**: $Y/mo — All AI features, 16K context, unlimited notes, memory palace
- **Enterprise**: $Z/mo — Team spaces, admin panel, API access, priority models

---

## Sync Infra

**Priority:** 4 | **Status:** planned

**Description:** Cross-device synchronization

### Modules

- `sync_engine (CRDT or operational transform)`
- `cloud_relay (encrypted sync server)`
- `offline_queue (conflict resolution)`
- `device_registry (device management)`

---

## Platforms

**Priority:** 5 | **Status:** ios/android pending

**Description:** Target platforms and deployment

### Platform Targets

- **Macos**: macOS desktop — primary dev target
- **Windows**: Windows desktop — Flutter desktop
- **Ios**: iOS — Flutter mobile, TestFlight beta
- **Android**: Android — Flutter mobile, Play Store
- **Web**: PWA — Flutter web, progressive enhancement

---

## Build Sequence

```
Phase 1 (Weeks 1-4): Core MVP
  → app_shell, note_editor, home_dashboard
  → Basic Hermes connector (manual trigger)
  → Free tier only

Phase 2 (Weeks 5-8): AI Integration
  → smart_compose, auto_tag, ask_memory
  → Tiered feature gating (Free/Starter/Pro)
  → Daily digest + context chrome

Phase 3 (Weeks 9-12): Sync + Platforms
  → sync_engine, cloud_relay
  → iOS + Android builds
  → Enterprise tier + admin panel

Phase 4 (Weeks 13-16): Polish + Launch
  → Memory palace UI
  → Performance optimization
  → Marketing blitz + launch
```
