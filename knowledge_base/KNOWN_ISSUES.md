# Active Issues & Workarounds
> Last updated: 2026-06-03

## 🔴 Active Blockers

### 1. GitHub Push 403 (VRiftist → NousResearch/hermes-agent)
- **Status:** 7+ commits stuck on `feat/gateway-integration-wiring`
- **Workaround:** Create fork, push there, submit PR from fork
- **Root cause:** PAT scope or repo permissions — not a code issue
- **Decided:** Option C — push to fork, create PR

### 2. Kimi API Intermittent 401
- **Status:** Primary key returns 401 under rate limit pressure
- **Workaround:** Dual-rotation code exists but needs second key
- **Decision:** Get second key from Moonshot (Option A). If unavailable, demote Kimi to cold standby and route through Deepseek → Claude fallback
- **Ollama bypass:** `kimi-k2.5:cloud` via OLLAMA_API_KEY eliminates the Moonshot API entirely

### 3. Quality Gate Enforcement Mode
- **Status:** Ring scores but doesn't block anything
- **Decision pending from Gerald:** Option B — advisory for 100 responses, then auto-reject

## 🟡 Known Issues (Non-Blocking)

### 4. OLLAMA_API_KEY — Not Live-Verified
- Key is in .env with valid format
- DNS to cloud.ollama.com blocked from sandbox
- **Fix:** Run verification from terminal: `curl -X POST https://cloud.ollama.com/api/tags -H "Authorization: Bearer $(grep OLLAMA_API_KEY ~/.hermes/.env | cut -d= -f2)"`

### 5. Sibling Subagent Drift
- 4 files modified by sibling: SESSION_PIN.md, TWO_TRACK_ARCHITECTURE.md, IMPLEMENTATION_BLUEPRINT.md, IDE_STRATEGY_2026-06-03.md
- Full re-read + reconciliation needed
- Not blocking but creating doc confusion

### 6. DeepSeek Timeout Pattern
- Intermittent timeouts, not auth failures
- Fallback chain should catch this — verify chain is: Deepseek → Claude
- If persistent: add circuit breaker (3 timeouts → skip for 5 min)

## ✅ Resolved (Last 7 Days)
- Orphan process cleanup (killed 24+ PIDs, recovered ~1.5GB)
- Heartbeat monitor daemon → cron mode (no more crash loops)
- Night council KeyError fix
- Config.yaml restructure (stale parse errors eliminated)
- Context orchestrator shims restored (audit L2 passing)
- Branding correction pass (Ring → LumenHub Approved™ across all docs)

## ⬜ Recurring Pain Points (Track Here)
| Issue | Frequency | Last Occurrence | Root Cause |
|-------|-----------|-----------------|------------|
| "Is SSH broken?" | Weekly | 2026-06-03 | Nobody checks INFRA_STATUS.md |
| "Is Kimi key dead?" | Bi-weekly | 2026-06-03 | Rate limit 401 ≠ bad key |
| "Deepseek timeout again" | Weekly | 2026-06-03 | No circuit breaker yet |
| "OLLAMA key not working" | Bi-weekly | 2026-06-03 | Sandbox ≠ terminal confusion |