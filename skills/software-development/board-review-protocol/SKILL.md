---
name: board-review-protocol
category: software-development
description: Multi-model board review protocol for code quality gates — hallucination detection, structured verdicts, and review chain management. Updated 2026-06-02 with editorial review extension.
tags:
  - "board-review"
  - "quality-gate"
  - "multi-model"
  - "hallucination-detection"
  - "code-review"
  - "review-chain"
version: "1.1.0"
updated: "2026-06-02"
related_skills:
  - model-consulting
  - requesting-code-review
  - auto-trim-engine
  - editorial-review
references:
  - references/2026-06-02-board-review-session.md
  - references/2026-06-02-float-priority-edge-case.md
  - references/2026-06-02-claude-timeout-incident.md
  - references/2026-06-01-stewards-charge-review.md
---

# Board Review Protocol

Multi-model board review protocol for code quality gates. Used when merging
significant changes to critical files (auto-trim engine, model routing, gateway
config, any core infrastructure).

Also used for **editorial/narrative review** — see [Editorial Review Extension](#editorial-review-extension-new-2026-06-02) below.

## Why A Board, Not A Single Reviewer

Single-model reviews hallucinate confidently when they can't read the code.
A board of independent models cross-validates findings and surfaces fabrication
through disagreement.

## Review Chain (ordered by cost, ascending)

| Role | Model | Provider | Cost/mo | Strengths | Known Limits |
|------|-------|----------|---------|-----------|-------------|
| Primary reviewer | DeepSeek v4-flash | DeepSeek | Free | Fast, detailed formatting | **Cannot access files in some network configs → hallucinates.** Always verify honesty. |
| Honesty gate | Ring-2.6-1t | Custom/OpenRouter | ~$0.71 | Transparent about limitations, strong checklists | Less detailed than Claude |
| Creative analysis | Grok-4.20 | xAI | Variable | Sharp structural thinking | Inconsistent availability |
| Board member | Kimi K2.5 | Moonshot / Ollama Pro | — | Board voting member | Auth issues must be resolved, not worked around |
| Deep static analysis | Claude claude-sonnet-4-6 | Anthropic | — | Strongest static analysis | **Times out from Mac behind proxy/firewall (~90s)** |

## Fallback Chain

```
DeepSeek Flash (free) → Ring ($0.71/mo) → Grok → Local Qwen → Kimi
```

Budget: ~$166/200 remaining. DeepSeek Direct: $2.12 left.

## Workflow

### Phase 1 — Pre-Review

1. Ensure all existing tests are green (44/44 for auto-trim)
2. Prepare the review prompt:
   - Explicitly request file contents or paste them inline
   - Specify what you want reviewed (architecture, bugs, tests, naming)
   - Ask the model to **only report what it can verify from the actual code**
3. Generate `scripts/_board_reviews.json` with the prompt for each model

### Phase 2 — Execute Reviews (parallel)

Run all available board members against the same prompt simultaneously.
Each model gets the **actual file contents** — not descriptions, not summaries.

**Critical:** If a model says "I don't have filesystem access," do NOT accept
detailed findings from it. Those are hallucinated. Flag immediately.

### Phase 3 — Compile Findings

For each model, assess four dimensions:

| Dimension | Question | Red Flag |
|-----------|----------|----------|
| **Honesty** | Did it admit when it couldn't read the file? | Gives detailed findings but admits no access → fabrication |
| **Specificity** | Are findings tied to real line numbers and code? | Vague "line ~400" without actual content → hallucinated |
| **Novelty** | Are findings new, or already addressed? | "Found" bugs that were fixed in prior commits |
| **Actionability** | Can you implement a fix from the description? | "Consider improving X" with no concrete suggestion |

Template for compiled verdict:

```
### Model Name — [char count]
**Honest assessment:** [Fabricated / Honest-but-limited / Verified against code]

| # | Claimed Finding | Reality |
|---|----------------|---------|
| 1 | ... | Already fixed / Fabricated / Valid — new bug |
```

### Phase 4 — Verdict

- 🟢 **Water is clear**: No new actionable bugs. All flagged items already
  resolved or noted as future improvements.
- 🟡 **Flag for re-review**: Findings need investigation but aren't blocking.
- 🔴 **Block merge**: Critical or unvalidated findings require resolution.

### Phase 5 — Post-Review

1. Update the audit file: `scripts/AUTO_TRIM_AUDIT.md` (or relevant)
2. Commit `scripts/_board_reviews.json` with date stamp
3. Archive reference: `references/YYYY-MM-DD-board-review-session.md`
4. Move on. No ceremony.

## Anti-Patterns

### 🚨 Fabrication on No-Access (CRITICAL)

**Pattern:** Model says "I don't have filesystem access" then proceeds to list
detailed bugs with line numbers. The findings are entirely hallucinated.

**Detection:** The model cannot name specific variables, function signatures,
or control flow that would only be knowable from reading the code.

**Response:** Discard all findings from that model for this review. Note it in
the compiled verdict. Use a model that can actually read the file.

### 🚨 Description-Only Review

**Pattern:** Review is conducted against a description of the code (\"I was told
there's a function that does X\") rather than the actual code.

**Response:** Always provide file contents. If the model can't accept files,
paste the relevant code inline in the prompt.

### 🚨 Single-Model Trust

**Pattern:** Treating one model's review as authoritative without cross-validation.

**Response:** Minimum 2 models. Disagreement between models = investigate.
Agreement between models on a finding = high confidence.

### 🚨 Blocking on Unavailable Reviewer

**Pattern:** Waiting for Claude when it consistently times out from the current
network environment.

**Response:** Claude is the strongest static analyst but not mandatory. If it
times out, proceed with Ring + DeepSeek. Document the timeout. Re-run from a
different network if the review is for a critical merge.

### 🚨 Stale Review Chain

**Pattern:** Not updating the model chain when keys expire, models are removed,
or network conditions change.

**Response:** After each board review session, verify all models in the chain
actually responded. Update `model-consulting` SKILL.md if the chain changed.

## Operational Notes

### Claude Timeout (Mac Behind Proxy)

The Anthropic API consistently times out from this Mac after ~90s. Likely a
firewall/proxy issue. Workarounds:

1. Run the review from a different network
2. Use the Anthropic console directly for code paste
3. Proceed with Ring + DeepSeek (still high quality)
4. Fix the proxy/firewall config

### When to Trigger a Board Review

- Architecture changes (new pipeline, routing logic, signal handling)
- Core engine modifications (auto-trim, compression, priority logic)
- Security-sensitive changes (key management, auth, sandboxing)
- Any change where "just test it" isn't sufficient (non-deterministic outputs)
- Before major version bumps or deployments
- **Policy and strategy decisions** — enforcement strategy, process changes, threshold setting, model chain composition, routing rules. These produce a formatted board verdict with per-model reasoning, confidence scores, and an implementation directive. (see `references/2026-06-04-quality-gate-enforcement-review.md` for a complete worked example with 4-model unanimous approve)
- **Editorial/narrative review** of manuscripts, documents, or complex content

### When NOT to Trigger

- Documentation-only changes
- Config tweaks with no logic change
- Fixing a typo in a log message
- Changes already covered by existing test suite with 100% pass rate

---

## Editorial Review Extension (NEW 2026-06-02)

The board review protocol has been validated for **editorial/narrative review**
through application to the manuscript "The Steward's Charge." This extension
documents what was learned.

### Key Differences: Editorial vs Code Review

| Dimension | Code Review | Editorial Review |
|-----------|-------------|-----------------|
| Primary model | DeepSeek v4-flash | Claude (structure) + Kimi (voice) |
| Quality gate metric | Bug count, test pass rate | Narrative coherence, pacing, voice |
| Fabrication risk | Hallucinated API/functions | Hallucinated plot details, invented scenes |
| Context needs | File contents (exact) | Manuscript sections (chunks < 32K) |

### Editorial Board Composition

| Role | Model | Why |
|------|-------|-----|
| Structural logic | Claude Sonnet 4.6 | Plot coherence, timeline tracking, cause-effect |
| Aesthetic judgment | Kimi K2.5 | Voice, tone, reader experience, emotional resonance |
| Quality gate | Ring-2.6-1t | Holistic verdict, readiness scoring |
| Pattern detection | DeepSeek v4-flash | Fast forensic scan: AI markers, repetition, stats |
| Lateral synthesis | Grok-4.20-reasoning | Character analysis, thematic insight |

### Lessons Learned

1. **Local forensic extraction works** — textutil + Python identified structural
   issues (dup chapters, orphaned text, truncation) without model calls.
   Saves API budget and avoids hallucination risk.

2. **Kimi auth failures block creative assessment** — the 401 error meant no
   "aesthetic judgment" board member was available. **Must resolve before next
   editorial session.** Kimi is board member, not fallback.

3. **Claude timeout affects editorial work too** — the proxy/firewall issue that
   blocks code reviews also blocks narrative analysis. Need to resolve or
   substitute with DeepSeek v4-pro.

4. **Ring generalizes to editorial verdicts** — worked well for quality gate
   scoring on narrative coherence, not just code correctness.

5. **Quantitative character tracking is powerful** — counting character mentions
   revealed Iriniel's late introduction (zero until Ch 17) objectively.

6. **Word frequency analysis catches problems humans miss** — "pressure" at
   138 occurrences and "bow" at 125 references flagged as overuse that a
   human editor might not quantify.

7. **Hybrid format (LitRPG) needs special handling** — game-system embedded
   content requires a distinct review lens: is the data consistent? Is it
   disruptive to narrative flow? Should it be separated?

### Workflow Adaptation

For editorial reviews, the workflow proceeds:

1. **Forensic Extraction** (local) → word count, chapter map, character mentions, AI-pattern scan
2. **Structural Audit** (automated) → duplicate headers, orphaned text, numbering gaps, stat consistency
3. **Narrative Analysis** (model-assisted) → character arcs, plot coherence, pacing, voice
4. **Board Consult** (parallel multi-model) → distribute findings to models by strength
5. **Compiled Report** → tiered recommendations (must-fix / pre-publish / polish)