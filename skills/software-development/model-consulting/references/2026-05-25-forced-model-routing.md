# Forced-Model Routing & Multi-Model Review Pipeline

> Discovered/built: 2026-05-25. | Skill: model-consulting

## Forced-Model Override Pattern

When a task explicitly requires a specific model, **do not rely on `classify_task()`**. The classifier maps tasks to generic categories which can route to the wrong model or a local fallback.

### Root Cause

During the 2026-05-25 blueprint review attempt, `classify_task()` mapped all three review prompts → "general" → routed to `mac-ollama:qwen3:14b` instead of the intended cloud models. Fix: bypass classification entirely when the target model is known.

### Implementation

`select_model()` now accepts `force_provider` and `force_model` keyword arguments:

```python
from model_routing import select_model

# Force a specific model, bypassing classification
config = select_model("general", prompt, force_provider="x-ai", force_model="grok-4.20-reasoning")

# Force by provider only
config = select_model("general", prompt, force_provider="deepseek")
```

### When to Use

- Blueprint/product reviews targeting a specific model's analytical style
- Comparing how different models approach the same problem
- Any task where persona matters more than cost optimization

### Anti-Pattern

Do NOT use forced override for everyday operational tasks. The automatic classifier optimizes cost, latency, and capability matching. Forced overrides are for deliberate, one-off expert consultation.

---

## Kimi Patience Protocol

Kimi (Moonshot) is a "temperamental artist" — transient 429s and intermittent 401s are expected.

### Retry Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| MAX_RETRIES | 50 | May take hours during peak load |
| BASE_DELAY | 30s | Aggressive initial backoff |
| MAX_DELAY | 300s | Cap at 5 minutes between attempts |
| Key rotation | On 401/429 | Tries secondary key before backing off |

### Key Constraint

Kimi uses the **DIRECT** `api.moonshot.cn` endpoint, NOT the OpenRouter proxy.

---

## Multi-Model Review Pipeline

A formalized workflow for structured expert input from multiple models on a single artifact.

### Script: `scripts/run_full_review.py`

1. Define review tasks — each specifies: target model, provider, API call, purpose, prompt
2. Execute sequentially — each calls provider API directly with forced routing
3. Compile results — auto-generates markdown report with coverage matrix
4. Log to memory palace

### .env Key Masking Pitfall

DeepSeek and Grok keys in `.env` were `***` (3-char placeholders) — never populated. Config.yaml references resolved to literal `***` strings, which providers correctly rejected.

**Fix verification:**
```python
env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if "KEY" in k:
                print(f"{k}: len={len(v)} masked={'***' in v}")
```