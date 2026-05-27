# Agent Context — Preload for New Sessions

## System State (as of 2026-06-03)

### Running Processes
- **Gateway**: PID 64251 — `hermes_agent.cli --gateway` — running since ~06:53AM, stable 3+ hrs
- **Heartbeat Monitor**: PID 56226 — `heartbeat_monitor.py` — running since ~01:30AM, stable 5+ hrs
- **Heartbeat Task Manager**: cron-based `*/3 * * * *` — runs via `--once` mode, picks up latest code each cycle
- **Session Watchdog**: cron-based `*/5 * * * *` — 114+ consecutive runs

### Stale Process Cleanup
- OLD heartbeat task manager daemon was running as a long-lived process (not `--once` mode).
  This was a leftover from a prior manual start. It was killed on 2026-06-03.
  The cron `--once` schedule is the correct execution path — no manual daemon needed.

### Key Fixes Applied Today (2026-06-03)
1. `heartbeat_task_manager.py` — timeout cap: MAX_TASK_RUNTIME=90s in `--once` mode, TASK_BATCH_LIMIT=1
2. `kimi_client.py` — added `is_available()` function for external readiness checks
3. `model_routing.py` — Kimi skipped in routing when no valid API key present
4. `linux_prod/` — patched files synced for deployment readiness

### Credential Status
- Kimi API: PRIMARY key in `.env` but returns intermittent 401; NO secondary key loaded
- GitHub: Push blocked (403 on both main repo and submodule)
- Telegram: Connected (chat_id: 1767184775)
- Ollama (Mac local): Working
- Ollama (Linux .114): Ready to deploy once push/SSH unblocked

### Architecture
- OS: macOS 26.5 (Mac Mini M2 32GB)
- Linux box: 192.168.1.230 (RTX 3060, 45GB RAM) — offline/retired, DO pending
- SSH topology: Mac→Linux outbound-only (Linux never reaches back)
- Tunnel: `ssh-tunnel-linux-ollama.sh` maps Mac:11435 → Linux:11434