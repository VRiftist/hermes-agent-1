# PROVIDER STATUS — Live Health Dashboard
# Updated: 2026-06-03

## Model Providers

| Provider | Model | Status | Notes |
|----------|-------|--------|-------|
| Ollama (Mac) | qwen3:14b | ✅ Active | Primary orchestrator brain |
| Ollama (Mac) | qwen3:8b | ✅ Active | Context trimmer (always on) |
| Ollama (Mac) | qwen2.5-coder:32b | ✅ Available | In config, not in active chain |
| Ollama (Linux .114) | qwen3:8b | ✅ Active (via tunnel) | Port 11434 |
| DeepSeek | deepseek-v4-flash | ✅ Configured | API key active |
| DeepSeek | deepseek-v4-pro | ✅ Configured | API key active |
| Grok (xAI) | grok-4.20-reasoning | ✅ Configured | API key active |
| Grok (xAI) | grok-4.3 | ✅ Configured | API key active |
| OpenRouter | ring-2.6-1t | ✅ Active | Quality gate model |
| OpenRouter | inclusionai/ring-2.6-1t | ✅ Active | Same, full name |
| Kimi | Moonshot | ⚠️ TEMPERAMENTAL | Primary key intermittently 401. No secondary key. |
| Anthropic | claude-sonnet-4 | ❌ Not active | API key not configured yet |

## Platform Connections

| Platform | Status | Details |
|----------|--------|---------|
| Telegram | ✅ Connected | Bot active, chat_id 1767184775 |
| Discord | ⚠️ Retrying | Reconnect failed since May 26 — upstream lib issue |
| FeiShu | ✅ Connected | Active |
| Termux | 🔧 Pending | 10 TODOs, deferred to Phase 3 |

## Services

| Service | Status | PID/Port |
|---------|--------|----------|
|| Hermes Gateway | ✅ Running | PID 64251, stable 3+ hrs |
|| Heartbeat Monitor | ✅ Running | PID 56226, 5+ hrs |
|| Heartbeat Task Manager | ✅ Cron | Every 3 min, `--once` mode, patched (90s cap, batch=1). Stale long-runner daemon killed 2026-06-03. |
|| Session Watchdog | ✅ Cron | Every 5 min, 114+ runs completed |
|| Ollama (Mac) | ✅ Serving | localhost:11434 |
|| Ollama (Linux) | ✅ Serving | .114:11434 (via tunnel) |

## Known Issues

1. **Kimi 401** — Intermittent auth failure. Need second key or demote to cold standby.
2. **Discord reconnect** — Upstream python-telegram-bot or gateway issue. Not config-related.
3. **OpenRouter credits** — Payment error flagged. Verify balance.
4. **mac sshd** — Not running. Needs `sudo launchctl load` with password.