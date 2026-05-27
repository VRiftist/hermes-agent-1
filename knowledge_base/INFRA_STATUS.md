# Knowledge Base — INFRA_STATUS
# Always-true infrastructure facts. Loaded into preload context for every session.
# Last verified: 2026-06-03

## Gateway
- PID: 64251
- Status: Running, healthy
- Platforms: Telegram ✅, Discord ⚠️ (retrying), FeiShu ✅
- Heartbeat monitor: PID 56226, 5+ hours uptime
- Heartbeat task manager: cron `--once` every 3 min (was every 2, fixed timeout)
- Quality gate: Ring (inclusionai/ring-2.6-1t) — Option B (100-response advisory → auto-reject)

## SSH & Network
- Linux .114: SSH tunnel tested, reachable via `ssh-tunnel-linux-ollama.sh`
- Ollama on .114: Port 11434, models loaded
- Mac sshd: NOT running — needs `sudo launchctl load` with Gerald's password
- Tunnel forwards local 11435 → remote 11434

## Ollama & Models
- Local (Mac): qwen3:14b, qwen3:8b, qwen2.5-coder:32b — all serving on localhost:11434
- Linux .114: qwen3:8b + 8 models on localhost:11434
- Cloud: DeepSeek v4 flash, Grok 4.20, Ring 2.6-1t, Claude (not yet active)
- Kimi: ⚠️ Temperamental — primary key intermittently 401. No secondary key loaded.

## Filesystem
- Main repo: ~/.hermes (macOS staging)
- Agent repo: ~/.hermes/hermes-agent (checked out, 7 commits ahead of origin)
- Production: /home/gerald/ai-team-shared/hermes-pipeline/ on .114
- Key files: config.yaml (restructured), gateway_integration.py (v2), base.py (4 patches)

## Credential Status
- .env file: EXISTS but EMPTY — keys loaded via inject_keys.py or launchd env
- Telegram: Works in gateway (BotFather token injected at launch)
- OpenRouter: Active, credits need verification
- Kimi: Primary key in .env returns 401 intermittently

## Common Misconceptions (STOP — check here first)
- SSH is NOT broken. Verified working 2026-06-03 by Gerald.
- Config.yaml parses clean. The cli-config.yaml error was a stale artifact from May 26.
- run.py double-trim is SAFE — trim_context() has idempotency guard at line 427.
- heartbeast_task_manager `--once` timeout was caused by */2 schedule hitting 120s limit. Fixed to */3.
- Discord reconnection failure is an upstream library issue, not our config.