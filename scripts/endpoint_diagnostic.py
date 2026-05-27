#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
DIAGNOSTIC: Test all 7 endpoints with correct URLs.
"""
import os, sys, json, urllib.request, time

sys.path.insert(0, "/Users/lumenhubai/.hermes/scripts")
env = {}
with open("/Users/lumenhubai/.hermes/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

def test(name, url, method="GET", body=None, headers=None, timeout=30):
    if headers is None:
        headers = {}
    start = time.time()
    try:
        body_bytes = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return f"OK ({resp.status}): {json.dumps(data)[:300]}", time.time()-start
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode()[:500]
        except:
            err_body = ""
        return f"HTTP {e.code}: {err_body[:200]}", time.time()-start
    except Exception as e:
        return f"ERROR: {str(e)[:200]}", time.time()-start

print("=" * 70)
print("  ENDPOINT DIAGNOSTIC — Detailed Failure Analysis")
print("=" * 70)

# 1. OpenRouter
r, t = test("OpenRouter Models", "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {env['OPENROUTER_KEY_1']}",
             "HTTP-Referer": "https://lumenhub.ai"})
print(f"\n1. OpenRouter: {r} [{t:.2f}s]")

# 2. DeepSeek — chat completions
r, t = test("DeepSeek Chat", "https://api.deepseek.com/v1/chat/completions",
    body={"model": "deepseek-chat", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
    headers={"Authorization": f"Bearer {env['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"})
print(f"2. DeepSeek:   {r} [{t:.2f}s]")

# 3. Anthropic — try different endpoint formats
r1, t1 = test("Anthropic /v1/messages", "https://api.anthropic.com/v1/messages",
    body={"model": "claude-3-sonnet-20240229", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]},
    headers={"x-api-key": env['ANTHROPIC_API_KEY'], "anthropic-version": "2023-06-01", "Content-Type": "application/json"})
print(f"3. Anthropic:  {r1} [{t1:.2f}s]")

# 4. Kimi — try different models and endpoints
r2, t2 = test("Kimi /v1/chat", "https://api.moonshot.cn/v1/chat/completions",
    body={"model": "moonshot-v1-8k", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10},
    headers={"Authorization": f"Bearer {env['KIMI_API_KEY']}", "Content-Type": "application/json"})
print(f"4. Kimi:       {r2} [{t2:.2f}s]")

# 5. xAI / Grok
r3, t3 = test("xAI / Grok", "https://api.x.ai/v1/chat/completions",
    body={"model": "grok-4.20-reasoning", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10},
    headers={"Authorization": f"Bearer {env['XAI_API_KEY']}", "Content-Type": "application/json"})
print(f"5. xAI/Grok:   {r3} [{t3:.2f}s]")

# 6. Firecrawl — list available endpoints
r4, t4 = test("Firecrawl Health", "https://api.firecrawl.dev/v1/health",
    headers={"Authorization": f"Bearer {env['FIRECRAWL_API_KEY']}"})
print(f"6. Firecrawl:  {r4} [{t4:.2f}s]")

# 7. Brave
r5, t5 = test("Brave Search", "https://api.search.brave.com/res/v1/web/search?q=test",
    headers={"Accept": "application/json", "X-Subscription-Token": env['BRAVE_API_KEY']})
print(f"7. Brave:      {r5} [{t5:.2f}s]")

print(f"\n{'='*70}")
print("  DIAGNOSIS:")
print("  Anthropic 404 → Wrong model name or endpoint version")
print("  Kimi 401 → Key invalid or model not activated on platform")
print("  Firecrawl 404 → Endpoint may require /v1/crawl not /v1/health")
print(f"{'='*70}")