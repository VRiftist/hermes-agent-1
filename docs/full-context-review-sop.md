# Full Context Review — Standard Operating Procedure

## Overview

Full context review is the ability to feed an entire document, codebase, or conversation
history to an LLM and get a comprehensive analysis. This SOP defines how we do it,
which models to use, and the architectural decisions behind it.

---

## 1. Why Full Context Review Matters

Traditional approach: chunk text → summarize each chunk → stitch summaries together.
This loses cross-chapter references, subtle dependencies, and global structure.

**Our approach:** Use models with native large context windows to process everything in one pass.

---

## 2. Architecture — Three-Tier Model Stack

| Tier | Model | Context | Role | When to Use |
|------|-------|---------|------|-------------|
| **L1 — Brain** | Ring 2.6-1t (OpenRouter) | 131K | Complex reasoning, architecture decisions | Hard analysis, code review planning |
| **L2 — Workhorse** | DeepSeek Flash (API) | 262K | Bulk processing, summarization | Full doc review, codebase analysis |
| **L3 — Edge** | qwen-coder-32b-96k (Linux GPU) | 96K | Fast local execution, privacy-sensitive tasks | Offline analysis, dev loop |

---

## 3. Full Context Review Workflow

### 3.1 — Input Preparation
```
Document/Codebase → Tokenize → Estimate size → Route to appropriate tier
```

**Rules:**
- < 8K tokens → Mac local (qwen3:8b, fast)
- 8K–96K tokens → Linux GPU (qwen-coder-32b-96k)
- 96K–262K tokens → DeepSeek Flash (API)
- > 262K tokens → Ring 2.6-1t with active context trimming
- Multi-document cross-ref → Always L1 or L2

### 3.2 — Review Types

**A. Full Code Review**
- Feed entire codebase or large PR
- Ask for: bugs, architectural issues, style violations, test coverage gaps
- Model: Ring 2.6-1t (best reasoning) or 96K local (fast iteration)

**B. Document Analysis**
- Feed full document set
- Ask for: summary, contradictions, missing sections, action items
- Model: DeepSeek Flash (handles more text, cheaper)

**C. Conversation History Review**
- Feed full session history
- Ask for: decision summary, open questions, next steps
- Model: Ring 2.6-1t or DeepSeek Flash

### 3.3 — Prompt Template

```
You are performing a full-context review. Process the entire document below
and answer the questions that follow. Do not summarize prematurely — read
EVERY section before answering.

--- BEGIN DOCUMENT ---
{full_text}
--- END DOCUMENT ---

Review questions:
1. What is the main argument/architecture?
2. What are the key decisions made?
3. Are there any contradictions or gaps?
4. What would you improve?
5. (Domain-specific questions)
```

---

## 4. Active Context Trimming (for >262K inputs)

When input exceeds the best available context window:

### Tier 1 — Essential (always included)
- System prompt, user identity, current task definition
- Most recent 2K tokens of active conversation

### Tier 2 — Recent (last 30 minutes)
- Recent exchanges, current working documents
- ~16K tokens

### Tier 3 — Compressed (current session)
- LLM-generated summary of earlier conversation
- ~4K tokens at 10:1 compression ratio

### Tier 4 — Evicted (archived)
- Stored in Memory Palace for retrieval if needed
- Not in active context

---

## 5. Benchmarks — Expected Performance

### Linux GPU (RTX 3060 12GB)
| Model | Max Context | Latency @ Max | VRAM Usage |
|-------|------------|---------------|------------|
| qwen-coder-32b-96k | ~96K (estimated) | TBD | ~8-10GB |
| qwen3:8b | ~32K | <5s | ~4GB |

### Mac M2 Pro (CPU only)
| Model | Max Practical | Latency @ Max | Notes |
|-------|--------------|---------------|-------|
| qwen2.5-coder:32b | ~8K | ~10s | CPU only, not viable for large context |
| qwen3:8b | ~4-6K | ~3s | Fine for small tasks |

### API Providers
| Model | Context | Cost per 1M tokens | Best For |
|-------|---------|-------------------|----------|
| Ring 2.6-1t | 131K | $$ | Complex reasoning |
| DeepSeek Flash | 262K | $ | Bulk processing |

---

## 6. Decision Matrix — "Which Model?"

```
START
  │
  ├─ Need deep reasoning/architecture? → Ring 2.6-1t
  │
  ├─ Processing large docs (>96K tokens)? → DeepSeek Flash
  │
  ├─ Fast iteration, privacy needed? → Linux GPU (96K model)
  │
  └─ Small task, low latency? → Mac local (8B)
```

---

## 7. Enterprise Considerations

- **Vault integration:** API keys stored in encrypted `.env` (transitioning to HashiCorp Vault)
- **Secrets file:** `~/.hermes/.env` with `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `XAI_API_KEY`
- **Audit trail:** All full-context reviews logged with model, context size, latency, cost
- **Cost control:** Auto-route to cheapest model that meets context requirements
- **Data sovereignty:** GPU-local for sensitive data, API for non-sensitive

---

## 8. Open Questions

1. Do we need the 14B model (qwen3:14b) for anything? It might be useful for
   "middle-tier" reviews that are too big for 8B but don't need 32B reasoning.
   
2. Should we fine-tune or create a custom "review" persona for any of these models?

3. What's the acceptable latency ceiling for full-context reviews?
   - Interactive: <30s
   - Batch/async: <5min

4. Do we need structured output schemas (JSON) for automated downstream processing?

---

*Last updated: 2026-05-25*
*Status: DRAFT — pending benchmark results from Linux GPU*