# Config Rewiring Session — 2026-05-24

## What Changed

Cloud-first fallback chain adopted.
Previous: `mac-ollama → linux-ollama → deepseek → ring-2.6-1t`
New: `ring-2.6-1t (primary) → deepseek-reasoner-flash (fallback) → x-ai/grok-4.20 (pending key)`

Local Ollama models removed from fallback chain, kept dormant for code grinding.

## Config Changes Applied

```
model.default = "ring-2.6-1t"
model.context_length = 131072
model.fallback = "deepseek-reasoner-flash"
model.fallback_providers = "deepseek,ring-2.6-1t"
providers.ring-2.6-1t.api_key = "sk-or-v1-...e220"
providers.deepseek.api_key = "sk-3fe...ba84"
providers.deepseek.models.deepseek-reasoner-flash.context_length = 262144
```

## Key Decision

Every API call bills the full conversation context as input tokens. Cost at 128K context is ~$0.001-0.013/turn depending on model. 128K primary budget prevents runaway costs while allowing rich conversations.

## Bugs Found

- Dot notation `providers.ring-2.6-1t.api_key` created nested YAML block `ring-2 > 6-1t > api_key`. Cleaned up.

## Still Pending

- xAI/Grok API key needed
- Telegram bot 401 — needs @BotFather replacement
- Duplicate API key cleanup in config.yaml
- Local 32B bisection testing deferred indefinitely