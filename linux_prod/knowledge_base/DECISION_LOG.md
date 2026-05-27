# DECISION LOG — Hermes Agent
# Every significant decision, with date, context, and outcome.
# Prevents re-litigating settled questions.

## 2026-06-03

### Quality Gate Mode → Option B (Advisory 100 → Auto-Reject)
- **Context**: Ring quality gate wired in advisory mode. Board (Gerald) needs to decide enforcement.
- **Decision**: Advisory for first 100 responses, then auto-reject for scores < 5/10.
- **Rationale**: Measure baseline false-positive rate before hard enforcement. Matches Gerald's "measure 100 then decide" philosophy.
- **Status**: IMPLEMENTED in gateway_integration.py with persistent counter (qg_stats.json).

### Cron Schedule → Reduced to */3
- **Context**: heartbeat_task_manager `--once` timing out at 120s on */2 schedule.
- **Decision**: Changed to */3 (every 3 minutes) to give headroom.
- **Rationale**: Python startup + memory palace import + gateway health check occasionally pushes past 120s.
- **Status**: DONE via cronjob update.

### Deprecated Scripts Removed
- **Context**: daemonize_heartbeat.py, heartbeat_daemon_watchdog.py, heartbeat_pulse.sh were wrappers around the now-cron-based heartbeat system.
- **Decision**: Delete all three. Heartbeat task manager runs via cron `--once`.
- **Status**: DONE.

### Tauri Strategy — Backend-First
- **Context**: Should we build Tauri IDE or terminal TUI first?
- **Decision**: Terminal/CLI first. Tauri is a renderer — same backend code. Fix current stack, then wrap in Tauri.
- **Rationale**: Zero code waste. Gerald confirmed: "staying on current stack, fixes translate directly."
- **Status**: ENFORCED — all dev work targets shared backend.

### Fork Architecture — Thin Override Layer
- **Context**: How to fork hermes-agent for LumenHub?
- **Decision**: `hermes_lumenhub/` package with preloaded skills, override layer, upstream merge scripts.
- **Rationale**: Never modify upstream directly. Python path ordering for clean overrides.
- **Status**: PLANNED — scaffold when sprint begins.

## 2026-06-02 (from prior sessions)

### Gateway Integration Module → Single Interface
- **Decision**: All gateway consumers route through gateway_integration.py, not direct context_orchestrator imports.
- **Status**: DONE. base.py patched, run.py patched.

### Shadow Review → Demoted
- **Decision**: 30B is primary code grinder. Shadow review is secondary.
- **Status**: DONE. gateway_shadow_review() returns no-op by design.

### Heartbeat → Two-Layer System
- **Decision**: heartbeat_monitor.py (60s daemon) + heartbeat_task_manager.py (2min cron).
- **Status**: DONE. Monitor running 5+ hours. Task manager on cron `--once`.

### Trust System → Iterative
- **Decision**: Use before trust. Grant first, flag violations, revoke on abuse.
- **Status**: ENFORCED. Delegation scope in approval.py follows this pattern.