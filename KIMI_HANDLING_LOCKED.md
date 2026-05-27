# KIMI HANDLING — LOCKED SPEC

> **Status: LOCKED** — Gerald confirmed. Not dropping, not deprecating.
> **Last updated:** 2026-05-27

---

## 1. CHAIN POSITION

```
Flash (OpenRouter) → Grok (xAI) → Ring @95% (OpenRouter) → 30B shadow → KIMI → Claude Sonnet (final merge)
```

- Kimi sits second-to-last before Claude Sonnet final merge.
- 30B model assigned EXCLUSIVELY to Track 2 (board review chain) — never for routine code gen.

## 2. ACTIVE KEYS

| Role | Env Variable | Status | Notes |
|------|-------------|--------|-------|
| Primary | `KIMI_API_KEY` | `sk-fHRGqhUnVKNzVgxl8w80EMi4lwRFUY7RlTnhhoaDEqtBHihh` — ACTIVE | Rotated in 2026-05-27 |
| Secondary | `KIMI_API_KEY_2` | `sk-yRKAGXTCroVjsMukjE6gRmkLkkCOWZrDN5aAoKsuj40LSARA` — BACKUP | Untested until primary rotates |

**Dead keys:** `sk-k2ww...` (old primary, 401), `sk-fHRGqhU...` (old secondary, replaced)

## 3. ROTATION & RETRY PROTOCOL

### Rotation Triggers (rotate BEFORE backoff)
- **401** → Key invalid → rotate immediately → retry
- **429** → Rate limited → rotate immediately → retry

### Exponential Backoff
| Attempt | Base Delay | Actual (with jitter) |
|---------|-----------|----------------------|
| 1 | 1s | 0.9–1.1s |
| 2 | 2s | 1.8–2.2s |
| 3 | 4s | 3.6–4.4s |
| 4 | 20s | 18–22s |
| 5 | 60s | 54–66s |

MAX_RETRIES: 5 | After success: reset active index to primary.

### Routing (model_routing.py L419-426)
```
if not kimi_client.is_available():
    # Skip Kimi, chain degrades gracefully
    continue
```

## 4. 3-DAY SILENCE RULE

Per Gerald: "Replace the first one and quit bringing Kimi up unless 3 days have gone by without successful access."

- **Successful access** = any API call returning valid JSON (not an error dict)
- **Reset the 3-day clock** on every successful access
- **Alert only after 3 FULL calendar days** since last success
- Alert channel: Telegram via session_watchdog.py
- Phase 2 (code the timer): deferred, designed in spec

## 5. AGGRESSIVE USAGE STRATEGY

**Current balance:** $24.97 | **Refill trigger:** < $10

- Moonshot-v1-8k: ~$0.50/$1.00 per 1M tokens
- At $24.97, capacity: ~25–50M tokens ≈ 300–600 consults
- Strategy: batch project reviews, schedule follow-up timers, let retry backoff handle rate limits naturally
- Cold standby: Claude Sonnet handles all work if both Kimi keys die

## 6. PHASE 2 — DEFERRED (DESIGNED, NOT CODED)

- Session blacklist tracking
- Wall-time cap (3 min abort)
- Context merge buffer across retries
- Claude fallback merge directive
- Balance monitoring automation
- Cost tracking per session

## 7. KEY SYNCHRONIZATION

| File | Location | Synced? |
|------|----------|---------|
| kimi_client.py | scripts/ → linux_prod/ | ✅ Identical (8605 bytes) |
| model_routing.py | scripts/ → linux_prod/ | ✅ Identical |
| .env | Mac → linux_prod/.env | ✅ At deploy time |
| THIS SPEC | ~/.hermes/ → linux_prod/knowledge_base/ | ✅ Synced |