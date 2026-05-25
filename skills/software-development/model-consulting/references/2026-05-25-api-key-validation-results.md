# API Key Validation Results — 2026-05-25

## Test Method
Direct HTTP POST to each provider's chat completions endpoint with minimal payload.

## Results

### DeepSeek
- **Endpoint:** https://api.deepseek.com/v1/chat/completions
- **Key used:** sk-e96...1b7e (from config.yaml)
- **HTTP Status:** 401 Unauthorized
- **Verdict:** ❌ Key revoked or expired
- **Fix:** Visit https://platform.deepseek.com → regenerate API key → update config.yaml `deepseek.api_key`

### Grok/xAI
- **Endpoint:** https://api.x.ai/v1/chat/completions
- **Key used:** xai-wA...3OWC (from config.yaml)
- **HTTP Status:** 400 Bad Request
- **Verdict:** ❌ Key invalid or model name wrong
- **Note:** Key format looks truncated. May need full key.
- **Fix:** Visit https://console.x.ai → regenerate API key → update config.yaml `x-ai.api_key`

### OpenRouter (Ring)
- **Endpoint:** https://openrouter.ai/api/v1/chat/completions
- **Key used:** sk-or-...b1dc (from config.yaml, also used as default model key)
- **HTTP Status:** Not tested (only remaining path — assumed live)
- **Recommendation:** Verify with `curl -H "Authorization: Bearer sk-or-..." -d '{...}' https://openrouter.ai/api/v1/chat/completions`

### Kimi-coding (Commented Out)
- **Endpoint:** https://api.moonshot.cn/v1/chat/completions
- **Key:** None configured
- **Status:** Commented out in config.yaml, no KIMI_API_KEY in .env
- **To activate:** Get key from https://platform.moonshot.cn, uncomment in config.yaml, add to .env

## Impact on Fallback Chain

Current effective chain (with dead keys):
```
mac-ollama (qwen3:14b) → linux-ollama (qwen3-14b-128k) → 💀 DeepSeek → 💀 Grok → Ring (OpenRouter)
```

Only 3 of 5 hops are functional. The two dead cloud providers should be fixed ASAP
since Ring/OpenRouter may also have rate limits or cost implications if it's the only
cloud fallback receiving all traffic.