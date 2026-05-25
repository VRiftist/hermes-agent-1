# ═══════════════════════════════════════════════════════════════
# HERMES KEY MANAGEMENT STRATEGY
# Decision: 2026-05-25
# Status: PENDING OPERATOR APPROVAL
# ═══════════════════════════════════════════════════════════════

## Problem Statement
API keys keep getting lost, rotated, or expiring silently. This is
unsustainable — every dead key = degraded capability + debugging time.

## Decision: Centralized Vault + Automated Health Monitoring

### 1. Drop Kimi from Active Chain ✅
**Rationale:** 4 cloud providers + 2 local = 6 endpoints. That's redundant.
Adding a 5th provider with an unstable key adds fragility, not resilience.
Kimi goes to "cold standby" — config preserved, not active.

**Impact:** Zero. DeepSeek (reasoning), Grok (creativity), Ring (quality gate),
plus 2 local Qwen3 models = full capability coverage.

### 2. Centralized Key Vault (.env)
**What:** ALL keys move to `~/.hermes/.env` — single source of truth.
**Permissions:** `chmod 600` — only owner can read/write.
**Format:**
```
# ═══════════════════════════════════════
# HERMES API KEY VAULT
# Last updated: 2026-05-25
# DO NOT commit this file to any repo
# ═══════════════════════════════════════

# OpenRouter (2 keys for redundancy)
OPENROUTER_KEY_1=sk-or-...b1dc
OPENROUTER_KEY_2=sk-or-...backup

# DeepSeek
DEEPSEEK_API_KEY=sk-8ea...c887

# xAI / Grok
XAI_API_KEY=xai-ZC...d0r7

# Kimi (COLD STANDBY — do not use until activated)
# KIMI_API_KEY=

# Digital Ocean (when provisioned)
# DIGITALOCEAN_API_KEY=

# Telegram bot
TELEGRAM_BOT_TOKEN=

# Firecrawl (if activated)
# FIRECRAWL_API_KEY=

# Brave Search (if activated)
# BRAVE_API_KEY=

# Claude API (if activated)
# ANTHROPIC_API_KEY=
```

**Rules:**
- config.yaml NEVER contains actual keys — only references to env vars
- `.env` is in `.gitignore` globally
- `.env.bak` template (with placeholder format) IS committed for onboarding
- Every key has a comment with provider URL + where to renew

### 3. Automated Key Health Check (Daily)
**Tool:** `scripts/key_guardian.py` — runs daily via cron at 06:00 UTC.
Does NOT make API calls. Validates keys by:
- Checking env vars exist and are non-empty
- Parsing key format (prefix check: `sk-or-*`, `sk-*`, `xai-*`)
- Cross-referencing with circuit breaker health state
- Sending Telegram alert if any key is missing or marked unhealthy

### 4. Key Recovery Playbook (Per Provider)

| Provider | Where to Renew | Max Time to Restore | Notes |
|----------|----------------|---------------------|-------|
| OpenRouter | openrouter.ai/settings/keys | 2 min | Keep 2 keys always |
| DeepSeek | platform.deepseek.com/api | 5 min | Model names change — check docs |
| xAI / Grok | x.ai/dashboard | 3 min | API access tier matters |
| Kimi | platform.moonshot.cn | 10 min | Unreliable — deprioritized |
| Digital Ocean | cloud.digitalocean.com/security | 5 min | Droplet + API key |

### 5. Rotation Schedule
- **Every 90 days:** Review all keys, rotate if possible
- **After any team change:** Immediately rotate affected keys
- **After any suspicion of exposure:** Rotate immediately
- **Automate reminder:** Cron job logs rotation check to memory palace

### 6. Emergency Fallback
If ALL cloud keys die simultaneously:
1. Agent falls back to local Ollama (2 endpoints, zero external dependency)
2. Telegram alert sent to operator
3. Agent enters "reduced capability" mode — no cloud reasoning/creativity
4. Operator restores keys → agent auto-detects recovery via health check

## Files to Create
1. `~/.hermes/.env` — centralized vault (with current verified keys)
2. `~/.hermes/.env.template` — safe-to-commit onboarding template
3. `~/.hermes/scripts/key_guardian.py` — daily key validation daemon
4. `~/.hermes/documentation/key_management.md` — this doc, for onboarders

## Task List (P0/P1 from this decision)

| # | Task | Priority | Status |
|---|------|----------|--------|
| 1 | Create .env vault with current keys | P0 | READY |
| 2 | Update config.yaml to read from env vars | P0 | READY |
| 3 | Create .env.template for onboarding | P0 | READY |
| 4 | Set .env permissions (chmod 600) | P0 | READY |
| 5 | Create key_guardian.py | P1 | READY |
| 6 | Schedule key_guardian cron (daily 06:00 UTC) | P1 | READY |
| 7 | Add Digital Ocean provisioning to task list | P2 | READY |
| 8 | Kimi: archive config, mark cold standby | P2 | READY |

## Decision by: Operator (Gerald Hibbs)
**Awaiting approval via Telegram before executing.**

---
*This strategy ensures: no single point of key failure, daily automated
validation, documented recovery for every provider, and graceful
degradation to local-only operation if all cloud keys are lost.*