# OpenRouter Independence Roadmap

## Current State
- OpenRouter is used as proxy for `inclusionai/ring-2.6-1t` (quality gate, 262K context)
- OpenRouter key `sk-or-...1e80` is live and validated (HTTP 200)
- OpenRouter takes a markup (~10-20%) on top of underlying provider costs
- Ring-2.6-1t is the ONLY model routed through OpenRouter exclusively

## Why Replace OpenRouter?

| Risk | Impact | Likelihood |
|------|--------|------------|
| Vendor lock-in | Switching cost grows with users | High |
| Margin erosion | 10-20% of API spend goes to OR, not us | Medium |
| Pricing changes | OR could raise rates or deprecate models | Medium |
| Rate limiting | Shared infrastructure, noisy neighbors | Low-Medium |
| Single point of failure | If OR goes down, quality gate breaks | Low |

## Phased Independence Plan

### Phase 0: NOW (No Action Needed)
- OpenRouter is working perfectly
- Don't fix what isn't broken
- **Cost: ~$0.004/1K tokens for Ring** (OR markup included)

### Phase 1: Revenue > $1K/mo — Direct Ring Access
- Subscribe to Ring (Ling) directly via Ant Group / ling.tbox.cn
- Add direct API key alongside OpenRouter as parallel path
- Update `model_routing.py` to prefer direct, fall back to OR
- **Savings: Eliminate OR markup on Ring (~10-15%)**
- **Effort: ~2 hours** — add provider endpoint, test, route

### Phase 2: Revenue > $5K/mo — Build Quality Gate Alternatives
- Self-host an equivalent open-source verification model:
  - **Llama 3.1 70B** or **Qwen2.5 72B** at Q4_K_M (~45GB VRAM)
  - Linux RTX 3060 (12GB) too small → need A100 80GB, H100, or 2×A6000
  - Alternative: **DeepSeek-V2/V3** via direct API (cheaper than Ring)
- Implement multi-model voting: 2 of 3 quality gate models must agree
- **Savings: Eliminate Ring dependency entirely for non-critical checks**
- **Effort: ~8 hours + hardware investment**

### Phase 3: Revenue > $20K/mo — Full Provider Independence
- Direct API keys for ALL providers:
  - DeepSeek ✅ (already direct)
  - xAI/Grok ✅ (already direct)
  - Ring via direct Ling subscription (Phase 1)
  - Kimi via direct moonshot.cn activation
  - Anthropic (when key sorted)
- OpenRouter becomes emergency fallback ONLY
- **Savings: 15-25% total API spend reduction**
- **Effort: ~16 hours** — integration, testing, failover logic

### Phase 4: Revenue > $50K/mo — Self-Hosted Baseline
- Rent/mBuy dedicated GPU instances (Lambda Labs, CoreWeave)
- Self-host Qwen3-14B, Qwen3-8B, + quality verification model
- Cloud APIs become burst capacity only
- **Savings: 60-70% of current API costs**
- **Effort: ~40 hours + $2-5K/month infrastructure**

## Key Technical Dependencies

| Blocker | Solution |
|---------|----------|
| Linux Ollama offline | Provision DO droplet (pending IP) |
| Ring direct access | Create account at ling.tbox.cn |
| Kimi direct access | Platform activation at moonshot.cn |
| GPU budget for self-hosting | Revenue-dependent (Phase 4) |

## Decision Framework

**Escalation triggers** for each phase:

```
Monthly Revenue → Action
─────────────────────────────────────────────
< $1K/mo           → Stay with OpenRouter (Phase 0)
$1K - $5K/mo       → Phase 1: Direct Ring parallel path
$5K - $20K/mo      → Phase 2: Alternative quality gates
$20K - $50K/mo     → Phase 3: All-direct providers
> $50K/mo          → Phase 4: Self-hosted baseline
```

## Recommendation

**Don't do anything now.** OpenRouter is an asset, not a liability, at this stage. The plan is:

1. **Document the dependency** (done — this file)
2. **Monitor monthly API spend** via `key_guardian.py` (can add OpenRouter spend tracking)
3. **Build Phase 1 capability proactively** — add Ring direct API config as inactive, flip a switch when revenue triggers it
4. **Revisit quarterly** — tie to Night Council review cycle

This keeps us shipping now while having a clear, cost-justified path to independence.