# Architecture Decision — 2026-05-24

## Decision: Return to ring-2.6-1t primary

After experimenting with grok-4.20 (2M ctx) as primary, reverted to ring-2.6-1t.

### Why ring wins as primary

- **Reasoning quality**: ring-2.6-1t is purpose-built for complex reasoning tasks.
- **Cost**: ~$0.01–0.03/session for input-heavy use at 128K ctx. Grok-4.20 at 2M ctx costs ~$2.50/turn when fully filled — 80× more expensive.
- **Context is not free**: A bigger window means every turn bills the entire filled context. 128K is the sweet spot for this workload.

### Final fallback chain

```
ring-2.6-1t (primary, 128K ctx, OpenRouter)
  ↓ failure/rate-limit
deepseek-reasoner-flash (256K ctx, DeepSeek API)
  ↓ failure
grok-4.20 (2M ctx, xAI API)  [3rd tier — provider resilience, not cheap]
  ↓ last resort
ring-2.6-1t (reasoning fallback via ring provider)
```

### Provider separation achieved

| Provider | API Host | Role |
|----------|----------|------|
| OpenRouter | openrouter.ai | Primary |
| DeepSeek | api.deepseek.com | Fallback 1 |
| xAI | api.x.ai | Fallback 2 (separate infra) |
| Local Ollama | localhost:11434/5 | Dormant experiments only |

### 3rd tier rationale

Grok-4.20 at 2M ctx is expensive as an automatic fallback but provides:
- A completely separate API provider (xAI own infra, not OpenRouter)
- Massive context for edge cases exceeding 256K
- The option to manually promote it to primary via config for specific tasks

### Still pending

- End-to-end Telegram test
- `trim_retention` setting (~10 turns recommended)
- 32B coder OOM investigation (dormant)