# Context Trimming Philosophy — Decision Record (2026-05-25)

## Question
Should the 8B model on Linux be used for "compressing" context (rephrasing/summarizing) or only for "cutting" (deleting worthless blocks)?

## Decision: Hybrid — Compression + Deletion, Not Either/Or

The user explicitly requested reexamination of this assumption. The answer is **both**, applied at different tiers:

### Tiers Using Compression (rephrase → `[COMPRESSED]` tag)
- **T5 (Tool Output):** Raw tool results are highly structured and redundant. Compression reduces 80%+ of token usage while preserving all actionable information.
- **T4 (Background Material):** Reference docs, prior context that's relevant but not active. Compress to extract only the facts needed.
- **T2 (Recent High-Importance):** Compress before dropping. If compression reduces below a threshold, drop the original and keep only the compressed summary.

### Tiers Using Deletion (pure drop)
- **T6 (Old Conversation):** By this point, information is already encoded in T1-T3 state. The raw turns are disposable.

### Tiers Never Trimmed
- **T0 (Identity):** Who we are, what we can do, operating principles. Immutable.
- **T1 (Active Task):** Current goal, sub-tasks, in-flight decisions. Compress only as last resort.

### T3 (Semantic Facts from Palace)
- Dedup-check against Memory Palace first.
- If the fact already exists in the Palace with higher importance, drop the context copy.
- If unique, compress and tag.

## Why Not Compression-Only?
- Compression costs tokens + compute (you pay for both input and output)
- Some content has near-zero information density (e.g., repeated greetings, boilerplate)
- Deletion is instant and free; compression is a model call

## Why Not Deletion-Only?
- Loses nuance and context that isn't captured in higher-tier summaries
- "Review this code" needs surrounding context that pure deletion would destroy
- Memory Palace isn't perfect — some contextual detail only lives in the window

## Metrics for Tuning
- **Token efficiency:** (useful tokens retained) / (total tokens before trim)
- **Task success rate:** % of tasks completed correctly post-trim vs pre-trim
- **Ring pass rate:** Quality gate pass rate as a proxy for information loss
- **Latency delta:** Time added by compression vs time saved by smaller context

## 8B Role Clarification
The Linux `qwen3:8b` is NOT the compression engine — it's the **long-context fallback** for when the Mac 14B runs out of budget. Compression will be done inline by the context orchestrator using Python string operations + optional LLM-based summarization (using the currently active model, not a dedicated compression model).

The 8B fits Linux RTX 3060 (12GB VRAM) with headroom for KV cache during context orchestrator operations.