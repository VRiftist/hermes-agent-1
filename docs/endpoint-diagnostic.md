# Endpoint Diagnostic Report — 2026-05-25

## Kimi K2 — NEW: ALIVE ✅ (via Io Net proxy)

| Field | Value |
|-------|-------|
| **Status** | ✅ ACTIVE — responded via Io Net's provider |
| **Model ID** | `moonshotai/kimi-k2.6-20260420` (self-identifies as "K2.5") |
| **Direct moonshot.cn** | ❌ 401 Unauthorized — key not yet activated on platform |
| **Io Net proxy** | ✅ Working — routed through Io Net infrastructure |
| **Cost** | $0.00042/request (sampled) |
| **How it activated** | Unknown — likely Io Net had the key pre-loaded or activated it on our behalf |
| **Recommendation** | Use Io Net as Kimi proxy OR activate key directly at moonshot.cn |

## Cloud Provider Status Summary

| Provider | Status | Notes |
|----------|--------|-------|
| OpenRouter | ✅ Live | `inclusionai/ring-2.6-1t`, 262K context |
| xAI/Grok | ✅ Live | `grok-4.20-reasoning` |
### Kimi v1-8k
| **Kimi** | ✅ Partial — works via Io Net proxy; direct moonshot.cn key 401 |
| Anthropic | ❌ 404 | Wrong key format or base URL — needs investigation |
| Firecrawl | ❌ 404 | Endpoint likely changed from /v1 |

### Action Items
1. **Kimi direct key**: Attempt manual activation at [moonshot.cn](https://moonshot.cn) — the Io Net proxy works but direct access is cleaner
2. **Anthropic**: Verify API key format (starts with `sk-ant-...`) and try `https://api.anthropic.com/v1`
3. **Firecrawl**: Check if API migrated to `https://api.firecrawl.dev/v1/` — may need account upgrade

## Architecture Decision: Kimi Provider Strategy

Since Kimi works through Io Net's proxy but NOT directly against moonshot.cn, we have two options:

**Option A: Route Kimi through Io Net**
- Pros: Already working, no activation needed
- Cons: Third-party proxy dependency, less control, potential latency

**Option B: Activate key directly at moonshot.cn**
- Pros: Direct connection, full control, lower cost potential
- Cons: Requires platform signup/activation, may take time

**Recommendation**: Use Io Net as primary path for now. Activate direct key in parallel for fallback. Do NOT block on this — Kimi is working.