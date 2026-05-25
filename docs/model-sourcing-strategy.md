# Model Sourcing Strategy for End Users

## The Question
"Where do Hermes users get their AI models from? Do we provide them? Do users bring their own? Do we rely on free tiers?"

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

## The "All-In-One" Long-Term Vision

**Phase 1 (Now → MVP):** Local Ollama + user-supplied cloud keys. User chooses.
**Phase 2 (Launch → 6 months):** Bundled API credits in paid tiers. Users don't need to hunt for keys.
**Phase 3 (Scale → 12 months):** Hermes-as-a-service hosted option — user just opens browser, we handle everything. Models served from our infrastructure.
**Phase 4 (Maturity → 24 months):** Self-hosted fine-tuned models + licensed model weights for specific verticals. True vertical AI.

## Where This Answers Your Question

**"Can we provide the models to people?"**
- Short answer: YES, but not by becoming a model provider. We become a *routing layer* that bundles access.
- Free users: local Ollama only (fast, private, no cost)
- Paid users: bundled cloud credits + local fallback
- We don't need to train models — we aggregate and route

**"Our users getting models" — the product flow:**

```
New user signs up
  → Free tier: "Install Ollama + pull qwen3:8b (one click)" → instant local AI
  → Pro tier: same + bundled API credits → cloud models included
  → Enterprise tier: dedicated API keys + custom models + SLA
```

## Decision: Pin OpenRouter Replacement

✅ Pinned. See `docs/openrouter-independence-roadmap.md` for the phased plan.
Current posture: OpenRouter is an asset, not a liability. Revisit at $5K/mo revenue.

## Outstanding Questions

1. **"Lauderdale"** — Still unresolved. Model name, provider, or codename?
2. **Starter tier ($5/mo)** — What feature boundaries? Local-only + limited cloud credits?
3. **Linux Ollama** — Still blocked on DO droplet provisioning for fleet testing
4. **Mac model cleanup** — 45GB reclaimable, should we proceed with cleanup scripts?