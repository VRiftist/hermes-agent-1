# Hermes API Specification v1

> Last updated: 2026-05-25 | Status: Draft for review
> Purpose: Define the contract between Hermes (backend brain) and all clients (Flutter app, Cursor plugin, CLI, web).

## Architecture Principle

**One brain, many bodies.** Hermes is the single source of intelligence. Every client connects via this API. No client has model logic, memory logic, or context logic — that all lives here.

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Flutter App │  │ Cursor      │  │  CLI / Web  │
│  (primary)   │  │ Plugin      │  │  Interface   │
└──────┬───────┘  └──────┬───────┘  └──────┬──────┘
       │                  │                 │
       └──────────────────┼─────────────────┘
                          │
                   ┌──────▼──────┐
                   │  HERMES API │
                   │  (REST/SSE) │
                   └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
        ┌─────▼────┐ ┌────▼────┐ ┌───▼──────────┐
        │ Model    │ │ Memory  │ │ Context      │
        │ Routing  │ │ Palace  │ │ Orchestrator │
        └──────────┘ └─────────┘ └──────────────┘
```

## Authentication

- All endpoints require `Authorization: Bearer <api_key>` header
- API keys are per-user, scoped to a workspace
- Key rotation: 90-day cycle, enforced by Night Council
- Rate limiting: per-key, configurable (default: 60 req/min)

## Endpoints

### 1. Chat Completion (Primary)

```
POST /v1/chat/completions
```

Standard OpenAI-compatible chat completion. Hermes handles model routing, context assembly, and trimming transparently.

**Request:**
```json
{
  "model": "auto",                    // "auto" = Hermes decides, or explicit model slug
  "messages": [{"role": "user", "content": "..."}],
  "max_tokens": 4096,
  "stream": true,
  "metadata": {
    "client": "cursor",              // "flutter", "cursor", "cli", "web"
    "workspace_id": "ws_abc123",
    "skill_context": null             // set when invoked from a skill
  }
}
```

**Response:**
```json
{
  "model": "qwen3:14b",               // actual model used (transparent routing)
  "choices": [{"message": {"content": "..."}}],
  "usage": {"prompt_tokens": 1234, "completion_tokens": 567, "total_tokens": 1801},
  "context": {
    "tiers_active": ["T0", "T1", "T3"],
    "tokens_used": 8450,
    "tokens_budget": 12000,
    "trimmed": false
  }
}
```

### 2. Memory Query

```
POST /v1/memory/query
```

Search memory palace for relevant facts, episodes, and semantic connections.

**Request:**
```json
{
  "query": "what did we decide about pricing tiers?",
  "limit": 10,
  "types": ["episodic", "semantic", "working"],   // optional filter
  "min_importance": 3,                             // optional threshold
  "context_window": "active"                       // "active" or "all"
}
```

**Response:**
```json
{
  "results": [
    {
      "type": "decision",
      "content": "Pro tier at $20/mo, not $200-300...",
      "source": "session_20260520_143221",
      "importance": 8,
      "tags": ["pricing", "tiers", "decision"],
      "relevance_score": 0.94
    }
  ],
  "total_found": 3,
  "query_time_ms": 47
}
```

### 3. Memory Store

```
POST /v1/memory/store
```

Persist an observation, decision, or fact into the memory palace.

**Request:**
```json
{
  "category": "decision",
  "content": "User confirmed: 8b model is for tool-use fallback, NOT compression",
  "importance": 7,
  "tags": ["architecture", "model-selection", "8b-role"],
  "context_snapshot": {"active_task": "definining skill architecture"}
}
```

### 4. Skills Execute

```
POST /v1/skills/execute
```

Execute a named skill with parameters.

**Request:**
```json
{
  "skill_name": "daily_digest",
  "parameters": {
    "period": "24h",
    "format": "bullet"
  }
}
```

**Response:**
```json
{
  "skill_name": "daily_digest",
  "status": "completed",
  "output": "# Daily Digest — May 25, 2026\n\n## Decisions Made\n- ...\n\n## New Notes\n- ...",
  "model_used": "qwen3:14b",
  "tokens_consumed": 420
}
```

### 5. Skills List

```
GET /v1/skills
```

Returns all available skills with metadata.

**Response:**
```json
{
  "skills": [
    {"name": "daily_digest", "description": "AI-generated daily review", "trigger": "cron", "model": "qwen3:14b"},
    {"name": "auto_tag", "description": "Semantic auto-tagging", "trigger": "on_create", "model": "qwen3:8b"},
    {"name": "context_health", "description": "Context window analysis", "trigger": "on_request", "model": "qwen3:8b"}
  ]
}
```

### 6. Context Status

```
GET /v1/context/status
```

Returns current context window state for `context_chrome` UI.

**Response:**
```json
{
  "tokens_used": 8450,
  "tokens_budget": 12000,
  "tiers": {
    "T0_identity": {"tokens": 1200, "trimmed": false},
    "T1_task": {"tokens": 2100, "trimmed": false},
    "T2_recent": {"tokens": 1800, "trimmed": false},
    "T3_semantic": {"tokens": 1400, "trimmed": false},
    "T4_background": {"tokens": 900, "trimmed": true},
    "T5_tool_output": {"tokens": 650, "trimmed": true},
    "T6_conversation": {"tokens": 400, "trimmed": true}
  },
  "health": "healthy",                    // "healthy", "warning", "critical"
  "last_trim": "2026-05-25T10:23:00Z"
}
```

### 7. Model Status

```
GET /v1/models/status
```

Returns availability of all configured models.

**Response:**
```json
{
  "models": {
    "qwen3:14b": {"provider": "mac-ollama", "status": "available", "latency_ms": 45},
    "qwen3:8b": {"provider": "mac-ollama", "status": "available", "latency_ms": 28},
    "qwen3-coder:30b-a3b": {"provider": "mac-ollama", "status": "available", "latency_ms": 120},
    "deepseek-v4-flash": {"provider": "deepseek", "status": "available", "latency_ms": 340},
    "grok-4.20-reasoning": {"provider": "x-ai", "status": "available", "latency_ms": 520},
    "inclusionai/ring-2.6-1t": {"provider": "openrouter", "status": "available", "latency_ms": 890}
  }
}
```

## Built-in Skills

| Skill | Trigger | Model | Purpose |
|-------|---------|-------|---------|
| `daily_digest` | cron 08:00 | qwen3:14b | Summarizes yesterday's notes, decisions, activity |
| `auto_tag` | on_create | qwen3:8b | Semantic tagging on new notes |
| `context_health` | on_request | qwen3:8b | Reports context window status |
| `memory_search` | on_request | qwen3:14b | Natural language memory query |
| `smart_compose` | on_request | qwen3:14b | AI writing assistance |
| `archive_review` | cron 03:00 | qwen3:14b | Night Council + archive maintenance |
| `consolidate_notes` | on_request | qwen3:14b | Merge related notes into structured knowledge |

## Skill Definition Format

Skills are defined in `~/.hermes/skills/*.json`:

```json
{
  "name": "daily_digest",
  "description": "AI-generated daily review of notes and activity",
  "version": "1.0",
  "trigger": {
    "type": "cron",
    "schedule": "0 8 * * *"
  },
  "model": "qwen3:14b",
  "provider": "mac-ollama",
  "max_tokens": 2048,
  "temperature": 0.3,
  "permissions": ["memory:read", "notes:read"],
  "params": {
    "period": {"type": "string", "default": "24h"},
    "format": {"type": "string", "default": "bullet"}
  }
}
```

## Client Integration

### Cursor Plugin (~200 lines)
1. Connect to Hermes HTTP API on localhost
2. Intercept user prompts → send to `/v1/chat/completions`
3. Display response inline
4. Optional: `/v1/memory/query` for context-aware completions

### Flutter App
1. `hermes_connector` module wraps all endpoints
2. `context_chrome` module polls `/v1/context/status`
3. `memory_palace_ui` module calls `/v1/memory/query` and renders spatial graph

## Decision: Why REST and Not Embedded?

- REST allows multiple clients (Flutter, Cursor, web, mobile) to share one Hermes
- Hermes maintains its own state (memory palace, context window) — embedding would duplicate per client
- Localhost-only by default = no cloud dependency for privacy-sensitive use
- Can be deployed to a server later for multi-device access