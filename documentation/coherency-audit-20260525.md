# HERMES AGENT — FULL COHERENCY AUDIT
# Date: 2026-05-25
# Scope: Every core file, every assumption, every design decision
# Auditor: Hermes self-audit (multi-model review cycle)
# Status: COMPLETE — 7 critical issues, 12 warnings, 5 recommendations

---

## EXECUTIVE SUMMARY

The system is **structurally sound but operationally disconnected**. The individual components (Memory Palace, Context Orchestrator, Model Routing, Circuit Breaker, Key Guardian) are each well-designed in isolation. The problems are:
1. **They don't talk to each other yet** (orchestrator not in gateway loop)
2. **Redundant monitoring systems** (two separate health tracking paths)
3. **Security gaps between policy and practice** (PII, alerting, egress)
4. **Documentation lies** (key_guardian "doesn't make API calls" — it does)

Verdict: **Not production-ready, but foundationally correct. The architecture is sound; the wiring is not.**

---

## 1. MEMORY PALACE (`memory_palace.py`)

### ✅ What's Right
- SQLite with WAL mode: correct choice for persistence + concurrent reads
- Episodic/semantic/working layer separation: architecturally clean
- Deduplication and confidence decay: good curation mechanisms
- 56KB footprint for 15 episodes + 9 facts: efficient at current scale

### ❌ Challenges & Issues

**ISSUE 1: Working memory survives the session it's supposed to be scoped to.**
- `set_working()` stores in the same SQLite DB as persistent memory
- "Cleared on session end" is only true if the session ends cleanly (via `end_session()`)
- If the gateway crashes, is killed, or the connection drops — working memory persists as ghost state
- **Impact:** Next session may inherit stale working context from a dead session
- **Fix:** Add a TTL or session_id to working memory entries. On `start_session()`, purge any working entries older than N minutes or from a different session ID.

**ISSUE 2: `_extract_facts()` is dangerously naive.**
- Algorithm: split by newlines, take first 80 chars as "concept", next 200 as "description"
- This produces garbage from structured content (code, JSON, tables)
- Example: a file listing like `drwxr-xr-x  5 user  staff  160 May 25 10:00 src/` becomes concept="drwxr-xr-x  5 user  staff  160 May 25 10:00 src/" — meaningless
- **Impact:** Semantic memory degrades over time with low-quality facts, making recall unreliable
- **Fix:** Either (a) use an LLM call to extract structured facts before storing, or (b) remove auto-extraction entirely and only store manually tagged facts. Option (b) is more reliable at this scale.

**ISSUE 3: No encryption at rest.**
- SQLite DB is plaintext on disk
- Contains: all conversation history, decisions, API usage patterns, potentially sensitive code or credentials discussed
- `.env` has `chmod 600` (good), but `memory-palace.db` has no permissions guard
- **Impact:** Anyone with filesystem access can read the full agent memory
- **Fix:** Add `chmod 600` to the DB file on creation. Consider SQLCipher for encryption at rest.

**ISSUE 4: No pruning during long-running sessions.**
- `prune_expired()` is only called during Night Council (3am cron)
- During a long session that generates many episodes, the DB grows unbounded
- **Impact:** Memory bloat, slower recall queries, potential context pollution
- **Fix:** Call `prune_expired()` at the start of every `start_session()` and after every N episodes during a session.

### ⚠️ Warning: `user_char_limit: 1375` still in config.yaml
The config still has `memory_char_limit: 2200` and `user_char_limit: 1375` — these are the OLD flat-memory limits. The Memory Palace was built to replace this, but the config values still exist and may be used by the gateway's default memory handler. **Verify these are not being used as a ceiling on top of the Palace.** If they are, the Palace is being strangled by its predecessor's limits.

---

## 2. CONTEXT ORCHESTRATOR (`context_orchestrator.py`)

### ✅ What's Right
- 6-tier priority system is well-designed (T0=identity never trimmed → T6=conversation deleted first)
- Model-adaptive budgets (8K for 8B local, 12K for 14B, 24K for DeepSeek, 32K for Ring)
- Session lifecycle: prep → trim → end, with persistence
- Self-tests pass (3/3 phases)

### ❌ Challenges & Issues

**CRITICAL: Not wired into gateway runtime.**
- This is already documented as the #1 gap. Until this is fixed, the entire context management system is theoretical.
- The integration point is in `config.yaml` under `context.engine: compressor` — but the orchestrator is a completely separate Python module with no interface to the gateway.

**ISSUE 5: Token counting is inaccurate.**
- Uses `len(text) * 0.25` (chars × 0.25) as token estimate
- The framework doc itself acknowledges this is "too rough for trim decisions"
- Actual tokens vary by 20-40% depending on content type (code vs natural language)
- **Impact:** Trim thresholds may fire too early or too late. On an M2 Mac with qwen3:14b (16K context), being off by 20% means trimming at 11.5K actual tokens when you think you're at 12K, or not trimming until 14.4K when the window is already full.
- **Fix:** Use `tiktoken` for OpenAI-compatible models (DeepSeek, Grok, Ring). For Ollama/Qwen, use the model's own tokenizer. Add a `tokenize()` function that selects the right tokenizer per model.

**ISSUE 6: No interrupt recovery.**
- If the session is killed (Ctrl+C, crash, timeout), there's no state checkpoint
- The `session_end()` phase persists state, but only if the session ends cleanly
- **Impact:** Any in-progress reasoning, half-formed analysis, or pending decisions are lost
- **Fix:** Add `session_interrupt()` that catches SIGINT/SIGTERM and does a fast state dump (current task state + dirty writes). On next `session_start()`, detect and offer to restore.

**ISSUE 7: Compression is described but not implemented.**
- The framework doc §3.3 describes a sophisticated hybrid compression system:
  - T5: compress to 10% tokens, tag `[COMPRESSED]`, persist full text to Palace
  - T3: check Palace for existing facts before trimming
  - Rehydration protocol for compressed blocks
- The actual `context_orchestrator.py` code implements simple trimming, not compression
- **Impact:** The 10-token stubs mentioned in the framework ("Trimmed block (tier 5, 2000 tokens)") lose almost all information. If the model later needs that content, it's gone.
- **Fix:** Implement at minimum a T5 compression function that extracts key findings, file paths, and decisions into a ~200-token summary. The full text goes to the Palace for rehydration.

---

## 3. MODEL ROUTING (`model_routing.py`)

### ✅ What's Right
- Task classification by keyword is a reasonable starting point
- Circuit breaker with cooldown prevents hammering dead endpoints
- Preference for local models before cloud (cost + latency wins)
- Separate `REASONING_MODELS` set for "think harder" tasks

### ❌ Challenges & Issues

**ISSUE 8: Keyword-only classification is fragile.**
- "Write a bug report" → `code_generation` (matches "write") — should probably be `review`
- "I'm thinking through a design" → no keyword match → `general` — should be `design`
- Negation not handled: "Don't write code, just explain it" → `code_generation` (matches "write" and "code")
- **Impact:** Wrong model selection for edge cases. A reasoning task routed to qwen3:8b instead of DeepSeek means worse quality.
- **Fix:** Add confidence scoring. Return the top-2 categories with scores. If the top score is below a threshold (e.g., 3 keyword matches), fall through to `general` and let the model self-route. Better: add negative keywords ("not code", "just explain", "in theory").

**ISSUE 9: Budget check ignores output cost.**
- Code only checks `cost_per_1k_input` against remaining budget
- Grok costs $10/1K output tokens vs $1.25/1K input — output is 8× more expensive
- **Impact:** A budget of $1.0 for input could be blown by $8.0+ in output on a Grok call
- **Fix:** Estimate output length (e.g., 4× input length, or model-specific average) and check total estimated cost (input + output) against budget.

**ISSUE 10: `qwen3-coder:30b-a3b` is missing from routing.**
- The framework doc lists it as "Staged — On disk, not yet in routing"
- `model_routing.py` MODELS dict doesn't include it
- `config.yaml` mac-ollama models list doesn't include it
- **Impact:** A model that was explicitly provisioned for deep reasoning isn't being used
- **Fix:** Add to MODELS dict and CATEGORY_BEST for reasoning and design tasks.

**ISSUE 11: Context window check uses 70% threshold uniformly.**
- `if history_length > cfg["context_length"] * 0.7: continue`
- This leaves 30% for output. For a 16K model, 30% = 4800 tokens of output headroom
- For code generation, 4800 tokens is plenty. For a simple yes/no question, it's wasteful.
- **Fix:** Make the threshold proportional to expected output length. For "quick" tasks (get_task_size), require only 20% headroom. For "large" tasks, require 50%.

**ISSUE 12: No model fallback within a single reasoning chain.**
- If DeepSeek v4-flash fails mid-reasoning chain, the entire chain fails
- The circuit breaker marks a model dead after 3 failures, but doesn't trigger mid-chain re-routing
- **Impact:** A single API timeout kills a multi-hop consultation
- **Fix:** In the consult/merge flow, wrap each model call with a try/except that triggers circuit breaker update and retries with the next candidate model.

---

## 4. CIRCUIT BREAKER (`circuit_breaker.py`)

### ✅ What's Right
- Dual monitoring (health checks + consecutive failure counting) is robust
- 5-minute cooldown before retry is sensible
- `get_failover_chain()` provides clean active model list

### ❌ Challenges & Issues

**ISSUE 13: Two separate health tracking systems exist.**
- `circuit_breaker.py` → file-based `~/.hermes/logs/model_health.json`
- `model_routing.py` → in-memory `HEALTH` dict (lost on restart)
- These are independent. `circuit_breaker.py` reads/writes the file. `model_routing.py` uses its own dict initialized from nothing.
- **Impact:** Health state from the circuit breaker isn't used by the routing engine. A model marked dead by the circuit breaker is still considered healthy by model_routing until it fails 3 times in the current process.
- **Fix:** Single source of truth. Have `model_routing.py` use the circuit breaker's `check_health()`/`report_health()` functions, or load the health file at startup.

**ISSUE 14: No latency-based degradation.**
- A model responding in 5 seconds isn't "unhealthy" per the current checks
- But for a quick coding question, a 5-second wait is unacceptable
- **Impact:** Slow-degraded models are treated as healthy and get routed traffic
- **Fix:** Track latency in health state. Add a "degraded" state (not just healthy/unhealthy) when latency exceeds a threshold (e.g., 3× the model's `latency_estimate_ms`).

---

## 5. KEY MANAGEMENT (`key_guardian.py`, `.env`)

### ✅ What's Right
- Centralized .env vault is correct architecture
- chmod 600 is correct
- Telegram alerting on key failure is good
- Pseudo-code in security_model.md matches actual implementation

### ❌ Challenges & Issues

**ISSUE 15: The documentation lies about key_guardian's behavior.**
- The key_management_strategy.md says: "Does NOT make API calls. Validates keys by: Checking env vars exist and are non-empty, Parsing key format..."
- The actual code in `test_key()` sends a real API request to each provider endpoint
- **Impact:** The cron job generates API usage (and cost) on every run. For DeepSeek, that's $0.14/1K input per check. Not expensive, but the documentation is misleading, which matters for capacity planning.
- **Fix:** Update the documentation. Consider making API calls optional (a `--live-check` flag) with key format + existence check as the default daily run.

**ISSUE 16: Telegram alerting is entirely non-functional.**
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are not set in `.env`
- `send_telegram_alert()` silently returns without sending if these are empty
- **Impact:** The entire alerting chain is dead. Key failures, health alerts, Night Council recommendations — all silently dropped. The operator is flying blind.
- **Fix:** P0 — get valid Telegram bot token and chat ID, add to `.env`. Add a startup assertion that alerts can actually be sent.

**ISSUE 17: `test_key()` only tests one model per provider.**
- DeepSeek check uses `deepseek-chat` model, but the routing config uses `deepseek-v4-flash` and `deepseek-v4-pro`
- If `deepseek-chat` works but `v4-flash` doesn't, the check passes falsely
- **Fix:** Test the actual models used in routing, not just one representative.

---

## 6. CONFIG.YAML ANOMALIES

**ISSUE 18: `context.engine: compressor` is a ghost setting.**
- The config references a "compressor" context engine
- But `context_orchestrator.py` is the actual context engine, and it's not referenced here
- There may be a built-in "compressor" in the Hermes framework that's also active — two competing compression systems?
- **Fix:** Clarify: is the built-in compressor active, or is the orchestrator replacing it? If the orchestrator is the intended system, update the config or disable the built-in.

**ISSUE 19: `ephemeral_system_ttl: 0` contradicts context trimming.**
- Ephemeral system TTL of 0 means system messages never expire
- But the context orchestrator's T0 tier (which includes identity/system) is "never trimmed"
- These are aligned — but the system messages are set at the framework level, while the orchestrator manages the conversation window. If both systems are active, system messages could be duplicated or conflicting.

**ISSUE 20: `show_reasoning: false` contradicts transparency goals.**
- The operating agreement says "operates transparently"
- The architecture emphasizes deliberate model switching that the operator should understand
- But reasoning (chain-of-thought) is hidden from the operator
- **Fix:** Set `show_reasoning: true` at least for consult/merge operations, or add a command to toggle it on.

**ISSUE 21: `max_turns: 300` is dangerous without turn-based trimming.**
- 300 turns × even 2 sentences per turn = 600 sentences in context
- No active trigger to trim based on turn count (only token-based)
- **Fix:** Add a turn-based trim trigger. E.g., after 100 turns, force a mid-session trim regardless of token count.

---

## 7. SECURITY MODEL vs REALITY

**ISSUE 22: `redact_pii: false` + verbose logging = data leak risk.**
- Config has PII redaction disabled
- Logs include full conversation content
- Memory palace stores conversation episodes
- **Impact:** If the user discusses credentials, personal data, or proprietary code, it's stored in plaintext in multiple locations
- **Fix:** Enable `redact_pii: true`, or at minimum ensure the memory palace encrypts its contents (Issue 3).

**ISSUE 23: `allow_lazy_installs: true` is a supply chain risk.**
- Agent can install arbitrary packages via pip/npm on request
- A compromised model (or a prompt injection) could instruct the agent to install malicious packages
- The approval system (`Tier 2: APPROVED`) should catch this — but only if the agent requests approval. The operation may be framed as "installing a required dependency" and bypass review.
- **Fix:** Either disable lazy installs, or require explicit operator confirmation with package name + source.

**ISSUE 24: No egress filtering.**
- Security model says "Network Isolation: Cloud API calls go through direct HTTPS only"
- But the config enables web search, web extraction, browser automation, and image generation — all of which make arbitrary HTTPS calls
- "Direct HTTPS only" doesn't mean "only to known endpoints"
- **Fix:** Document that egress filtering isn't implemented and is planned for a future phase. Don't claim it exists.

**ISSUE 25: SSH access is both "Tier 2: APPROVED" and always-available in config.**
- Security model says SSH requires operator confirmation
- But `linux-ollama` is a configured provider with a base_url — the model can call it whenever needed
- **Fix:** If SSH is truly Tier 2, the Ollama endpoint shouldn't be pre-configured. Or document that the approval happens at setup time, not per-call.

---

## 8. CROSS-CUTTING ISSUES

**ISSUE 26: No integration tests.**
- Every component has a `__name__ == "__main__"` self-test
- No test verifies the full pipeline: message → classify → route → model → response → trim → persist
- **Impact:** The individual pieces may work perfectly but fail when connected. The gap between "built and tested standalone" and "works in the gateway" is exactly where bugs live.
- **Fix:** Create an integration test suite that mocks model APIs and tests the full message lifecycle.

**ISSUE 27: No dead letter queue or message replay.**
- If a message causes a crash (bad input, API error, encoding issue), it's lost
- No mechanism to replay failed messages after a fix
- **Fix:** Log all incoming messages to a `logs/inbox.jsonl` file. On startup, offer to replay the last failed message.

**ISSUE 28: Documentation inconsistency — "rock" = "grok".**
- `context-architect.md` says: 'Terminology: "rock" = "grok" — always substitute'
- This term is used nowhere in the codebase, the framework doc, or the model configs
- **Impact:** Dead documentation. If "rock" is ever used in a model's context, it's been manually substituted. If not, it's a lie in the identity block.
- **Fix:** Remove or actually implement (e.g., a pre-processor that replaces "rock" → "grok" in user inputs).

**ISSUE 29: Night Council doesn't include context orchestrator maintenance.**
- The Night Council reviews logs, health, and memory — but doesn't trigger orchestrator maintenance
- `context_orchestrator.py` should have a `maintenance()` or `nightly_cleanup()` function that:
  - Prunes expired episodes
  - Reviews confidence scores
  - Consolidates redundant facts
  - Checks DB size and vacuum if needed
- **Fix:** Add this to Night Council and document the dependency.

**ISSUE 30: `consul_merge.py` coupling with context orchestrator is undefined.**
- The consult/merge state machine needs to interact with the context orchestrator (to know current context, to add new turns, to trigger trims)
- But the interface between them is not defined in any code
- **Fix:** Define a clean API: `orchestrator.register_turn()`, `orchestrator.get_context()`, `orchestrator.consult(model_key, prompt)`, etc.

---

## 9. FUNDAMENTAL DESIGN CHALLENGES

### Is the Memory Palace the right architecture?

**Verdict: Yes, but the implementation is thin.**

The layered design (surface → episodic → semantic → working → mythic) is well-conceived. The problem is execution:
- The "mythic substrate" (narrative structures, quarterly update) doesn't exist
- Automatic fact extraction is crude (`_extract_facts`)
- The Palace is at 56KB with 15 episodes — fine now, but the automation layer needs to mature before it works at 100× this size
- Without good extraction, the Palace becomes a flat log with extra steps

**Recommendation:** Reduce reliance on auto-extraction for now. Store episodes manually tagged. Build semantic facts through the consult/merge cycle (Grok synthesizing episodes into facts, reviewed by Ring). This is more reliable than line-splitting heuristics.

### Is 6-tier trimming the right granularity?

**Verdict: Over-engineered for the current system, correct for the target system.**

With 6 models and ~8K-32K token budgets, 6 tiers gives meaningful control. But:
- T3 (semantic facts) vs T4 (background) is blurry in practice
- The distinction only matters when you're near the trim threshold
- At current usage levels (56KB DB, short sessions), you'll rarely hit trim thresholds
- **Recommendation:** Keep the 6-tier design on paper. Implement a simpler 3-tier runtime (keep/compress/delete) and add finer tiers when usage patterns show they're needed.

### Is the model chain correct?

**Verdict: Yes, with one critical addition needed.**

```
Mac qwen3:14b → DeepSeek v4-flash → Grok → Ring
                                           ↓
                                   Quality Gate
```

This is sound. The missing piece: **`qwen3-coder:30b-a3b`** needs to be added to the routing chain for complex reasoning tasks. It's on disk, it's provisioned, it just isn't wired in.

### Is hybrid compression the right approach?

**Verdict: Yes, but implementation gap is real.**

The framework describes: T5 compress → tag [COMPRESSED] → persist full text → rehydrate on demand. This is the correct theory. But:
- Compression requires a model call (cost + latency)
- Rehydration requires a Palace lookup (latency)
- At current usage, pure deletion might be simpler and adequate
- **Recommendation:** Implement T5 compression as a Phase 2 feature. For now, T5 → persist to Palace → delete from context. If the model asks about past tool output, it rehydrates from the Palace. This avoids the cost of compression while preserving the content.

---

## 10. PRIORITIZED FIX LIST

| # | Priority | Issue | Effort | Impact |
|---|---------|-------|--------|--------|
| 1 | **P0** | Wire context_orchestrator into gateway loop | High | Unlocks all context management |
| 2 | **P0** | Fix Telegram alerting (add token/chat_id to .env) | Low | Restores operator visibility |
| 3 | **P0** | Merge dual health tracking systems | Medium | Eliminates inconsistent model health data |
| 4 | **P1** | Add `qwen3-coder:30b-a3b` to routing config | Low | Completes planned model chain |
| 5 | **P1** | Fix key_guardian docs (it DOES make API calls) | Trivial | Honest documentation |
| 6 | **P1** | Add working memory session isolation | Medium | Prevents ghost state from dead sessions |
| 7 | **P1** | Enable `redact_pii` or encrypt memory DB | Low | Security compliance |
| 8 | **P2** | Replace keyword classification with confidence scoring | Medium | Better model routing |
|| **P2** | Add model-specific tokenizers | Medium | Accurate trim decisions |
| 9 | **P2** | Implement T5 compression + rehydration | High | Effective context management |
| 10 | **P2** | Add interrupt checkpoint (session_interrupt) | Medium | Crash recovery |
| 11 | **P2** | Add latency-based degradation detection | Low | Better failover decisions |
| 12 | **P3** | Night Council orchestrator maintenance | Low | Automated DB health |
| 13 | **P3** | Integration test suite | Medium | Confidence in connected system |
| 14 | **P3** | Dead letter queue + message replay | Low | Resilience to failures |
| 15 | **P3** | Encrypt memory DB (SQLCipher) | Medium | Security at rest |

---

## 11. CONFIRMED CORRECT DECISIONS

After exhaustive review, these decisions hold:

1. ✅ **Local-first model chain** — correct for latency, cost, privacy
2. ✅ **Deliberate routing (not reactive)** — correct for predictable behavior
3. ✅ **SQLite Memory Palace** — correct architecture, needs implementation depth
4. ✅ **6-tier priority system** — correct theory, simplify initial implementation
5. ✅ **Hybrid compression** — correct long-term, defer T5 compression to Phase 2
6. ✅ **Centralized .env vault** — correct and well-implemented
7. ✅ **Night Council cron** — correct, needs orchestrator integration
8. ✅ **Ring as quality gate** — correct use of 262K context window
9. ✅ **Consult/merge/become paradigm** — correct, limit to 3 hops
10. ✅ **Kimi in cold standby** — correct (4 cloud + 2 local = full coverage)

---

*Audit complete. The system's bones are good. The muscles and nerves need connecting.*