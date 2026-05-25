---
name: hermes-gateway-ops
category: devops
description: Hermes gateway configuration, hygiene auditing, key injection, fallback chain management, and recovery procedures. Updated for local-first 5-model architecture (2026-05-25).
tags:
  - "telegram"
  - "config"
  - "fallback-chain"
  - "local-first"
version: "2.7"
updated: "2026-05-25T20:00"
related_skills:
  - hermes-agent
  - hermes-infrastructure
  - remote-access
  - inference-architecture
  - key-management
references:
  - references/config-yaml-key-injection-issues.md
  - references/session-2026-05-24-notes.md
  - references/2026-05-25-architecture-overview.md
  - references/config-hygiene-20260524.md
  - references/2026-05-24-telegram-401-debugging.md
  - references/2026-05-24-rewiring-session.md
  - references/2026-05-25-session-wiring-update.md
  - references/2026-05-25-model-specs-confirmed.md
---

# Hermes Gateway Operations (v2 — Local-First 5-Model Architecture)

End-to-end management of Hermes Agent gateway configuration, credential injection, fallback chain tuning, and post-change verification.

## When to Use This Skill

- Injecting or rotating API keys (Telegram, OpenRouter, DeepSeek, Grok)
- Rebuilding or repairing `config.yaml` structure
- Diagnosing gateway startup failures and polling conflicts
- Auditing `.env` file integrity
- Managing fallback chain ordering (local-first → cloud by capability)
- Verifying model connectivity across Mac/Linux/Cloud tiers
- Setting up new cron jobs or systemd/launchd services

---

## Current Architecture (2026-05-25)

**This is a local-first architecture.** Local models are primary; cloud is an **upgrade path**, not a default.

```
ACTIVE 5-MODEL CHAIN (all verified live, 2026-05-25):

Tier 1 (Primary)    mac-ollama       qwen3:14b         16K    Free    Mac M2 32GB
Tier 2 (Heavy)      linux-ollama*    qwen3:8b          16K    Free    Linux RTX3060
Tier 2a (Aggressiv) linux-ollama*    qwen3:8b Q3_K_M   32-64K Free    Linux RTX3060
Tier 3 (Reasoning)  deepseek ✅      v4-flash           32K   $0.14   Cloud
Tier 4 (Creative)   x-ai             grok-4.20-reason  16K   $1.25   Cloud
Tier 5 (Quality)    openrouter       ring-2.6-1t       262K   $0.88   Cloud

DEAD: kimi-coding (moonshot, 401 — cold standby)
* Linux offline — Hetzner retired, Digital Ocean pending

Key discovery: Ring-2.6-1t actual context is 262K, not 16K on model card.
```

### Corrected Model Chain (2026-05-25 Audit)

| Change | Before | After | Reason |
|--------|--------|-------|--------|
| Linux model | qwen3-14b-128k / 128K | qwen3:8b / 16K (safe) | VRAM audit: 14B barely fits with no context headroom |
| Linux aggressive | (not configured) | qwen3:8b Q3_K_M / 32-64K | Uses only 3.5GB VRAM, leaves room for KV |
| DeepSeek key | Old key, 401 | `sk-bca71f6fd...` / HTTP 200 | New key pre-activated with credit |
| Ring context | Assumed 16K | 262K (confirmed via API) | OpenRouter model card was wrong |

### config.yaml Structure Rules

1. `model.default` = highest-priority model for the gateway
2. `model.fallback` = first fallback (set to `deepseek-v4-flash`)
3. `model.fallback_providers` = ordered chain of provider names — **NO duplicates** (the double-entry bug on line 57 was fixed)
4. Each provider in `providers:` section lists its models with context lengths
5. API keys stored in top-level or provider-level `api_key` fields
6. **Never use `hermes config set` for provider names with dots** — causes broken nested YAML

### Credential Management

#### Cloud API Keys (current as of 2026-05-25)
- **OpenRouter:** verified HTTP 200 ✅ — model slug corrected to `inclusionai/ring-2.6-1t`
- **DeepSeek:** `sk-bca71f6fd65644599bba2f98df455661` — HTTP 200 ✅ (new key pre-activated)
- **xAI (Grok):** verified HTTP 200 ✅
- **Kimi:** DEAD (401) — cold standby, awaiting new key

⚠ **Key injection rule:** NEVER use sed/perl for API key values in config.yaml. Use Python yaml library or exact-string replacement.

```python
# Correct method:
import yaml
with open('~/.hermes/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
config['providers']['deepseek']['api_key'] = 'NEW_KEY'
with open('~/.hermes/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

#### DeepSeek Activation Pattern (2026-05-25)

DeepSeek keys from the platform website may not be immediately active. If HTTP 401 on valid key:

1. Go to [platform.deepseek.com](https://platform.deepseek.com) → API Keys
2. Delete any placeholder/old keys that were never activated
3. Generate new key — it comes **pre-activated** with credit balance
4. Update `~/.hermes/.env`: `DEEPSEEK_API_KEY=sk-bca71f6fd65644599bba2f98df455661`
5. Run `key_guardian.py` to verify: should return HTTP 200 on both `/chat/completions` and `/models`

⚠ **Old DeepSeek key** was never activated on platform.deepseek.com. New key came pre-activated with credit balance.

### Telegram Polling Conflict Prevention

Telegram allows exactly one long-polling `getUpdates` session per bot token.

**Symptoms:** Gateway returns 401 after token rotation even though new token is valid.

**Resolution:**
1. Unload stale launchd plist: `launchctl unload -w ~/Library/LaunchAgents/ai.hermes.gateway.plist`
2. Kill any lingering Hermes gateway processes
3. Start gateway fresh as background process
4. If conflict persists: wait ~20 min or call `deleteWebhook?drop_pending_updates=true`
5. Then re-install: `hermes gateway install`

---

## Diagnostic Commands

```bash
# Verify all 4 cloud keys are live
for pair in "deepseek:deepseek-v4-flash" "xai:grok-4.20-reasoning" "openrouter:ring-2.6-1t"; do
  provider=$(echo $pair | cut -d: -f1)
  model=$(echo $pair | cut -d: -f2)
  echo -n "$model: "
  # Use appropriate auth header per provider
  curl -s -o /dev/null -w "HTTP %{http_code}\n" \
    -H "Authorization: Bearer KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"'"$model"'","messages":[{"role":"user","content":"hi"}]}' \
    "https://api.${provider}.com/v1/chat/completions" 2>/dev/null
done

# Check config.yaml for duplicate fallback_providers
grep -n "fallback_providers" ~/.hermes/config.yaml
# Should return exactly ONE match

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('~/.hermes/config.yaml'))" && echo "YAML OK"
```

---

## Service Management

### Launchd (Mac, Primary)
```bash
# Check status
hermes gateway status
launchctl list | grep hermes

# Restart
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway.plist
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist

# View logs
log stream --predicate 'subsystem == "ai.hermes"'
```

### Linux SSH Bridge
```bash
# Check Ollama on Linux
ssh linux 'systemctl status ollama'
ssh linux 'curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool'

# Restart Ollama on Linux
ssh linux 'sudo systemctl restart ollama'
```

---

## Common Failure Modes & Recovery

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Gateway 401 after token refresh | Telegram polling conflict | Unload plist, kill process, restart |
| config.yaml duplicate keys | Manual edit caused nested YAML | Use Python yaml safe_load/dump cycle |
| Model returning errors after key rotation | Key not fully propagated | `/reload` or `hermes gateway restart` |
| Local models not responding | Ollama service stopped | `ollama serve` or `systemctl restart ollama` |
| High latency on cloud models | Provider rate limiting | Circuit breaker activates; wait 5 min |

---

## Environment & Secrets Load Order

1. System environment (highest precedence)
2. `.envrc` in project directory
3. `~/.hermes/.env` (primary location)
4. `config.yaml` platform token fields (lowest precedence)

## Related Files
- `~/.hermes/config.yaml` — gateway configuration
- `~/.hermes/.env` — API keys and secrets
- `~/.hermes/logs/model_health.json` — circuit breaker health state
- `~/.hermes/logs/hermes_main.jsonl` — structured audit trail