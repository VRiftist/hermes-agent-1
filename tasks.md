# HERMES AGENT — TASK TRACKER
# Last Updated: 2026-06-03 (auto-update this session)
# Owner: Gerald Hibbs via Hermes Agent
# Purpose: Single source of truth for all pending work items
# Recovery Grade: Every item has enough context to resume after any interruption

---

## CRITICAL (P0) — Blocks Deployment & Production Readiness

### 1. RESTORE SSH TO LINUX .114
- **Status:** ✅ RESOLVED — SSH verified, 30B active on .114
- **Last Known:** SSH key issue resolved. IP at .114 confirmed working.
- **Impact:** Unblocks ALL Linux deploy tasks
- **Options:**
  - (A) ~~Generate new SSH key, send to Gerald for `.114` install~~ — DONE
  - (B) ~~Use GitHub Actions or alternative CI/CD deploy path~~ — Not needed
  - (C) ~~Use `ssh-copy-id` from Mac if Gerald can run a command on .114~~ — Resolved
- **Files Affected:** All `~/.hermes/linux_prod/` and `~/.hermes/linux_production/` mirrors
- **Recovery Note:** SSH connectivity confirmed. Ready for file sync.

### 2. FIX GITHUB PUSH 403
- **Status:** 🔴 BLOCKED
- **Details:** Account `VRiftist` gets 403 on push to `NousResearch/hermes-agent`. Branch `feat/gateway-integration-wiring` has 7+ local commits that cannot push. PR cannot be created.
- **Options:**
  - (A) Gerald grants push access to `VRiftist` on GitHub
  - (B) Use a Personal Access Token (PAT) with `repo` scope instead of existing key
  - (C) Gerald creates PR manually from local branch
- **Recovery Note:** Repo was force-pushed previously. Confirm branch protection rules aren't blocking `VRiftist`.

### 3. GERALD DECISION: Gateway Choice (hermes-cli vs run_bridge.py)
- **Status:** ⏳ AWAITING DECISION
- **Context:** `run_bridge.py` (PID 33241) is running on Linux `.114`. `hermes-cli` is the newer gateway. They may conflict.
- **Impact:** Determines which process serves traffic, which PID to kill, which config to update.
- **Recommendation:** `hermes-cli` (newer, actively developed, wired with context orchestrator)
- **Recovery Note:** Once decided, kill the other process and verify with `ps aux | grep -E 'hermes|bridge'` and `curl localhost:PORT/health`.

### 4. GERALD DECISION: Quality Gate Enforcement Policy
- **Status:** ⏳ AWAITING DECISION — **currently ADVISORY-ONLY**
- **Context:** Quality gate is now fully wired into `base.py` message lifecycle:
  - Runs Ring (`openrouter:ring-2.6-1t`) after every assistant response
  - **Advisory mode**: warns on score < 5/10, does NOT block delivery
  - Score + content returned in `gateway_quality_gate()` response for logging
- **Options:**
  - (A) Keep warning-only indefinitely (gather metrics first)
  - (B) Warning-only for first 100 responses, then auto-reject below threshold
  - (C) Warning-only for first 100 responses, then auto-rewrite below threshold
  - (D) Always warn, never block (conservative forever)
- **Recommendation:** Option B — gather 100 response scores, then enforce. Gives real data before committing.
- **Recovery Note:** The quality gate model (`openrouter:ring-2.6-1t`) must be live and healthy before enforcement. Currently active via OpenRouter (verified working in logs).

### 5. GERALD DECISION: SSH Key for Linux .114
- **Status:** ⏳ AWAITING DECISION
- **Context:** Gerald says "SSH is working typo above" — does this mean SSH IS working now (password-based?), or that the previous status note about the IP was a typo?
- **Clarification Needed:** Gerald to confirm:
  - (A) SSH works now at .114 (password auth?)
  - (B) SSH key was fixed/restored
  - (C) Alternative deploy path (GitHub Actions, rsync, etc.)
- **Recovery Note:** Cannot deploy until this is resolved. Affects ALL Linux production tasks.

---

## HIGH (P1) — Must Complete Before Board Sign-Off

### 6. DEPLOY MATCHED PAIR TO LINUX (.114)
- **Status:** ✅ SSH VERIFIED — ready for file sync once Gerald triggers
- **Files to Sync:**
  | File | Mac Source | Linux Dest | Size | Notes |
  |------|-----------|-----------|------|-------|
  | `auto_trim.py` v2 | `~/.hermes/hermes-agent/scripts/auto_trim.py` | `~/.hermes/auto_trim.py` | 32KB | REPLACES outdated v1 (9KB) |
  | `gateway_integration.py` v2 | `~/.hermes/scripts/gateway_integration.py` | `~/.hermes/gateway_integration.py` | 14KB | REPLACES outdated v1 (5.3KB) |
  | `consult_merge.py` | `~/.hermes/scripts/consult_merge.py` | `~/.hermes/consult_merge.py` | 9.4KB | MISSING from Linux entirely |
  | `context_orchestrator.py` | `~/.hermes/scripts/context_orchestrator.py` | `~/.hermes/context_orchestrator.py` | 25KB | MISSING from Linux entirely |
  | `memory_palace.py` | `~/.hermes/scripts/memory_palace.py` | `~/.hermes/memory_palace.py` | 16KB | MISSING from Linux entirely |
  | `night_council.py` | `~/.hermes/scripts/night_council.py` | `~/.hermes/night_council.py` | 12KB | MISSING from Linux entirely |
  | `test_pause_protection.py` | `~/.hermes/scripts/test_pause_protection.py` | `~/.hermes/test_pause_protection.py` | 23KB | MISSING from both hermes-agent/ AND Linux |
- **Directory Creation:**
  - `~/.hermes/bridge/signals/responses/` (empty dir)
  - `~/.hermes/logs/archive/` (verify exists)
- **Critical Constraint:** `auto_trim.py` v2 and `gateway_integration.py` v2 MUST be deployed together (16-field response contract dependency). Never one without the other.
- **Verification:** After sync, run `python3 -c "import auto_trim; import gateway_integration; print('Both imported OK')"` on Linux.

### 7. WIRE CONTEXT ORCHESTRATOR INTO GATEWAY RUNTIME LOOP
- **Status:** ✅ COMPLETE (base.py) — ⏳ DEFERRED: run.py trim timing optimization
- **What was Done (this session, 2026-06-03):**
  - `gateway_integration.py` fully wired into `base.py` message lifecycle
  - All 7 orchestrator functions imported from `gateway_integration` (replacing direct `context_orchestrator` import)
  - `gateway_message_start()` with `task_category`, `orchestrator_session_key`, `platform` params
  - `gateway_register_turn("user")` added before `_message_handler` call
  - `gateway_trim_check()` wired before `_message_handler` with logging for trimmed blocks/tokens
  - `gateway_quality_gate()` wired after response generation, **advisory mode**
  - `gateway_register_turn("assistant")` fixed with `orchestrator_session_key`
  - `gateway_message_end()` in finally block fixed with `orchestrator_session_key`
  - All 15 self-test cases pass ✅
  - Syntax verified: `py_compile` passes clean ✅
  - Committed in hermes-agent: `ef63825a1`
- **Remaining (run.py):**
  - `gateway_trim_check()` at run.py line 8178 fires on every inbound message (inside `_handle_message_with_agent`)
  - Now REDUNDANT with the new base.py trim check before `_message_handler`
  - Run.py trim uses more accurate token counting: `sum(len(content) for msg in history) // 4`
  - **Decision:** Leave run.py trim as safety net (catches any direct callers); double-check is cheap and harmless
  - If optimization desired: move run.py trim to after transcript loading, or wrap with `if not already_trimmed` flag
- **Recovery Note:** The orchestrator is now fully operational inside the gateway's message processing loop. Linux deployment (task #6) is the remaining dependency.

### 8. FIX DEFERRABLE TRIM TIMING (run.py optimization)
- **Status:** 🟡 DEFERRED — Low priority optimization
- **Problem:** `gateway_trim_check()` at `run.py:8178` fires on every inbound user message AND is now redundant with base.py's trim check
- **Correct Behavior:** Ideally a single trim right before response generation
- **Planned Fix:** Either (a) remove the run.py call since base.py handles it, or (b) guard it with a skip-if-already-trimmed flag
- **Impact:** Minor — reduces one redundant compression cycle per message
- **Testing Required:** Verify trim still fires when context is large. Verify no double-trim overhead.

### 9. RUN FULL TEST SUITES
- **Status:** 🟡 PARTIALLY DONE
- **Mac Tests:** 44/44 pytest ✅, 15/15 gateway integration self-test ✅, 28/28 pause_protection ✅, 7/7 lifecycle smoke ✅, 5/5 syntax ✅
- **Linux Tests:** NOT YET RUN (no SSH access)
- **Required Before PR:**
  - Mac: Re-run after any changes (currently green)
  - Linux: Full `test_pipeline.py --validate` once SSH restored
  - Cross-platform: Verify identical behavior on both
- **Recovery Note:** All test files are at:
  - `~/.hermes/hermes-agent/scripts/test_auto_trim.py` (44 tests)
  - `~/.hermes/scripts/test_pause_protection.py` (28 tests)
  - Gateway integration self-test (embedded in `gateway_integration.py` `__main__`)

### 10. CREATE GITHUB PR
- **Status:** 🔴 BLOCKED BY #2 (GitHub Push 403)
- **Branch:** `feat/gateway-integration-wiring` (7+ local commits)
- **Required:** Push to `NousResearch/hermes-agent`, then create PR
- **PR Description Must Include:**
  - Full audit summary
  - Board review link
  - Test results (44/44, 15/15, 28/28)
  - Before/after comparison of files deployed to Linux
  - Risk register updates
- **Workaround:** If push fails, Gerald can pull the branch locally or use `git bundle`

---

## MEDIUM (P2) — Pre-Publish Polish

### 11. RESOLVE Kimi API 401 / Dual-Key Issue
- **Status:** 🔴 BLOCKED — Needs Gerald action
- **Problem:** Only `KIMI_API_KEY` loaded (1 key); `KIMI_API_KEY_2` not in `.env`
- **Client supports:** Dual-key rotation on 401/429 but only 1 key available
- **Behavior:** Intermittent 401 "Invalid Authentication" from api.moonshot.cn
- **Fix Options:**
  - (A) Gerald obtains a second Kimi/Moonshot API key → add `KIMI_API_KEY_2=sk-xxxx` to `.env`
  - (B) Demote Kimi to cold standby (disable in config, use only as manual fallback)
  - (C) Wait for openrouter:kimi endpoint to stabilize (not yet available)
- **Recommendation:** Option B for now (cold standby), re-activate when second key obtained
- **Key Management Strategy:** See `documentation/key_management_strategy.md`