# Model Sourcing — Decision Log (2026-05-25)

## Key Decisions

### 1. Ollama = Local Only (Confirmed)
- Ollama is a local inference engine, NOT a cloud service
- No "Ollama Pro cloud models" in our current stack
- Users run qwen3:14b/8b locally via `ollama pull`
- Zero cost, zero API keys, zero cloud dependency

### 2. OpenRouter Free Tier = NEW OPPORTUNITY
- 50+ free models, ~100K tokens/day per key
- Could serve Free-tier users without any local Ollama install
- Best use: non-critical tasks (auto-tag, summarize, memory search)
- Risk: rate limits, model availability changes

### 3. Ollama Pro = NOT for Hermes Production
- $20/mo per user subscription model
- Same CLI interface as local — easy integration
- Why we skip it: vendor lock-in, privacy leak, cost at scale
- Why we might use it: friction-free cloud models for free-tier users
- **Decision: Defer. Revisit when user count justifies the cost analysis**

### 4. Cloud API Cost Reality
- Hermes' model routing already optimizes cost by task type
- Blended cost per user: ~$2.25/mo at 50K tokens/day avg
- Pro tier at $10/mo = ~77% margin before compute overhead
- OpenRouter's free tier could make Free users $0 cost to us

### 5. "Where Do Users Get Models?" — ANSWERED
```
Free  → OpenRouter free tier (0 setup) OR local Ollama
Pro   → Bundled API credits + local Ollama 
Enterprise → Dedicated keys + custom models
```