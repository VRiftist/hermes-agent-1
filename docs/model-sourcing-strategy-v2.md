# Model Sourcing Strategy for End Users (v2)

## The Question
"Where do Hermes users get their AI models? Do we provide them? Do users bring their own? Do we rely on free tiers?"

## Current Architecture (Developer/Beta)

```
┌──────────────────────────────────────────────┐
│             HERMES AGENT (coordinator)        │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │  model_routing.py (task-classified)     │ │
│  │  consult/merge/circuit-breaker          │ │
│  └─────────────────────────────────────────┘ │
│         │              │             │        │
│    ┌────▼────┐   ┌─────▼────┐   ┌───▼────┐  │
│    │ LOCAL   │   │  CLOUD   │   │ QUALITY│  │
│    │ Ollama  │   │ APIs     │   │ GATE   │  │
│    │ qwen3:  │   │ DeepSeek │   │ Ring   │  │
│    │ 14b/8b  │   │ Grok     │   │ 262K   │  │
│    └─────────┘   └──────────┘   └────────┘  │
└──────────────────────────────────────────────┘
```

## Tier 1: Local Models (Ollama — Free, No Account Needed)

**Who provides it:** User installs Ollama themselves, pulls models.
**Cost to user:** $0 (electricity only)
**Cost to us:** $0
**Models available:** qwen3:14b, qwen3:8b, qwen3-coder:30b-a3b, llama3, etc.
**Context:** 8K-16K tokens (varies by model)

**Key point:** Ollama is NOT a cloud service. It's a local inference engine. There are no "Ollama Pro cloud models." Every model runs on the user's own hardware. Think of it like a local database — data never leaves the machine.

**For the product:** We can script `brew install ollama && ollama pull qwen3:8b` as part of a one-click installer. Users get local AI with zero cost, zero API keys, zero cloud dependency.

## Tier 2: Cloud APIs (API Keys — User Brings Their Own)

**Who provides it:** User obtains API keys from providers.
**Cost to user:** Pay-per-use (varies by provider)
**Cost to us:** $0 (we don't pay)
**Providers in chain:**

| Provider | Cheapest Model | Approx Cost/1M tokens | Context |
|----------|---------------|----------------------|---------|
| DeepSeek | v4-flash | ~$0.14 input / $0.28 output | 32K+ tokens |
| xAI | Grok-4-mini | ~$0.10 input / $0.40 output | 8K tokens |
| Ant Group | Ring-2.6-1t (via OpenRouter) | ~$0.50 input / $2.00 output | 262K tokens |
| (Other) | Many options via OpenRouter | varies | varies |

**For the product:** Users paste their keys into `.env` or a settings UI. We route intelligently.

## Tier 3: Bundled API Keys (We Provide — For Paid Users)

**Who provides it:** We (LumenHubAI) hold master API keys. User's requests go through our proxy.
**Cost to user:** Included in subscription
**Cost to us:** Real API costs per request, but bulk/margin pricing applies
**For the product:** This is the SaaS model. User pays $10/mo, we bundle a set amount of API credits. When credits run out, they upgrade tier or fall back to local-only.

**Revenue math example:**
- User on Pro ($10/mo) → avg 50K tokens/day
- Cost: ~50K × $0.0015 (blended avg) = ~$0.075/day = ~$2.25/mo
- **Margin: ~77%** before inference compute

## NEW: OpenRouter Free Tier (Discovered 2026-05-25)

**Important update:** OpenRouter now offers **50+ free models** with ~100K tokens/day per API key, with zero billing required. This includes models like Qwen variants, Llama, Mistral, and other open-weight models.

**What this means for Hermes:**
- We could route non-critical tasks (auto-tag, summarize, memory search) through OpenRouter's free tier
- The Ring quality gate would still use a paid model
- This could **eliminate API costs for the Free tier entirely** — no Ollama install required, just use OpenRouter's free models
- Rate limits (~100K tokens/day) would need management in the context orchestrator

**Caveats:**
- Free tier is rate-limited and could change without notice
- Not suitable for heavy workloads (agents, long conversations)
- We need to build a "free tier router" that stays within quotas
- OpenRouter's free model list changes — we need to monitor availability

## NEW: Ollama Pro ($20/mo) — Cloud Models via Ollama

**Important update:** Ollama launched a paid cloud tier in March 2026. Key details:

| Feature | Ollama Local (Free) | Ollama Pro ($20/mo) |
|---------|-------------------|---------------------|
| Models | Models on your machine | Cloud-hosted models (GLM-5.1, Kimi K2.6, DeepSeek v4, etc.) |
| Context | 8K-16K typical | Up to 1M tokens on some models |
| Privacy | 100% local | Your data goes to Ollama's servers |
| Cost | $0 | $20/mo |
| Setup | `ollama pull model` | Same CLI — `ollama run model:cloud` |

**Why this matters for Hermes:**
- Ollama's cloud models use the **exact same API** as local models — just change the model name
- "Cloud" models like `kimi:cloud` or `deepseek-v4-pro:cloud` can be added instantly — no API key management
- Context windows up to 1M tokens — far beyond what local hardware can handle
- Tool calling and vision support built in

**Should Hermes use Ollama Pro?**
- **NO for production/enterprise** — Vendor lock-in, privacy concerns, $20/user/mo adds up at scale
- **YES for free-tier users** — If we bundle `kimi:cloud` or `qwen3:cloud` as free-tier models, users get cloud AI with zero API key management
- **Consideration:** Ollama Pro is per-user subscription, not per-API-key. At scale this is expensive vs. our own API keys

## The "All-In-One" Long-Term Vision

**Phase 1 (Now → MVP):** Local Ollama + user-supplied cloud keys OR OpenRouter free tier. User chooses.
**Phase 2 (Launch → 6 months):** Bundled API credits in paid tiers. Users don't need to hunt for keys. OpenRouter free tier used for non-critical tasks.
**Phase 3 (Scale → 12 months):** Hermes-as-a-service hosted option — user just opens browser, we handle everything. Models served from our infrastructure.
**Phase 4 (Maturity → 24 months):** Self-hosted fine-tuned models + licensed model weights for specific verticals. True vertical AI.

## Where This Answers Your Question

**"Can we provide the models to people?"**
- Short answer: YES, via multiple strategies:
  - Free users: Local Ollama OR OpenRouter free tier (zero cost to us)
  - Mid users: Ollama Pro cloud models (users pay $20/mo directly to Ollama)
  - Paid users: Bundled API credits (we pay ~$2/mo per user, charge $10/mo)
  - Enterprise: Dedicated keys + custom routing

**"Are we using Ollama's free cloud models right now?"**
- No. We use Ollama for local inference only. Ollama Pro cloud models exist but we haven't integrated them.
- We COULD integrate OpenRouter's free tier for non-critical tasks — this is the better free option since it requires no user setup.

## Decision: Pin OpenRouter Replacement

✅ Pinned. See `docs/openrouter-independence-roadmap.md` for the phased plan.
Current posture: OpenRouter is an asset, not a liability. Revisit at $5K/mo revenue.

## Outstanding Questions

1. **"Lauderdale"** — Still unresolved. Model name, provider, or codename?
2. **Starter tier ($5/mo)** — What feature boundaries? Local-only + limited cloud credits?
3. **Linux Ollama** — Still blocked on DO droplet provisioning for fleet testing
4. **Mac model cleanup** — 45GB reclaimable, should we proceed with cleanup scripts?
5. **OpenRouter free tier integration** — Should we build a free-tier router using OpenRouter's free models? This would eliminate "no API key" friction for Free users.
6. **Ollama Pro: use or skip?** — Decision needed. Pro: easy cloud models for users, Con: vendor lock-in, $20/user/mo at scale.