# Model Access Patterns — Command Reference

> Every model call in the Hermes system follows one of these patterns.
> Use this doc to understand how each model is invoked, what keys it needs,
> and how to debug failures.

---

## Provider Key Map

| Provider | Env Var | Endpoint | Key Format | Where to Get |
|----------|---------|----------|------------|--------------|
| DeepSeek | `DEEPSEEK_API_KEY` | `api.deepseek.com/v1` | `sk-...` | platform.deepseek.com |
| xAI/Grok | `XAI_API_KEY` | `api.x.ai/v1` | `xai-...` OR `x...<long>` | console.x.ai → API Keys |
| OpenRouter | `OPENROUTER_KEY_1` | `openrouter.ai/api/v1` | `sk-or-...` | openrouter.ai/settings/keys |
| Kimi | `KIMI_API_KEY` + `KIMI_API_KEY_2` | `api.moonshot.cn/v1` (DIRECT) | `sk-N...` OR `sk-sH...` | platform.moonshot.cn |
| Ollama (Mac) | None | `localhost:11434/v1` | N/A | Local |
| Ollama (Linux) | None | `192.168.1.230:11434/v1` | N/A | Local (offline) |

---

## Model: Grok-4.20-reasoning (xAI)

**Role**: User pain points, X/Twitter discourse analysis, strategic reasoning
**Endpoint**: `https://api.x.ai/v1/chat/completions`
**Auth**: `Bearer {XAI_API_KEY}`
**Access pattern** (Python):
```python
import urllib.request, json

url = "https://api.x.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {xai_key}",
    "Content-Type": "application/json",
}
body = json.dumps({
    "model": "grok-4.20-reasoning",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 8192,
})
req = urllib.request.Request(url, data=body.encode(), headers=headers)
with urllib.request.urlopen(req, timeout=180) as resp:
    result = json.loads(resp.read().decode())
    content = result["choices"][0]["message"]["content"]
```
**CLI test**: `curl -H "Authorization: Bearer $XAI_API_KEY" https://api.x.ai/v1/models`
**Common failures**:
- HTTP 400: Key is a Grok-chat key, not API key → get proper API key from console.x.ai
- HTTP 401: Key expired or revoked → regenerate at console.x.ai
- HTTP 429: Rate limited → backoff and retry

---

## Model: DeepSeek v4-pro / v4-flash

**Role**: Detailed architecture audit, code analysis, "anal-retentive" detail work
**Endpoint**: `https://api.deepseek.com/v1/chat/completions`
**Auth**: `Bearer {DEEPSEEK_API_KEY}`
**Access pattern** (Python):
```python
url = "https://api.deepseek.com/v1/chat/completions"
headers = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
body = json.dumps({
    "model": "deepseek-v4-pro",        # or "deepseek-v4-flash" for cheaper/faster
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 8192,
})
```
**CLI test**: `curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models`
**Common failures**:
- HTTP 401: Platform activation incomplete → visit platform.deepseek.com, complete payment/terms
- HTTP 400: Wrong model name → use `deepseek-v4-pro` or `deepseek-v4-flash`

---

## Model: Ring-2.6-1t (OpenRouter)

**Role**: Quality gate, final architectural review, verification
**Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
**Auth**: `Bearer {OPENROUTER_KEY_1}`
**Model slug**: `inclusionai/ring-2.6-1t` (NOT `ring/ring-2.6-1t`)
**Access pattern** (Python):
```python
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {or_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://lumenhub.ai",
    "X-Title": "LumenHub Blueprint Review",
}
body = json.dumps({
    "model": "inclusionai/ring-2.6-1t",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 8192,
})
```
**CLI test**: `curl -H "Authorization: Bearer $OPENROUTER_KEY_1" https://openrouter.ai/api/v1/models`
**Common failures**:
- HTTP 401: Key invalid or exhausted → regenerate at openrouter.ai/settings/keys
- HTTP 500: Model temporarily unavailable → retry with backoff

---

## Model: Kimi v1-8k (Moonshot DIRECT)

**Role**: Creative/design/UX judgment, aesthetic sense, multilingual
**Endpoint**: `https://api.moonshot.cn/v1/chat/completions` (DIRECT, NOT OpenRouter proxy)
**Auth**: `Bearer {KIMI_API_KEY}`
**Model**: `moonshot-v1-8k`
**Special**: Uses `kimi_client.py` with built-in dual-key rotation + exponential backoff
**Patience mode**: Up to 50 retries with 30s–300s backoff (potentially hours)

**Direct access pattern** (Python):
```python
import sys
sys.path.insert(0, "/Users/lumenhubai/.hermes/scripts")
from kimi_client import chat_completion

result = chat_completion(
    messages=[{"role": "user", "content": prompt}],
    model="moonshot-v1-8k",
    temperature=0.7,
    max_tokens=4096,
)
if "error" in result:
    print(f"Kimi error: {result['error']}")
else:
    content = result["choices"][0]["message"]["content"]
```
**CLI test**: `python3 ~/.hermes/scripts/kimi_client.py` (runs without making API calls)
**Common failures**:
- "NO_KIMI_KEY": Key not found or masked in .env → check `KIMI_API_KEY` and `KIMI_API_KEY_2`
- HTTP 401: Platform auth incomplete → visit platform.moonshot.cn
- HTTP 429: Rate limited → client auto-retries with backoff + key rotation

---

## Model: qwen3:14b (Ollama, Mac)

**Role**: Default local general-purpose model
**Endpoint**: `http://localhost:11434/v1`
**Auth**: None (local)
**Access pattern**:
```python
url = "http://localhost:11434/v1/chat/completions"
headers = {"Content-Type": "application/json"}
body = json.dumps({
    "model": "qwen3:14b",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 8192,
})
```
**CLI test**: `curl http://localhost:11434/v1/models`
**Verify**: `ollama list` on Mac terminal

---

## Model: qwen3-coder:30b-a3b (Ollama, Mac)

**Role**: Dedicated reasoning/consult/merge model, code generation
**Endpoint**: `http://localhost:11434/v1`
**Auth**: None (local)
**Access pattern**:
```python
url = "http://localhost:11434/v1/chat/completions"
body = json.dumps({
    "model": "qwen3-coder",           # matches Ollama model tag
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 16384,
})
```
**CLI test**: `curl http://localhost:11434/v1/generate -d '{"model":"qwen3-coder","prompt":"explain recursion"}'`

---

## Quick Diagnostic Commands

```bash
# Check all local Ollama models (Mac)
ollama list

# Test each cloud API key in one shot
curl -s -H "Authorization: Bearer $XAI_API_KEY" https://api.x.ai/v1/models | python3 -m json.tool | head -20
curl -s -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models | python3 -m json.tool | head -20
curl -s -H "Authorization: Bearer $OPENROUTER_KEY_1" https://openrouter.ai/api/v1/models | python3 -m json.tool | head -20

# Run Hermes self-test
cd ~/.hermes && python3 scripts/full_selftest.py

# Check key guardian health report
cat ~/.hermes/logs/model_health.json | python3 -m json.tool

# Run blueprint review manually
python3 ~/.hermes/scripts/run_full_review.py
```