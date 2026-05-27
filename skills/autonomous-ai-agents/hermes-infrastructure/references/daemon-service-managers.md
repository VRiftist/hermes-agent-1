# Daemon Deployment — launchd (macOS) & systemd (Linux)

Native service managers replaced cron for heartbeat daemon lifecycle management.

## Why not cron for daemons

- No process lifecycle management — if script dies, stays dead until next tick
- `no_agent` mode ignores `script_args` (root cause of heartbeat timeout loop)
- 120s cron timeout kills long-running scripts
- Background terminal sessions introduce phantom state via session restoration

## macOS: launchd

**File:** `scripts/com.lumenhub.heartbeat.plist`

Key structure:
- `ProgramArguments` — venv Python path + script path + `--mode daemon`
- `EnvironmentVariables` — `SILENT_MODE=1`, `PYTHONUNBUFFERED=1`
- `KeepAlive: true` — auto-restarts on crash
- `StartInterval: 300` — restarts every 5 min if not running
- `StandardOutPath` / `StandardErrorPath` — log to `logs/`

**Install:**
```bash
cp com.lumenhub.heartbeat.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.lumenhub.heartbeat.plist
launchctl start com.lumenhub.heartbeat
launchctl list | grep heartbeat
```

## Linux: systemd

**File:** `scripts/hermes-heartbeat.service`

Key directives:
- `Restart=on-failure` with `RestartSec=10`
- `MemoryMax=512M` / `CPUQuota=50%` / `OOMPolicy=kill`
- `SILENT_MODE=1` / `PYTHONUNBUFFERED=1`
- Logs to `logs/` via `StandardOutput=append:`

**Install:**
```bash
sudo cp hermes-heartbeat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-heartbeat
systemctl status hermes-heartbeat
```

## SILENT_MODE protocol

When `SILENT_MODE=1`:
- Routine heartbeats → **suppressed**
- Gateway crash/restart → **sent** (critical, `force=True`)
- Max restart limit → **sent**
- Stale heartbeat > 4 min → **sent** (dead man's switch)

## Migration from cron

1. Create the service file
2. Disable old cron entry (`"enabled": false` in `cron/jobs.json`)
3. Load/start the native service
4. Verify heartbeat file timestamp updates
5. Remove old cron entry once stable