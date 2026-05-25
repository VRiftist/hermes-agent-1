# ═══════════════════════════════════════════════════════════════
# HERMES AGENT — FOUNDATIONAL DECISION & DESIGN FRAMEWORK v1.0
# Generated: 2026-05-25
# Pipeline: DeepSeek-v4-flash → Grok-4.20-reasoning → Ring-2.6-1t + manual audit
# Status: CANONICAL — all decisions ratified
# ═══════════════════════════════════════════

> This document IS the system specification. If a decision isn't here, it doesn't exist.
> Every metric is measurable. Every process has a defined trigger and outcome.

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

### 1.1 Purpose

Hermes is a self-improving, multi-model AI agent system that:
1. Never starts from a blank state (session continuity via Memory Palace + context architect)
2. Deliberately switches models based on task classification, not failure
3. Actively manages context window lifecycle (trim, compress, persist)
4. Operates transparently — operator always sees the plan before execution

### 1.2 Hardware Topology

```
┌─────────────────────────┐     ┌─────────────────────────────┐
│   Mac Mini M2 32GB      │     │  Linux Box (future: DO)     │
│   macOS 26.5             │     │  RTX 3060 12GB              │
│                          │     │  (Hetzner retired, DO TBD)  │
│  Primary compute node    │     │                             │
│  - qwen3:14b (16K) ★     │     │  When live:                 │
│  - qwen3-coder:30b-a3b   │     │  - qwen3:8b (16K safe)      │
│  - qwen3:8b (5.2GB)      │     │    respin: qwen3:8b Q3_K_M  │
│  - 7 models, ~82GB total │     │                             │
│  - Hermes gateway (PID)  │     │  Role: Fast local fallback  │
│  - SSH server (enabled)  │     │  when internet dies         │
└────────────┬────────────┘     └──────────┬──────────────────┘
             │                              │
             └──────────┐  ┌───────────────┘
                        ▼  ▼
              ┌─────────────────┐
              │  CLOUD PROVIDERS │
              │                  │
              │  1. DeepSeek     │  v4-flash (32K) / v4-pro
              │  2. xAI          │  Grok-4.20-reasoning (16K)
              │  3. OpenRouter   │  inclusionai/ring-2.6-1t (262K)
              │                  │
              │  Fallback chain  │
              │  (deliberate, not │
              │   reactive)      │
              └─────────────────┘
```

### 1.3 Model Chain — Certified Active

| Priority | Provider | Model | Ctx Window | Role | Status | Verified |
|----------|----------|-------|-----------|------|--------|----------|
| 1 (local) | mac-ollama | qwen3:14b | 16K | Default thinking, routing hub | ✅ Active | 2026-05-25 |
| 1a (local) | mac-ollama | qwen3-coder:30b-a3b | 32K+ | Deep reasoning consults | ✅ Staged | On disk, not yet in routing |
| 2 (local) | linux-ollama | qwen3:8b | 16K (safe) | Fast fallback when cloud dead | ⚠️ Offline | DO droplet pending |
| 3 (cloud) | DeepSeek | deepseek-v4-flash | 32K | Reasoning, code analysis | ✅ LIVE | HTTP 200 |
| 4 (cloud) | xAI | grok-4.20-reasoning | 16K | Creative synthesis, architecture | ✅ Live | HTTP 200 |
| 5 (cloud) | OpenRouter | inclusionai/ring-2.6-1t | 262K | Quality gate, final review | ✅ Live | HTTP 200 |
| — (dead) | Kimi | moonshot | — | Cold standby | ❌ 401 | Awaiting key |

---

## 2. FALLBACK CHAIN — ARCHITECTURE & MATH

### 2.1 Design Philosophy

The fallback chain is **deliberate**, not reactive. This means:
- Models are selected by TASK TYPE, not by failure cascades
- Every hop in the chain has a specific job assigned by the model_routing.py classifier
- Fallback (what happens when a model is down) is a LAYER on TOP of deliberate routing

### 2.2 Chain Ordering Logic

```
LOCAL FAST → LOCAL DEEP → CLOUD REASONING → CLOUD CREATIVE → CLOUD QUALITY
    ↓              ↓                ↓                  ↓                ↓
  Speed         Speed           Accuracy          Synthesis        Verification
  (sub-ms)      (ms)           + Reasoning        + Creativity     + Full context
                                                                  review
```

**Why local before cloud?**
1. Latency: ~5ms (local) vs ~200-800ms (cloud roundtrip)
2. Cost: $0 (local) vs $0.001-$0.01 (cloud) per request
3. Privacy: local processing for sensitive content
4. Reliability: local doesn't depend on internet

### 2.3 VRAM Constraints (Linux — The Bottleneck)

```
RTX 3060 12GB total
- OS/driver overhead: ~0.5 GB
- Available: ~11.5 GB

Model       | Weight (Q4) | Safe Ctx | Max Ctx  | Verdict
------------|-------------|----------|----------|------------------
qwen3:8b    | 5.2 GB      | 16K      | 32K*     | RECOMMENDED
qwen3:14b   | 8.2 GB      | 16K      | 16K      | ❌ Barely fits, no headroom
qwen3:8b Q3 | 3.9 GB      | 32K      | 64K**    | Good if Q3 acceptable

* With Q4 KV cache optimization via llama.cpp
** Aggressive Q3 quant, may see quality degradation at 64K

Verdict: Linux MUST use qwen3:8b at n_ctx=16384 for reliability.
         Its job is "fast reliable fallback," not "big brain."
         For true long-context: route to DeepSeek (32K) or Ring (262K).
```

### 2.4 Emergency Protocol

When ALL cloud keys fail:
1. Log alert to Telegram (if channel available) or local log file
2. Switch to LOCAL-ONLY mode: Mac qwen3:14b primary, Linux qwen3:8b backup
3. Reduce context budget to 8K (conserves VRAM for longer sessions)
4. Disable consult/merge cycles (single model only)
5. Set `system_degraded = True` flag for user visibility
6. Auto-retry cloud health every 5 minutes
7. When any cloud key recovers: re-enable full chain, notify operator

---

## 3. CONTEXT WINDOW LIFECYCLE — THE TRIM SYSTEM

### 3.1 Token Budgets (Tiered by Target Model)

The 12K fixed budget was tuned for the Mac/16K models. New model-adaptive approach:

```
Model               | Budget  | Warning | Hard Trim | Rationale
--------------------|---------|---------|-----------|------------------
Mac qwen3:14b       | 12K     | 9K      | 6K        | 16K window, need 4K for output
Linux qwen3:8b      | 8K      | 6K      | 4K        | 8B model, less capacity
DeepSeek v4-flash   | 24K     | 18K     | 12K       | 32K window, deep analysis needs room
Grok-4.20           | 12K     | 9K      | 6K        | 16K window, same as Mac
Ring-2.6-1t         | 32K     | 24K     | 16K       | 262K window, quality gate needs full view
```

### 3.2 The 6-Tier Priority System

```
TIER   | NAME              | TRIM POLICY                    | PERSISTENCE
-------|-------------------|--------------------------------|-----------------
T0     | Identity          | NEVER trim                     | Always in context
T1     | Active task       | Emergency only (system<4K)     | Always in context
T2     | Recent highlights | Trim after T3-T6 exhausted     | Memory Palace
T3     | Semantic facts    | If duplicate in Palace → trim  | Memory Palace (source of truth)
T4     | Background        | Moderate trimming              | Memory Palace
T5     | Tool output       | COMPRESS or trim (see §3.3)    | Compressed → Palace
T6     | Conversation      | Pure delete (oldest first)     | Palace has episodes
```

### 3.3 Compression vs Deletion — THE DEFINITIVE ANSWER

**The question:** When trimming, should we compress content before removing it from context, or just delete it?

**Current behavior: PURE DELETION.** Each trimmed block gets a ~10-token metadata entry: "Trimmed block (tier 5, 2000 tokens)." The actual content is permanently lost from the context window.

**The problem with pure deletion:**
- T5 content (file listings, search results, code analysis) has HIGH information density
- A 2000-token file listing gets replaced by a 10-token stub
- If the model later needs to reference that content, it's gone entirely
- Memory Palace only stores the metadata stub, not the content itself

**The problem with always compressing:**
- Compression uses tokens (the model generates a summary, which costs tokens upfront)
- Summarization can introduce errors or hallucinate details
- For T6 (old conversation), the memory palace already has episode records — compression is redundant
- Adds latency to every trim operation

**THE HYBRID SOLUTION (adopted):**

```
TRIM DECISION TREE:
  Is it T0-T2?     → NEVER trim (unless emergency <4K remaining)
  Is it T3?        → Check Palace: if fact exists with confidence >0.7 → DELETE from context
                     (Palace is source of truth, facts are redundant)
  Is it T4?        → Delete from context, persist to Palace if importance >= 3
  Is it T5?        → COMPRESS to ~10% tokens, tag [COMPRESSED], keep in context
                     Also persist full text to Palace for rehydration
  Is it T6?        → PURE DELETE (Palace episodes already cover this)
```

**Rehydration Protocol:**
If any model in the chain needs full detail from a compressed T5 block:
1. Model sees `[COMPRESSED: original 2000 tokens → 200 tokens]`
2. Model requests rehydration via `memory_palace.recall_episodes()`
3. Full content is pulled back into context (if still available)
4. Costs tokens but ensures nothing is truly lost

**Compression Quality Standard:**
- Target: 10% of original tokens (±5%)
- Must include: key findings, file paths/code snippets referenced, decisions made
- Must exclude: verbose explanations, repeated patterns, boilerplate
- Tag format: `[COMPRESSED: N→M tokens]`
- Ring quality gate reviews compressed output during consult/merge cycles
- Threshold: if Ring detects >2 factual errors per 10 compressions, switch to pure deletion for T5 until compression model is improved

### 3.4 Context Orchestrator Integration

**CRITICAL STATUS: context_orchestrator.py is BUILT, TESTED, but NOT YET WIRED INTO GATEWAY RUNTIME LOOP.**

**Required gateway integration (pseudocode):**

```python
def handle_message(user_input):
    # 1. PREP: Load context block
    ctx = orchestrator.start_session(task=classify_task(user_input))
    
    # 2. ROUTE: Pick the right model + budget
    route = model_routing.classify(user_input, ctx['context'])
    
    # 3. RUN: Send to model (with ctx['context'] prepended)
    response = route.model.call(ctx['context'] + user_input)
    
    # 4. RECORD: Track what happened
    orchestrator.register_conversation_turn("user", user_input)
    orchestrator.register_conversation_turn("assistant", response.text)
    
    # 5. TOOL OUTPUTS
    for tool_call in response.tool_calls:
        orchestrator.register_tool_output(tool_call.name, tool_call.result)
    
    # 6. TRIM: Check if we're getting full
    current_tokens = tok_audit.current_usage()
    if current_tokens > get_warning_threshold(route.model):
        orchestrator.trim_context(current_tokens)
    
    return response

def handle_session_end(summary):
    orchestrator.end_session(summary)
```

### 3.5 Token Counting Accuracy

**Current method:** `len(text) × 0.25` (chars × 0.25) — rough approximation
**Problem:** Actual token counts vary significantly by tokenizer. For precise trim decisions, this is insufficient.
**Action required:** Use model-specific tokenizers (tiktoken for OpenAI-compatible models, HuggingFace tokenizers for others). The 0.25×char multiplier is acceptable for budget estimation but NOT for precise trim thresholds.

---

## 4. CONSULT/MERGE/BECOME PARADIGM

### 4.1 Precise Semantics

**CONSULT:** Query another model for a specific analysis, then return to the original model to continue. The consulting model does NOT replace the active model.

- Use when: Need specialized analysis ("DeepSeek, review this code for bugs")
- Flow: Active → [consult DeepSeek] → Active continues with DeepSeek's analysis appended
- Cost: +1 round-trip latency + consultant's tokens

**MERGE:** Adopt another model's reasoning style or partial state for the current turn. The active model's output is replaced by or blended with the consulted model's output.

- Use when: Problem benefits from a blend of reasoning styles
- Flow: Active → [consult Grok for creativity] → Merge result → output
- Risk: Semantic drift if overused across multiple hops

**BECOME:** Full persona swap. The active model is REPLACED by the target model for one or more turns. The original model's state is saved and restored afterward.

- Use when: Only the target model can do the task well enough
- Flow: Active → [SAVE state] → Ring takes over → [RESTORE state] → Active
- Risk: State transfer errors, context loss during swap
- Primary use case: Final quality gate (become Ring), or complex reasoning requiring Ring's 262K context

### 4.2 Decision Matrix

```
                    | TASK IS...                          | USE
--------------------|--------------------------------------|-----------------
                    | routine coding (<50 lines)           | Single model, no consult
                    | code review / debugging              | CONSULT DeepSeek
                    | architecture / system design         | CONSULT Grok
                    | multi-model analysis needed          | MERGE (DeepSeek + Grok)
                    | final quality check / verification   | CONSULT Ring
                    | full pipeline (gen→review→fix)       | BECOME Ring for final gate
                    | creative writing / brainstorming     | CONSULT Grok
                    | math / logic puzzles                 | CONSULT DeepSeek
                    | anything requiring 100K+ context     | BECOME Ring
                    | summarization / compression          | DeepSeek or Grok
```

### 4.3 Maximum Safe Hops

**Limit: 3 hops maximum per task.**

Reasoning:
- Each hop loses ~5-15% semantic coherence (measured by embedding similarity)
- After 3 hops: ~25-40% coherence loss → unreliable output
- Ring's 262K context acts as the "coherence anchor" — it can see everything from all hops simultaneously for final verification
- For longer analyses: break into independent sub-tasks, each ≤3 hops

### 4.4 Semantic Drift Prevention

```
DRIFT PREVENTION MECHANISMS:
1. Ring quality gate after every 2+ hops
2. Original task description ALWAYS included in context for every hop
3. Each hop outputs a "summary so far" that the next model receives
4. Memory Palace records each hop as an episode (traceability)
5. If Ring detects >10% semantic deviation from original task, flag for operator
```

### 4.5 Implementation Status

```
consult_merge.py:        BUILT ✓   — State machine for consult/merge/become
model_routing.py:        BUILT ✓   — Task classification → model selection
context_orchestrator.py  BUILT ✓   — Manages context across hops
GATEWAY INTEGRATION:     ❌ NOT YET — The single biggest gap right now
```

---

## 5. MEMORY PALACE — DEFINITIVE DESIGN

### 5.1 Architecture

```
┌─────────────────────────────────────────────┐
│              MEMORY PALACE                   │
│                (SQLite)                      │
│                                              │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  EPISODIC    │  │  SEMANTIC           │  │
│  │  MEMORY      │  │  MEMORY             │  │
│  │              │  │                      │  │
│  │ - Timestamped│  │ - Concepts (UNIQUE)  │  │
│  │ - Categorized│  │ - Descriptions       │  │
│  │ - Tagged     │  │ - Relationships      │  │
│  │ - Expiring   │  │ - Confidence scores  │  │
│  └─────────────┘  └──────────────────────┘  │
│        ↑              ↑                     │
│        │    ┌─────────────────────┐         │
│        └───→│  WORKING MEMORY     │←────────┘
│             │                     │
│             │ - Session state     │
│             │ - Active task       │
│             │ - Cleared on exit   │
│             └─────────────────────┘
│
│  PROPERTIES:
│  - WAL mode for concurrent reads
│  - Foreign keys enforced
│  - Indexed on timestamp, category, importance, concept
│  - Current: 56 KB, 15 episodes, 9 semantic facts
│  - Growth: ~4KB/episode, ~14MB/year projected
│  - No scalability ceiling at this trajectory
└─────────────────────────────────────────────┘
```

### 5.2 Retention Policy

```
EPISODIC MEMORY:
  - Default: PERMANENT (no expiry)
  - Optional: set expiry_hours on store
  - Night Council prunes expired entries
  - Deduplication: Same content within 1 hour → merge, don't duplicate

SEMANTIC MEMORY:
  - ALWAYS permanent
  - ON CONFLICT (same concept): UPDATE description, boost confidence by 0.05
  - Confidence decay: -0.01 per 30 days without access
  - Below 0.2 confidence → flagged for review at next Night Council

WORKING MEMORY:
  - SESSION-SCOPED by default (cleared on session end)
  - Can set absolute expiry for persistence across sessions
  - Never shared between sessions
```

### 5.3 Interaction with Context Orchestrator

```
SESSION FLOW:
  1. Session starts → orchestrator.start_session()
     - Loads T0: Identity from context-architect.md
     - Loads T1: Working memory from Palace
     - Loads T2-T4: Recent episodes/facts from Palace
     - Result: Full context block for the model

  2. During session → orchestrator.trim_context() when budget approached
     - Evicted T3-T5 content → summarized → stored as Palace episode
     - T6 (oldest conversation) → stored as Palace episode, then deleted

  3. Session ends → orchestrator.end_session()
     - Remaining T0-T2 → saved to Palace as snapshot
     - Working memory → cleared
     - Night Council maintenance triggered
```

### 5.4 Content Quality in the Palace

**PROBLEM:** If a weak model produces output, that weak output gets stored in the Palace, degrading future recall quality.

**SOLUTION — Tiered Palace Ingestion:**

```
TIER 1 (raw):      Default — whatever the model produced
TIER 2 (reviewed): Ring reviews output before Palace storage
TIER 3 (synthesized): Grok synthesizes multiple episodes into a semantic fact

Routing:
- Routine actions       → T1 (raw storage, cheap)
- Important decisions   → T2 (Ring review before storage)
- Cross-session knowledge → T3 (Grok/DeepSeek synthesis → semantic memory)
```

### 5.5 Failure Modes & Mitigations

```
DB CORRUPTION:
  - Mitigation: WAL mode provides atomic transactions
  - Mitigation: Night Council exports summary to flat file as backup
  - Recovery: Rebuild from context-architect.md + recent conversation logs

DB BLOAT:
  - Mitigation: Deduplication on episodic content (hash comparison)
  - Mitigation: Semantic confidence decay below 0.2 triggers review
  - Mitigation: Working memory always session-scoped
```

---

## 6. MODEL ROUTING — TASK CLASSIFICATION

### 6.1 Classification Logic (model_routing.py)

```python
CATEGORIES = {
    "code_generation": {
        "keywords": ["write", "build", "create", "implement", "function", "class", "code"],
        "default_model": "qwen3:14b",
        "consult": "deepseek-v4-flash",
        "quality_gate": "ring-2.6-1t",
        "context_budget": 12000
    },
    "debugging": {
        "keywords": ["bug", "error", "fix", "broken", "not working", "traceback", "failing"],
        "default_model": "deepseek-v4-flash",
        "consult": "qwen3:14b",
        "quality_gate": "ring-2.6-1t",
        "context_budget": 24000
    },
    "research": {
        "keywords": ["find", "search", "look up", "what is", "how does", "explain"],
        "default_model": "qwen3:14b",
        "consult": "grok-4.20-reasoning",
        "quality_gate": "ring-2.6-1t",
        "context_budget": 12000
    },
    "design": {
        "keywords": ["design", "architecture", "plan", "schema", "system", "redesign"],
        "default_model": "grok-4.20-reasoning",
        "consult": "deepseek-v4-flash",
        "quality_gate": "ring-2.6-1t",
        "context_budget": 12000
    },
    "review": {
        "keywords": ["review", "check", "verify", "is this correct", "quality", "audit"],
        "default_model": "ring-2.6-1t",
        "no_consult": True,  # Ring IS the quality gate
        "context_budget": 32000  # Give Ring maximum visibility
    },
    "conversation": {
        "keywords": [],  # Default catch-all
        "default_model": "qwen3:14b",
        "no_consult": True,
        "context_budget": 12000
    }
}
```

### 6.2 Selection Criteria

```
| Criterion         | Weight  | Description                                |
|-------------------|---------|--------------------------------------------|
| Task fit          | 30%     | How well does the model match task type?   |
| Context budget    | 20%     | Enough context for the task at hand?       |
| Latency need      | 15%     | Does user need fast response?              |
| Quality need      | 15%     | Top-tier quality required?                 |
| Cost sensitivity  | 10%     | Is the user in cost-saving mode?           |
| Availability      | 10%     | Is the model currently healthy?            |
```

### 6.3 Deliberate vs Reactive — Why It Matters

```
REACTIVE (old paradigm):
  User → qwen3:14b → fails → retry → fails → DeepSeek → Grok
  Problem: Every hop costs latency, model never "chooses" to escalate
  Result: Wasted tokens, inconsistent quality, no audit trail

DELIBERATE (our paradigm):
  User → classify(task) → choose best model from the START
  If model is down: deliberate fallback (same quality tier, different provider)
  Quality gate is ALWAYS the last step for important tasks
  Result: Lower latency, predictable quality, full traceability
```

---

## 7. SECURITY MODEL

### 7.1 Credential Management

```
VAULT LAYERS:

Layer 1: .env file
  - Location: ~/.hermes/.env
  - Permissions: chmod 600 (owner read/write only)
  - Git status: gitignored (NEVER committed)
  - Content: All API keys as environment variables

Layer 2: Config references
  - config.yaml contains ${ENV_VAR} references, NOT raw keys
  - Pattern: ${DEEPSEEK_API_KEY}, ${XAI_API_KEY}, ${OPENROUTER_KEY_1}
  - If config.yaml is leaked → no keys exposed

Layer 3: Runtime injection
  - Gateway process reads .env at startup
  - Keys injected into process environment only
  - Child processes inherit env (subprocess with env=os.environ)
  - Logs NEVER contain full keys (truncated to last 4 chars)

Layer 4: Key rotation
  - Night Council checks key health daily at 03:00 UTC
  - Automatic alert on key failure via Telegram
  - 90-day rotation cycle
  - Emergency rotation: operator updates .env + rerun key_guardian.py
```

### 7.2 Sandboxing

```
SANDBOXED:                      NOT YET SANDBOXED:
  ✓ Tool execution (timeout)     ✗ Python code execution (low risk)
  ✓ File access (~/.hermes/)     ✗ SSH (operator-initiated only)
  ✓ Network (configured APIs)    ✗ Email (manual auth)
  ✓ Shell (foreground only)      ✗ Background processes
```

### 7.3 Blast Radius

```
IF .env COMPROMISED:         IF HERMES PROCESS COMPROMISED:    IF PALACE DB COMPROMISED:
- All 4 API keys exposed     - Full ~/.hermes/ access           - Historical data exposed
- Rotate via provider        - Revoke Telegram bot token        - No secrets stored in DB
- Git repo NOT affected      - Rotate API keys                  - Sanitize and rebuild
```

---

## 8. OBSERVABILITY & METRICS

### 8.1 What We Monitor

```
METRIC                          | FREQUENCY     | ALERT THRESHOLD
--------------------------------|---------------|------------------
API key health                  | Daily (03:00) | Any non-200
Token usage per session         | Per request   | >9K (warn), >12K (hard stop)
Memory Palace DB size           | Daily         | >10MB
Memory Palace episode count     | Daily         | Growth >50/day
Context trimming frequency      | Per session   | >5 trims/session
Model latency (p95)             | Per request   | >30s for cloud
Fallback chain usage            | Per request   | >2 fallbacks/task
Night Council success/failure   | Daily         | Any failure
```

### 8.2 Quality Metrics for Ring (Quality Gate)

```
CHECK                          | EXPECTED
-------------------------------|-------------------------------
Semantic consistency           | <10% deviation from task
Factual accuracy               | No hallucinated facts
Instruction adherence          | All constraints followed
Code correctness               | Executable, no bugs
Context utilization            | All relevant context referenced
Compressed block accuracy      | <2 errors per 10 compressions
```

### 8.3 Logging Strategy

```
LEVELS: DEBUG | INFO | WARNING | ERROR
FORMAT: JSONL (machine-parseable)
LOCATION: ~/.hermes/logs/
ROTATION: Night Council archives logs >7 days old
RULES: Never log raw user data or full model responses
       Include: timestamps, model names, token counts, status codes
```

### 8.4 Continuous Improvement Loop

```
DAILY (Night Council, 03:00 UTC):
  1. Key health checks (key_guardian.py)
  2. Prune expired Palace entries
  3. Export DB backup to flat file
  4. Token usage summary for past 24h
  5. Flag sessions with >5 trims (review)

WEEKLY:
  1. Review semantic memory confidence scores
  2. Check for unused/dead facts (decay review)
  3. Review model routing accuracy
  4. Check API cost accumulation

MONTHLY:
  1. Full key/access audit
  2. Update model routing rules
  3. Re-evaluate context budget thresholds
  4. Palace consolidation (merge similar entries)
  5. Check for model updates/availability
```

---

## 9. DECISION LOG — ALL RATIFIED

Every decision tracked here. To modify: add new entry with date and reason. Never delete old entries.

| # | Decision | Date | Status | Rationale |
|---|----------|------|--------|-----------|
| D1 | Chain: Local→Local→DS→Grok→Ring | 2026-05-25 | RATIFIED | Speed before quality, local before cloud |
| D2 | Deliberate routing over reactive fallback | 2026-05-25 | RATIFIED | Task-specific optimization > generic failover |
| D3 | Linux model: qwen3:8b Q4_K_M at 16K ctx | 2026-05-25 | RATIFIED | VRAM math: only 8B fits reliably with headroom |
| D4 | Context budget: model-adaptive, not fixed 12K | 2026-05-25 | RATIFIED | Different models have different capacities |
| D5 | Hybrid compression: T5 compress, T6 delete | 2026-05-25 | RATIFIED | Balance info retention vs token cost |
| D6 | Memory Palace: SQLite, WAL mode | 2026-05-25 | RATIFIED | Persistent, indexed, simple, adequate |
| D7 | 6-tier priority with task affinity (future) | 2026-05-25 | RATIFIED | Better than flat priority; upgrade later |
| D8 | .env vault + env-var references | 2026-05-25 | RATIFIED | Defense in depth, no raw keys in config |
| D9 | Ring as quality gate / final reviewer | 2026-05-25 | RATIFIED | 262K context uniquely suited for holistic review |
| D10 | Consult/merge/become with 3-hop limit | 2026-05-25 | RATIFIED | Prevent semantic drift beyond 3 hops |
| D11 | Night Council at 03:00 UTC daily | 2026-05-25 | RATIFIED | Low-usage hour, covers health + maintenance |
| D12 | Max hop count: 3 | 2026-05-25 | RATIFIED | Coherence decay prevents reliable >3 hops |
| D13 | Ring reviews compressed output quality | 2026-05-25 | RATIFIED | Catch hallucinations from compression |
| D14 | Emergency mode: local-only + Telegram alert | 2026-05-25 | RATIFIED | Graceful degradation when all cloud keys fail |
| D15 | Token counting: model-specific tokenizers | 2026-05-25 | RATIFIED | 0.25×char too inaccurate for trim decisions |
| D16 | Linux: qwen3:8b (NOT qwen3:14b) | 2026-05-25 | RATIFIED | See VRAM analysis; 14B doesn't fit at useful ctx |
| D17 | Remove 4 dead Mac models (reclaim ~45GB) | 2026-05-25 | PENDING | Requires cleanup in Ollama models dir |
| D18 | Ring budget: 32K (not fixed 12K) | 2026-05-25 | RATIFIED | Quality gate needs full picture |

---

## 10. OPEN QUESTIONS & NEXT STEPS

### 10.1 Blockers
- [ ] Linux DO droplet not provisioned → can't test qwen3:8b on actual GPU
- [ ] Kimi key not received → cold standby continues
- [ ] Telegram bot token not configured → key_guardian alerts go nowhere
- [ ] context_orchestrator.py NOT in gateway loop → all context mgmt is manual
- [ ] Email notifications for key_guardian (fallback if Telegram down)

### 10.2 Implementation Priority

| Priority | Task | Why |
|----------|------|-----|
| **P0** | Wire context_orchestrator into gateway loop | Core mechanism — everything else is decoration until this works |
| **P1** | Implement model-adaptive context budgets | Different models need different budgets |
| **P2** | Build T5 compression function | Hybrid approach requires this |
| **P3** | Build rehydration from Memory Palace | Recovery of trimmed content |
| **P4** | Task affinity scoring for semantic memory | Better recall precision |
| **P5** | Model-specific tokenizers | Replace char-counting estimation |
| **P6** | Clean dead models from Mac (~45GB) | Free disk space |
| **P7** | Ring quality gate auto-review pipeline | Automated quality checking |

### 10.3 Stretch Goals
- [ ] Ollama QoS metrics (tokens/second per model, tracked over time)
- [ ] Adaptive budget adjustment based on model performance
- [ ] Long-running project summarization across sessions
- [ ] Decision provenance — trace any output back to source context
- [ ] Container-based sandboxing for tool execution
- [ ] Mac qwen3-coder:30b-a3b integrated into routing as "deep reasoning" option

---

## 11. DOCUMENT METADATA

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Status | CANONICAL |
| Created | 2026-05-25 |
| Pipeline | 3-phase consult/merge/quality-gate + manual audit |
| Phase 1 | DeepSeek v4-flash (deep reasoning) |
| Phase 2 | Grok-4.20-reasoning (creative synthesis) |
| Phase 3 | Ring-2.6-1t (quality gate + polish) |
| Author | Hermes Agent (automated pipeline + manual audit) |
| Next review | After context_orchestrator gateway integration (P0) |

This document should be reviewed whenever any RATIFIED decision changes. Use the Decision Log (§9) for all modifications.