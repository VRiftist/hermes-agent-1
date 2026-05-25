# Model Roles & Memory Palace Integration — Decision Record

Date: 2026-05-25
Status: **DECIDED — Awaiting operator confirmation**

## Core Insight: The Palace Changes Everything

Before the Memory Palace, every piece of context had to live in the window. The 8B model was evaluated as a "compression engine" — rephrase and shrink to fit. **This framing is wrong.**

With the Palace, the architecture shifts from **"fit everything in the window"** to **"curate what enters the window."** The Palace is the infinite backing store; the context window is the working set.

---

## Updated Model Chain — Role Assignments (with Palace)

| Rank | Model | Provider | Job | Context Budget | Palace Role |
|------|-------|----------|-----|----------------|-------------|
| 1 | `qwen3:8b` | Mac Ollama | Quick tasks, trim decisions, local-first fallback | 8K (raw) / ~4K working set | Reads for dedup, writes trimmed state back |
| 2 | `qwen3:14b` | Mac Ollama | **Primary reasoning** — default for most tasks | 16K (raw) / ~10K working set | Reads/writes continuously; main Palace sync point |
| 3 | `qwen3-coder:30b-a3b` | Mac Ollama | Complex code gen, architecture, deep reasoning | 16K (raw) / ~8K working set | Reads architectural context, writes detailed decisions |
| 4 | `qwen3:8b` | Linux Ollama | Long-context processing (when online) | 16K (raw) / ~10K working set | Full Palace read for large document processing |
| 5 | `deepseek-v4-flash` | Cloud | Code review, logic analysis, debugging | 32K | Writes findings as semantic facts to Palace |
| 6 | `grok-4.20-reasoning` | Cloud (xAI) | Architectural decisions, critique, editorial | 16K | Reads architectural state from Palace |
| 7 | `ring-2.6-1t` | Cloud (OpenRouter) | **Quality gate** — final verification pass | **262K** | Reads full Palace + entire session for comprehensive check |
| 8 | `kimi-v1-8k` | Cloud (Moonshot) | Creative tasks (cold standby) | 8K | Writes creative artifacts to Palace |

---

## The 8B Question: Answered

**Should the 8B compress or delete?**

**Neither.** The 8B is a **long-context processing engine**, not a compression tool.

Here's why:

### Without Palace (old model)
```
[Identity][Task][History][Facts][Tool Output][Conversation]
         ↑ ALL must fit in window
         ↑ Compression is survival
```

### With Palace (new model)
```
PALACE (SQLite, unbounded):
  ├─ Episodic: full conversation history
  ├─ Semantic: extracted facts, relationships
  └─ Working: active task key-values

CONTEXT WINDOW (bounded):
  ├─ T0: Identity block (~500 tokens) ← NEVER trimmed
  ├─ T1: Active task state (~1K tokens) ← compress last
  ├─ T2: Recent highlights (~2K tokens) ← dedup Palace, compress
  ├─ T3: Semantic lookup (~2K tokens) ← PURELY Palace-backed, window copy disposable
  └─ T4-T6: Tool output + old turns ← delete or compress
         ↑ What matters is in the Palace, not the window
```

### Concrete Answer

| Aspect | Old Answer (pre-Palace) | New Answer (with Palace) |
|--------|------------------------|--------------------------|
| 8B primary job | Compress context to fit | **Curate window ↔ Palace boundary** |
| T3 (semantic facts) | Must compress | **Drop from window — Palace has it** |
| T5 (tool output) | Compress + tag | Still compress + `[COMPRESSED]` tag |
| T6 (old turns) | Delete (already planned) | Delete — Palace has the episode |
| Effective context | = window size | = **window size + Palace recall** |
| Compression urgency | High (8K is tight) | **Lower** (8B only needs ~4K working set) |

### Why This Changes the Budget Math

- **Mac 8B (Q4_K_M):** ~9GB total with KV cache. With a 4K working set + 500 token identity block, you have ~3.5K tokens of headroom. This is **comfortable**, not tight.
- **The 8B does NOT need to compress.** It needs to orchestrate: pull from Palace what's needed, push back what's learned, delete what's stale.
- Compression remains important for **T5 tool output** (2-4K tokens of raw JSON), but this is done by the orchestrator in Python, not by calling a model.

---

## Revised Compression Strategy (Palace-Aware)

### Before Model Invocation (Pre-Prompt)
1. Pull T0 identity from `context-architect.md`
2. Query Palace for relevant episodic + semantic memories matching task
3. Inject top-N Palace results into T3 slot
4. Check current token budget → if over warning, run mid-session trim

### After Tool Output (Post-Tool)
1. Parse tool result for extractable facts
2. Write high-value facts to Palace (semantic.db)
3. Replace raw tool output in context with `[COMPRESSED: <summary>]` tag
4. Log full tool output to JSONL for audit (not in context window)

### During Trim (Budget Exceeded)
1. **T6:** Delete oldest conversation turns (already in Palace as episodes)
2. **T5:** Compress tool output blocks → `[COMPRESSED: ...]`
3. **T4:** Dedup against Palace → delete if redundant, compress if unique
4. **T3:** Drop window copy (Palace has the source of truth)
5. **T2:** Compress to summary
6. **T1:** Compress only if budget still critical
7. **T0:** Never touched

---

## Metrics for Tuning

| Metric | Target | Measurement |
|--------|--------|-------------|
| Task completion rate | >95% | Did the model finish correctly? |
| Ring quality gate pass rate | >90% | Does Ring approve final output? |
| Token efficiency | >60% useful | (useful retained tokens) / (total pre-trim) |
| Palace recall hit rate | >70% | % of queries where Palace had relevant info |
| Compression ratio (T5) | >4:1 | (original tokens) / (compressed tokens) |
| Trim frequency | <2 per task | How often mid-session trim fires |
| End-to-end latency | <30s per turn | User message → response |
| Fallback rate | <5% | Tasks hitting fallback in chain |
| Palace growth rate | <100 facts/session | Watch for bloat |
| DB size | <1MB | Palace SQLite file size |

### Tuning Methodology
1. **Weekly:** Run `night_council.py` and examine metrics
2. **A/B:** When changing trim thresholds, run 10 tasks old vs 10 new, compare Ring pass rates
3. **Monthly:** Palace quality audit — remove stale/incorrect semantic facts
4. **Per-model addition:** Run 20-task benchmark before promoting to active chain

## Decision Summary

1. ✅ 8B is a long-context worker, NOT a compressor — Palace handles storage
2. ✅ Hybrid compression confirmed — T5 compress, T6 delete, T3 dedup-to-Palace
3. ✅ Effective context = window + Palace recall (the key architectural shift)
4. ✅ 8B budget ~4K working set is comfortable with headroom
5. ✅ Metrics defined for all critical dimensions
6. ⏳ Palace-aware trim integration pending in `context_orchestrator.py`