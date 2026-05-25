# Key Guardian Deploy & Cron Reference

## What key_guardian.py Does

Parses `~/.hermes/.env`, sends a minimal auth ping to each provider, reports status, writes `logs/model_health.json`, and optionally sends a Telegram alert on newly dead keys.

## Manual Run

```bash
python3 ~/.hermes/scripts/key_guardian.py
```

## Cron Setup

Installed via crontab at `0 3 * * *` (3:00 AM UTC daily):

```
0 3 * * * cd /Users/lumenhubai/.hermes && /usr/bin/python3 scripts/key_guardian.py >> ~/.hermes/logs/night_council.log 2>&1
```

Verify: `crontab -l`

## Telegram Alerts (optional)

Add to `.env`:

```
TELEGRAM_BOT_TOKEN=123456:ABC-...
TELEGRAM_CHAT_ID=-1001234567890
```

Without these, guardian still checks — just won't alert.

## Health Output

Written to `~/.hermes/logs/model_health.json`:

```json
{
  "last_check": "2026-05-25T08:02:00Z",
  "providers": {
    "DEEPSEEK_API_KEY": { "status": "alive", "detail": 200 },
    "XAI_API_KEY": { "status": "alive", "detail": 200 },
    "OPENROUTER_KEY_1": { "status": "missing", "detail": "not in .env" }
  },
  "dead_keys": ["OpenRouter (key 1) (OPENROUTER_KEY_1) → missing: not in .env"]
}
```

## Emergency Fallback Behavior

When all cloud keys are dead, the fallback chain (configured in `config.yaml`) routes everything to local Ollama endpoints. The circuit breaker in `circuit_breaker.py` will:
1. Mark cloud providers as unavailable
2. Route to `mac-ollama` or `linux-ollama`
3. Send a Telegram alert if configured