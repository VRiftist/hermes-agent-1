---
name: ai-assisted-fiction-authoring
category: software-development
description: "Complete best-practices skill for fiction authors writing with AI assistance: story bible management, AI co-author patterns, multi-model board review workflows, manuscript refactoring with change tracking, LitRPG stat consistency verification, character voice preservation, and project filesystem organization. Builds on Steward's Charge production workflow."
version: "1.0.0"
updated: "2026-06-02"
author: Hermes Agent
license: MIT
tags:
  - fiction-writing
  - ai-authoring
  - story-bible
  - litrpg
  - board-review
  - manuscript-refactoring
  - character-voice
  - filesystem-organization
metadata:
  hermes:
    tags: [fiction-writing, ai-authoring, story-bible, litrpg, board-review, manuscript-refactoring, character-voice]
    related_skills:
      - editorial-review
      - editorial-review-pipeline
      - board-review-protocol
      - model-consulting
references:
  - AI-AS-CO-AUTHOR.md (in-skills references section)
  - editorial-review/references/2026-05-26-full-book-board-review.md
  - board-review-protocol/references/2026-06-02-board-review-session.md
  - editorial-review-pipeline/references/2026-05-26-stewards-charge-final-delivery.md
---

# AI-Assisted Fiction Authoring

Complete best practices for fiction authors writing with AI assistance. This skill covers the full workflow from story bible creation through manuscript delivery, based on production experience with a 126K-word LitRPG novel (The Steward's Charge) using a 4-model editorial board chain.

## When to Use This Skill

- Starting a new fiction project and setting up filesystem/story bible infrastructure
- Using AI as a developmental editor, continuity checker, or co-author
- Running a multi-model board review on a manuscript
- Refactoring a manuscript with change tracking and diff preservation
- Checking LitRPG/GameLit stat progression for consistency
- Preserving character voice across AI-assisted edits
- Organizing drafts, refactors, diffs, and reports for a book project

---

## 1. Story Bible / Lore Bible

### 1.1 What It Should Contain

A story bible is a single source of truth for narrative consistency. Store it as `01_STORY_BIBLE.md` at the project root.

#### Required Sections

| Section | Contents | Example Entry |
|---------|----------|--------------|
| **Characters** | Full name, aliases, age, physical description, personality, voice markers, arc summary, relationships, backstory | `Iriniel — Elven steward, 247 yrs, silver hair, formal speech pattern, arc: isolation → trust, voice: measured, authoritative, uses "one must" constructions` |
| **Timeline** | Chronological events, chapter-by-chapter, dates/ages at each point | `Ch 1: Auric arrives at Aethermire (Day 1). Ch 17: Iriniel introduced (Day 12). Total span ~3 weeks.` |
| **Magic System** | Rules, limits, costs, user categories, naming conventions, hierarchy | `Aether-weaving: costs stamina, not mana. Three tiers: Threading (basic), Weaving (intermediate), Shaping (master). No resurrection. No time reversal.` |
| **Geography** | Named locations, distances, travel times, climate, cultural notes | `Aethermire: northern coastal fortress, 3-day ride from Thornwall. Climate: cold, sea mists. Architecture: pale stone, silver filigree.` |
| **Factions** | Name, goal, leader, members, internal conflicts, relationships | `The Concord: mercantile guild controlling trade routes. Leader: Magister Vex. Suspicious of Aethermire. Alliance: none.` |
| **Glossary** | Terms, pronunciation, in-world definitions | `Aether — (AY-ther) — The ambient magical energy. Surge — temporary stat boost from aether exposure.` |
| **LitRPG System Spec** | Stat ranges, level thresholds, VXP curve, skill trees, formulas | `Level N requires N×100 VXP. Starting stats: STR 8, DEX 10, INT 14. Max level: 50.` |
| **Inconsistency Log** | Tracked bugs and their resolution status | `Ch 31 → Ch 40: Level 4 → Level 10 (missing 6 levels). RESOLVED: added intermediate stat snapshots at Ch 35, Ch 38.` |

### 1.2 How to Maintain Across Drafts

**Rule: Bible is a living document, updated BEFORE every draft pass.**

```
Before each refactoring session:
  1. Read current bible
  2. Note any intended changes for THIS pass
  3. After pass, update bible with actual changes
  4. Run consistency checks against updated bible
```

**Version tagging convention:**

```
01_STORY_BIBLE.md              — always the latest
ARCHIVE/01_STORY_BIBLE_v1.md   — pre-first-refactor
ARCHIVE/01_STORY_BIBLE_v2.md   — pre-second-refactor
```

Each bible version gets a changelog footer:

```markdown
## Changelog
| Date | Version | Changes |
|------|---------|---------|
| 2026-05-20 | v1 | Initial |
| 2026-05-22 | v2 | Added Iriniel backstory, corrected timeline (was 2 weeks, now 3) |
| 2026-05-26 | v3 | Added VXP formulas, resolved Level 4→10 gap with Ch 35/38 snapshots |
```

### 1.3 Version Control for Narrative Consistency

**Git-based approach (recommended for solo authors):**

```
book-project/
├── .git/
├── manuscript/
│   ├── 01_STORY_BIBLE.md          <-- tracked, updated per refactor pass
│   ├── CHANGELOG.md               <-- human-readable narrative change log
│   └── consistency-errors.log     <-- auto-generated by verification scripts
└── ...
```

**Commit discipline:**

```
feat(story-bible): add Iriniel backstory section
fix(story-bible): correct timeline from 2 weeks to 3
refactor(story-bible): standardize faction entries
docs(story-bible): add VXP formula reference
```

**Consistency check prompt (run before every commit that touches the manuscript):**

```
You are a continuity checker. I will give you a story bible entry and a manuscript
passage. Report ONLY facts that contradict the bible. Do NOT suggest improvements.
Do NOT praise the writing. Do NOT list facts that match.

BIBLE ENTRY:
<clip from 01_STORY_BIBLE.md>

MANUSCRIPT PASSAGE:
<clip from manuscript.txt>

Format:
CONTRADICTION: <fact> — BIBLE says <X>, MANUSCRIPT says <Y>
LOCATION: Chapter N, paragraph M
CONFIDENCE: HIGH / MEDIUM / LOW (HIGH if explicit conflict, MEDIUM if implied)
```

**Verification checklist after each draft pass:**

- [ ] Story bible version bumped (v1→v2, etc.)
- [ ] Archive copy of pre-refactor bible saved to ARCHIVE/
- [ ] Changlog footer updated with what changed and why
- [ ] Git commit with standard prefix `feat(story-bible):` or `fix(story-bible):`
- [ ] Consistency check run on every manuscript chapter touched
- [ ] No contradictions of HIGH or MEDIUM confidence remain unresolved

---

## 2. AI-as-Co-Author Best Practices

### 2.1 Editorial vs Creative Generation — Two Distinct Prompt Modes

**MODE A: Editorial Prompt (analysis, critique, suggestions)**

```
System: You are a developmental editor. Analyze the following passage for <specific
focus>. Do NOT rewrite. Do NOT generate new content. Identify issues with
evidence from the text, not opinion.

Focus: <pacing / continuity / character voice / dialogue quality / showing vs telling>

Rules:
- Every claim must reference a specific line or paragraph
- If you cannot find a specific example for a claim, exclude that claim
- Rate severity: CRITICAL / MODERATE / MINOR
- Format: [SEVERITY] [LOCATION] [ISSUE] → [SUGGESTION]
```

**MODE B: Creative Generation Prompt (new content, prose)**

```
System: You are a creative writing assistant. Generate prose in the author's
voice. Key constraints:
1. NO em dashes — use commas or periods instead
2. NO transition words: however, moreover, nevertheless, furthermore
3. NO adverb-tagged dialogue: "he said angrily" → show anger through action
4. MAXIMUM ONE adjective per noun phrase
5. Sentences under 25 words on average
6. Avoid: "not only...but also", "it was as if", "somehow", "somewhat"
7. Match vocabulary level to the author's existing prose (check 3 sample paragraphs)
8. Match character voice exactly — if a character speaks formally, do NOT make them casual

SAMPLE VOICE:
<3 paragraphs of author's prose to match>
```

### 2.2 Avoiding AI-isms in Prose

**Known AI markers (ban these entirely):**

| AI Marker | Why It's A Problem | Replace With |
|-----------|-------------------|--------------|
| Em dashes (—) | AI overuses them as dramatic pauses | Periods, commas, or line breaks |
| "However" at sentence start | Corporate/proofreading tone | "But" or restructure |
| "Moreover / Furthermore / Nevertheless" | Academic boilerplate | Omit or use "Still" / "Yet" |
| "Not only...but also" | Forced parallelism, AI tell | Simple conjunction |
| "It was as if" | Telling, not showing | Direct description |
| "Somehow / Somewhat / Slightly" | Hedge words that weaken prose | Remove or replace with concrete detail |
| "He said angrily / she replied coldly" | Adverb-tagged dialogue (telling) | Show through action: "He slammed the mug down." |
| "Ethereal / Luminous / Whispered / Pristine" | AI default vocabulary | Pull from author's word frequency list |
| "Couldn't help but" | Passive construction | Direct action: "He laughed." not "He couldn't help but laugh." |
| "In a world where" | Cliché opener | Start in media res |

**Post-generation AI-ism scan prompt:**

```
Scan this text for AI writing markers. Report every occurrence with:
LINE: <line>
OFFENSE: <marker type>
FIX: <proposed replacement>

Text:
<passage>
```

### 2.3 Maintaining Author Voice

**Voice fingerprint extraction (run once per author/project):**

```
Analyze these 5 representative passages from the author. Extract a "voice
fingerprint" with:

1. Average sentence length (words)
2. Most common sentence start patterns (preposition, subject-verb, dialogue tag?)
3. Vocabulary tier (simple ~80%, moderate ~15%, advanced ~5%)
4. Dialogue attribution style (said/asked only, or varied)
5. Favorite rhetorical devices (parallelism, fragments, rhetorical questions)
6. Unusual word choices (words the author favors that most writers don't)
7. What the author NEVER does (e.g., no em dashes, no chapter epigraphs)

Return exactly this format so it can be pasted into every generation prompt.
```

**Voice consistency verification prompt:**

```
Below is character dialogue from this manuscript followed by AI-generated
dialogue in the same scene. Compare them. Does the AI dialogue match the
character's established vocabulary, sentence structure, and emotional register?

CHARACTER: <name>
ESTABLISHED VOICE: <voice fingerprint snippet>

ORIGINAL:
<3 lines of original dialogue>

AI-GENERATED:
<3 lines of AI dialogue>

VERDICT: MATCH / MINOR DRIFT (<sentence>) / MAJOR DRIFT (<sentence>)
If MAJOR DRIFT: Reject and regenerate with emphasis on <specific drift issue>.
```

### 2.4 Developmental Editing Use Cases

| Use Case | Prompt Pattern | Expected Output |
|----------|---------------|-----------------|
| **Pacing analysis** | "Track the event-density per chapter. Flag chapters where <1 or >5 major events occur. Identify the midpoint lull." | Chapter-by-chapter event count, flagged slow/dense chapters, suggested cuts or additions |
| **Dialogue quality** | "Rate each dialogue exchange on: (a) Does it advance plot? (b) Does it reveal character? (c) Is the voice distinct? Flag exchanges that are purely expository." | Exchanges tagged with scores, expository lumps flagged for rewrite |
| **Showing vs telling** | "Identify every instance of author telling the reader an emotion rather than showing it through action, dialogue, or sensory detail." | Line-by-line list of telling offenses with fix suggestions |
| **Continuity check** | "Check these 3 chapters for timeline consistency: character ages, time of day, season, travel distance feasibility." | Timeline contradictions mapped with chapter coordinates |
| **Word/phrase overuse** | "Count and list every occurrence of: <word>. If any word exceeds 0.5% of total words, flag as overuse." | Frequency table with flags |

### 2.5 Verification Checklist for AI-Co-Author Sessions

- [ ] Prompt mode is correct: EDITORIAL (analysis only) vs CREATIVE (generate prose)
- [ ] Voice fingerprint included in creative prompts
- [ ] AI-ism ban list enforced (post-generation scan)
- [ ] Original text preserved alongside AI-generated text (no blind replacement)
- [ ] Human-in-the-loop: all AI-generated additions reviewed by author before merge
- [ ] Character voice verification run on every AI-edited dialogue passage
- [ ] No "however/moreover/nevertheless" survive in final output
- [ ] No em dashes in final output (unless author's established style uses them)

---

## 3. Board Review Workflow

### 3.1 Board Composition (Validated on The Steward's Charge)

The board review chain is ordered **editorial → aesthetic → creative → quality gate**.
Each model sees the same manuscript but is prompted from its role's perspective.

| Order | Role | Model | Prompt Focus | Context Needed |
|-------|------|-------|-------------|----------------|
| 1 | Editorial/Structural | Claude Sonnet 4-6 | Plot coherence, timeline, character arcs, cause-effect logic | Full manuscript (200K ctx) |
| 2 | Aesthetic/Judgment | Kimi K2 | Voice, tone, reader experience, emotional resonance | Full ms via two-pass (128K ctx) |
| 3 | Creative/Lateral | Grok 4.3 | Character analysis, thematic threads, design feedback | Full manuscript (1M ctx) |
| 4 | Quality Gate (LAST) | Ring 2.6-1T | Holistic verdict, readiness scoring, regression check | Full manuscript (1M ctx) |

**Fallback chain when a model is unavailable:**

```
Claude (timeout) → DeepSeek v4 Flash (editorial)
Kimi (401 auth) → skip aesthetic, note in report
Grok (unavailable) → skip creative, note in report
Ring (OpenRouter down) → Agent Fallback (synthesize from all responses)
```

### 3.2 Structured Prompts for Each Board Role

**Prompt template — Editorial/Structural (Claude Sonnet):**

```
You are the lead developmental editor. Review the following manuscript.
Be rigorous and specific. Reference chapter numbers and paragraph ranges.

EVALUATE:
1. Plot coherence — does cause A lead to effect B without logical gaps?
2. Timeline integrity — are dates, ages, travel times consistent?
3. Character arcs — does each named character have a beginning, middle, and end?
4. Structural issues — pacing problems, redundant scenes, missing transitions
5. Thematic coherence — do sub-themes resolve or persist meaningfully?

SCORE: 0.0–10.0

FORMAT:
### Strengths (max 3, bullet)
- ...

### Issues (prioritized)
CRITICAL: <chapter, paragraph> — <issue> — <suggested fix>
HIGH: ...
MODERATE: ...

### Score & Rationale
Score: X.X/10
Rationale: 2-3 sentence summary.

### Action Items
Numbered list of specific, actionable recommendations.
```

**Prompt template — Aesthetic/Judgment (Kimi K2):**

```
You are an aesthetic/literary critic. Read this manuscript and assess:

1. Voice consistency — does the narration maintain a consistent register throughout?
2. Reader experience — where does engagement peak? Where does it flag?
3. Emotional stakes — are the consequences clear and felt?
4. Prose quality — is the sentence craft effective? Varied? Natural?
5. Dialogue authenticity — do characters sound like real (or in-world) people?

SCORE: 0.0–10.0

IMPORTANT: This is a LitRPG novel. Game stats and system blocks are genre
conventions, not flaws. Assess them on integration quality, not presence.

FORMAT:
### Voice Assessment
- Consistent register: YES/NO (if NO, cite chapters)
- Sentence variety: GOOD / ADEQUATE / REPETITIVE

### Reader Experience
- Engagement peaks: <chapters>
- Lulls: <chapters>
- Emotional high points: <chapters>

### Score: X.X/10
```

**Prompt template — Creative/Lateral (Grok 4.3):**

```
You are a creative editor with strong lateral thinking. Read this manuscript
and focus on:

1. Character depth — which characters feel three-dimensional? Which feel like
   archetypes? What one change would fix the flattest character?
2. Thematic threads — what themes are established but not resolved?
3. Narrative innovation — where could the story subvert reader expectations?
4. Sequel setup — are there natural hooks for Book 2 that feel organic?
5. Worldbuilding — what feels lived-in vs what feels explained?

Do NOT repeat structural or prose-level feedback (Claude and Kimi handle that).
Focus on high-level creative potential.

SCORE: 0.0–10.0

FORMAT:
### Creative Opportunities (prioritized)
1. <opportunity> — <chapter> — <why it matters>
2. ...

### Thematic Analysis
- Established themes: <list>
- Resolved: <list>
- Unresolved (pitched for Book 2): <list>

### Score: X.X/10
```

**Prompt template — Quality Gate (Ring 2.6-1T, MUST be last):**

```
You are the quality gate. You have read this manuscript AND the reviews from
the editorial, aesthetic, and creative reviewers below.

BOARD FINDINGS:
<paste Claude's review>
<paste Kimi's review>
<paste Grok's review>

Your job is to produce the FINAL VERDICT. Synthesize the board's findings,
resolve disagreements, and assess overall readiness.

ASSESS:
1. Regression risk — if we apply these recommendations, what could break?
2. Readiness — is this manuscript ready for: (a) immediate publication,
   (b) one more revision pass, or (c) significant restructuring?
3. Critical flags — are any issues blockers, or are they all polish/optional?
4. Creative risk — are we editing the author's voice into blandness?

FORMAT:
### Final Verdict: PASS / CONDITIONAL-APPROVE / REVISION-REQUIRED

### Readiness Score: X.X/10

### Synthesis
- Points of agreement across board: <bullets>
- Disagreements and resolution recommendation: <bullets>
- Board confidence: HIGH / MEDIUM / LOW

### Critical Flags (must fix before next pass)
1. ...

### Recommendations Accepted / Rejected
| Rec # | Board Member | Recommendation | Verdict | Rationale |
|-------|-------------|----------------|---------|-----------|
| 1 | Claude | ... | ACCEPT | ... |
```

### 3.3 When to Consult vs When to Merge

| Situation | Action |
|-----------|--------|
| All 4 models agree on a finding | MERGE — high confidence, apply immediately |
| 3 of 4 agree, 1 dissents | MERGE — document the dissent but proceed |
| 2 agree, 2 disagree | CONSULT — run a second pass targeting only the disputed issue |
| 1 strong, 3 silent/agnostic | CONSULT — the strong finding may be valid but needs verification |
| All disagree or all are vague | REJECT — the finding is not actionable |
| Quality gate (Ring) gives FAIL | BLOCK — do not merge until resolved and re-reviewed |

### 3.4 Board Review Session Record Keeping

After each session, archive to:
```
references/YYYY-MM-DD-board-review-<project>.md
```

Template:
```markdown
# Board Review Session — <DATE>
## Project: <BOOK TITLE>
## Chain: <Model A (editorial) → Model B (aesthetic) → Model C (creative) → Model D (gate)>

### Models Used
| Role | Model | Score | Available? |
|------|-------|-------|-----------|
| Editorial | Claude Sonnet 4-6 | 7.2/10 | ✅/❌ |

### Compiled Verdict
<Ring's final verdict>

### Action Items Applied
| # | Rec | Source | Status |
|---|-----|--------|--------|

### Regressions
None / <list regressions if any>
```

### 3.5 Verification Checklist for Board Reviews

- [ ] Chain ordering correct: editorial → aesthetic → creative → quality gate (LAST)
- [ ] Each model gets actual manuscript text, not summaries
- [ ] Context limits respected (128K for Kimi → two-pass; 200K for Claude)
- [ ] Ring/Kimi/DeepSeek all get full 1M ctx pass where available
- [ ] Dual-pass pattern used for Kimi at 128K margin (Part 1 → synopsis → Part 2 + synopsis)
- [ ] Quality gate (Ring) is LAST in sequence
- [ ] Fallbacks documented when primary model unavailable
- [ ] Session archive saved to references/YYYY-MM-DD-board-review-<project>.md
- [ ] OpenRouter key issue: run Ring inline (not via subagent) if keys don't propagate
- [ ] Agent Fallback verdict explicitly noted if Ring unavailable
- [ ] No fabricated model quotes — live API calls only

---

## 4. Manuscript Refactoring Workflows

### 4.0 Output Packaging & Delivery (Added 2026-06-01)

**Assemble a final output folder for every author delivery** using the `~/Documents/<Project>_Output/` convention.

Required contents:

| File | Purpose |
|------|---------|
| `manuscript_refactored.txt` | Final manuscript (the deliverable text) |
| `manuscript_original.txt` | Untouched original for comparison |
| `final_diff.txt` | Unified diff (506+ lines) with original line numbers |
| `vxp_verification_report.txt` | Independent stat-chain coherence audit |
| `build_refactored_manuscript.py` | Build script for reproducibility |
| `REVIEW_STEWARDS_CHARGE_BOOK1.md` | Full board review verbatim |
| `EDITORIAL_REPORT_2_Stewards_Charge.md` | Applied editorial report with change log |
| `EDITORIAL_REVIEW_PACKAGE_Stewards_Charge.md` | Author-facing package with prioritized actions |
| `2026-06-01-stewards-charge-review.md` | Board review applied — model notes & forensic results |
| `README.md` | Package index with verdict, summary, open items, next steps |

Also generate a `.docx` package (see `editorial-review-pipeline` skill) when python-docx/lxml are available.

**For inline diff display** (authors who prefer seeing changes in context): include the `<` / `>` diff lines in the report appendix or README alongside the standalone diff file.

### 4.1 Change Tracking (Diff-Based)

**Always generate a unified diff between original and refactored manuscript.**

```bash
# After refactoring
diff -u manuscript_original.txt manuscript_refactored.txt > refactor_diff.txt
```

**Diff naming convention:**
```
refactor_v1_diff.txt          — first refactoring pass
refactor_v2_diff.txt          — second refactoring pass
final_diff.txt                — final diff for delivery
```

**Always preserve EVERY version:**
```
manuscript_original.txt       — untouched original
manuscript_v1.txt             — after first refactor
manuscript_v2.txt             — after second refactor
manuscript_final.txt          — delivery version
```

### 4.2 Change Log Formats

#### Option A: Log + Appendix (Recommended for author delivery)

**Structure:** Summary table at front, full addition text in appendix.

```
# Change Log

## Summary
| ID | Location | Type | Reason | Verdict |
|----|----------|------|--------|---------|
| C1 | Ch 4, after para 12 | Addition (~200 words) | Expand Iriniel's backstory | ✅ Verified |
| C2 | Ch 8-16 | Trim (~15-20%) | Middle-third pacing | ✅ Applied |
| C3 | Ch 21, para 5-8 | Rewrite | Fix VXP continuity | ✅ Original stats preserved |
| C4 | Ch 34, end | Addition (~1,000 words) | Plant sequel seed | ✅ Voice-matched |
| C4-echo | Ch 53, before final stat block | Addition (~200 words) | Close foreshadowing loop | ✅ New |

## Appendix: Full Addition Text
### Addition C1 — Ch 4 (Iriniel backstory expansion)
<full text of the addition>

### Addition C4 — Ch 34 (Fracturing seed)
<full text of the addition>
```

#### Option B: Inline Markup (Recommended for internal editing)

Mark changes directly in the manuscript file with tags:

```
[— Ch 12 Original —]
He walked quickly through the market.
[— Ch 12 Refactored —]
He shouldered through the market crowd, past a fruit stall, past a woman
selling ribbons. [TRIMMED: ~20 words. Pace tightened]
[— End Ch 12 —]

[— Ch 34 Addition C4 —]
<new content here>
[/ADDITION C4]
```

### 4.3 Change ID Convention

| Prefix | Meaning | Example |
|--------|---------|---------|
| `A` | Structural edit (reorder, relocate) | `A1: Moved Ch 42 bonus scene to appendix` |
| `B` | Pacing edit (trim, condense) | `B2: Trimmed Ch 8 travel sequence ~250 words` |
| `C` | Addition (new content) | `C3: Added Iriniel backstory ~500 words` |
| `D` | Line-level edit (style, grammar) | `D4: Fixed tense inconsistency para 3` |
| `E` | Stat/LitRPG correction | `E5: Corrected VXP 145→150 in Ch 31 stat block` |

### 4.4 Refactoring Prompt Template (for Claude Sonnet)

```
You are performing a controlled manuscript refactoring. Follow these rules exactly.

## CRITICAL RULES
1. PRESERVE author voice — no AI-isms (no em dashes, no "however/moreover/nevertheless",
   no "not only...but also", no adverb-tagged dialogue)
2. EDIT and MOVE — do NOT rewrite unless absolutely necessary
3. Preserve ALL economic content, ALL character voice signatures
4. Preserve LitRPG elements (stats, skill trees, attribute blocks)
5. Only rewrite or add if the board has specifically recommended it

## WHAT NOT TO CHANGE
<list elements with unanimous positive board feedback>

## RECOMMENDATIONS (from board)
### A — Structural Edits
### B — Pacing Edits
### C — Additions
### D — Line-Level Edits
### E — Content Preservation (read only, do not touch)

## OUTPUT FORMAT
Use marking tags:
- [MOVED FROM Ch X] — content relocated from another chapter
- [ADDED: C2] — new content, tagged with change ID
- [TRIMMED: ~N words] — content removed or condensed
- No other markup in the body

## MANUSCRIPT TO REFACTOR
<paste full manuscript>
```

### 4.5 Verification Checklist for Refactoring

- [ ] Original manuscript preserved (manuscript_original.txt)
- [ ] Refactored version saved separately (manuscript_v1.txt)
- [ ] Unified diff generated (refactor_v1_diff.txt)
- [ ] Change log created (Option A or B)
- [ ] Every change ID referenced in diff corresponds to an entry in change log
- [ ] No AI-isms in new/generated text (run AI-ism scan)
- [ ] Character voice verified on all edited dialogue
- [ ] Stat chain re-verified if any stat blocks were touched
- [ ] Diff statistics recorded (+/- line counts)

---

## 5. VXP/Stat/Level Progression Tracking (LitRPG/GameLit)

### 5.1 The Stat Chain Problem

LitRPG novels embed game-system data (VXP, levels, attribute points) within the narrative. The most common bug is **stat regression**: a character at Level 4 in Chapter 31 reaches Level 10 by Chapter 40 with only enough earned VXP for 2 levels.

### 5.2 Mathematical Verification Protocol

**Step 1: Extract all stat snapshots from the manuscript.**

```
Scan the manuscript for stat blocks. Each block contains:
- Chapter number
- Character name
- Level
- Current VXP / VXP to next level
- Any attribute points (STR, DEX, INT, etc.)

Output as CSV for verification:
Chapter, Level, VXP_Current, VXP_Next, VXP_Earned_This_Chapter, Notes
```

**Step 2: Trace the progression chain.**

```
From the extracted stats:
- Verify that Level N+1 requires ΔVXP = N × 100 (or whatever the system formula is)
- Sum all VXP earned across chapters between stat snapshots
- Verify: VXP_earned = VXP_next_snapshot - VXP_current_snapshot
- Flag any negative VXP (stat regression) or impossible jumps
```

**Step 3: Report format.**

```
## VXP Chain Verification Report

System Formula: Level N requires N×100 VXP from previous level

| Chapter | Level | VXP | Expected VXP | Δ Status |
|---------|-------|-----|-------------|----------|
| 1       | 1     | 0/100 | — | ✅ Baseline |
| 12      | 2     | 50/200 | 0–100 | ✅ |
| 23      | 3     | 180/300 | 200 | ✅ |
| 31      | 4     | 145/400 | 300 | ❌ GAP: 145 vs 400—only earned 145 VXP total (missing 255) |
| 40      | 10    | — | — | ❌ LEVEL JUMP: 4→10 with no intermediate snapshots |

RESOLUTION:
- Issue at Ch 31: Correct 145/400 to 150/400 (synchronization with Ch 12-23 earning)
- Issue at Ch 31→40: Add stat snapshots at Ch 35 (Level 6) and Ch 38 (Level 8)
- Post-fix re-verify full chain
```

### 5.3 VXP Verification Prompt

```
Act as a LitRPG system auditor. Below is the extracted stat chain from a manuscript.

SYSTEM FORMULA: Level N requires N×100 VXP to advance from Level N-1.
Starting Level: 1. Starting VXP: 0.

STAT CHAIN:
<CSV of extracted stat blocks>

TASKS:
1. Trace the full progression chain from start to end
2. Identify every gap where earned VXP doesn't match required VXP
3. Identify every level jump with no intermediate stat snapshot
4. Calculate the correction needed for each gap
5. Report regressions (negative VXP progress)

OUTPUT FORMAT:
### Chain Trace
| Step | Ch | Level | VXP | Expected Δ | Actual Δ | Status |
|------|----|-------|-----|-----------|---------|--------|

### Gap Analysis
<list of every discontinuity>

### Proposed Corrections
<specific, chapter-level fixes>

### Post-Correction Chain
<what the chain will look like after fixes>
```

### 5.4 Stat Snapshot Placement Rules

1. **Minimum frequency**: Every 5 chapters or every major level-up, whichever comes first
2. **Position**: End of chapter, after action resolves, before transition to next scene
3. **Novel end**: Final stat block should NOT be the last page — place 1–2 paragraphs before "End of Book"
4. **Copy-paste protection**: Every stat snapshot addition is susceptible to copy-paste errors. Always re-verify the full chain after insertion, not just the snapshot you inserted.

### 5.5 Verification Checklist for LitRPG Stats

- [ ] All stat snapshots extracted into CSV
- [ ] Chain traced from Chapter 1 to end
- [ ] Every level jump has at least one intermediate snapshot (rule: max 2 levels per gap)
- [ ] No negative VXP (regression) at any point in the chain
- [ ] End-of-book final stat block not on last page
- [ ] Formula verified: Level N → N+1 requires correct ΔVXP per system rules
- [ ] DeepSeek v4 Flash coherence check run on the full chain (independent verification)
- [ ] Corrections applied, chain re-verified

---

## 6. Character Voice Preservation

### 6.1 Building a Character Voice Profile

For every named character with dialogue, create a voice profile in the story bible:

```yaml
Character: Iriniel
Voice Profile:
  - Register: Formal, measured, authoritative
  - Sentence structure: Compound-complex, periodic sentences
  - Vocabulary: Elevated but not archaic ("one must consider" not "thou must")
  - Speech patterns: Uses rhetorical questions, avoids contractions in formal settings
  - Emotion tells: Stiffens posture when angry, touches silver necklace when anxious
  - Dialogue tags: Prefers action-based ("Iriniel set down her cup.") over adverbs
  - What they DON'T say: Slang, profanity, casual idioms
  - Internal monologue: Strategic, calculating, rarely emotional
```

**Voice profile extraction prompt:**

```
From the following 5 dialogue passages of this character, extract a voice profile.
Include: sentence length range, favored constructions, vocabulary tier,
emotional tells (how they show vs tell emotion), what they never say.

Character name: <name>
Passages:
<5 dialogue passages>

Return a structured voice profile suitable for pasting into a story bible.
```

### 6.2 Pre/Post-Edit Voice Comparison

**Before accepting any AI edit that touches character dialogue, run this check:**

```
CHARACTER: <name>
VOICE PROFILE: <from story bible>

ORIGINAL DIALOGUE (author-written):
<excerpt>

EDITED DIALOGUE (AI-modified):
<excerpt>

COMPARE on these dimensions:
1. Vocabulary register — does the word tier match?
2. Sentence structure — same rhythm and complexity?
3. Characteristic phrases — are the character's verbal tics preserved?
4. Emotion register — would this character react this way?
5. Internal consistency — does this match how they spoke in Chapter X?

For each dimension: MATCH / MINOR DRIFT / MAJOR DRIFT
If MAJOR DRIFT on any dimension: REJECT the edit
If MINOR DRIFT on 2+ dimensions: REJECT the edit
```

### 6.3 Bulk Dialogue Consistency Scan

For a full-manuscript scan:

```
Extract every line of dialogue from this manuscript, grouped by character.
For each character:
1. Count total lines of dialogue
2. Identify the most common sentence start word
3. Identify the most common word (excluding articles/prepositions)
4. Calculate average words per utterance
5. Find any utterances that use vocabulary outside the character's established tier

Report any character whose dialogue pattern shifts significantly (>20% variance)
between chapters or between original and AI-edited sections.
```

### 6.4 Handling Internal Monologue

Internal monologue is the most fragile voice element — it's where character identity lives. Rules:

1. **Never rewrite internal monologue.** Edit for grammar only.
2. **Never add internal monologue that wasn't there.** If the board recommends more interiority, the author writes it.
3. **Tag internal monologue sections before sending to AI** so the edit model knows which sections are untouchable:

```
[INTERNAL — DO NOT EDIT]
He thought about the aether, about the weight of the steward's charge.
He had not asked for this. He had never asked for anything.
[END INTERNAL — RESUME EDITABLE NARRATIVE]
```

### 6.5 Verification Checklist for Character Voice

- [ ] Every speaking character has a voice profile in the story bible
- [ ] AI edits touching dialogue pass pre/post voice comparison
- [ ] No internal monologue was rewritten by AI
- [ ] No character voice drift between original and AI-edited sections
- [ ] First 3 chapters' dialogue checked for baseline against later chapters
- [ ] Bulk dialogue consistency scan run (no >20% variance per character)

---

## 7. Tools and Filesystem Organization

### 7.1 Recommended Directory Structure

```
book-project/
│
├── 01_STORY_BIBLE.md              # Single source of truth (always latest)
├── 02_PHASE_PLAN.md               # Overall writing/editing plan with phases
├── CHANGELOG.md                   # Narrative change log (human-readable)
├── consistency-errors.log         # Auto-generated verification output
│
├── manuscript/                    # All manuscript versions
│   ├── manuscript_original.txt    # UNTOUCHED original
│   ├── manuscript_v1.txt          # After refactor pass 1
│   ├── manuscript_v2.txt          # After refactor pass 2
│   └── manuscript_final.txt       # Delivery version
│
├── drafts/                        # Author's draft versions
│   ├── 001_first_draft.txt
│   ├── 002_self_edit_pass.txt
│   └── 003_beta_readers.txt
│
├── refactors/                     # Refactoring artifacts
│   ├── refactor_v1_diff.txt       # Unified diff
│   └── refactor_v2_diff.txt       # Unified diff
│
├── reports/                       # Editorial board reports
│   ├── 001_initial_review.docx
│   ├── 002_board_review.docx
│   └── 003_final_delivery.docx
│
├── prompts/                       # Prompts used for each session
│   ├── refactoring_prompt_v1.md
│   ├── board_review_prompt.md
│   └── consistency_check_prompt.md
│
├── verification/                  # Verification outputs
│   ├── vxp_chain_audit.txt
│   ├── voice_consistency_report.txt
│   ├── ai_marker_scan.txt
│   └── word_frequency_report.txt
│
├── bible_archive/                 # Versioned story bibles
│   ├── 01_STORY_BIBLE_v1.md
│   └── 01_STORY_BIBLE_v2.md
│
├── references/                    # Session archives
│   └── 2026-05-26-board-review-stewards-charge.md
│
├── templates/                     # Reusable prompt templates
│   ├── refactoring-prompt.md
│   ├── voice-profile-extraction.md
│   └── continuity-check.md
│
└── scripts/                       # Automation
    ├── extract_stats.py           # Extract LitRPG stat blocks
    ├── voice_scan.py              # Bulk dialogue consistency
    └── ai_marker_detect.py        # AI-ism scanner
```

### 7.2 Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Manuscript files | `manuscript_<version>.txt` | `manuscript_v2.txt` |
| Diff files | `refactor_v<N>_diff.txt` | `refactor_v2_diff.txt` |
|| Reports | `<NNN>_<type>_<book>.docx` | `002_board_review_project_x.docx` |
| Prompts | `<type>_prompt_v<N>.md` | `refactoring_prompt_v2.md` |
| Verification outputs | `<topic>_report.txt` | `vxp_chain_audit.txt` |
| Bible versions | `01_STORY_BIBLE_v<N>.md` | `01_STORY_BIBLE_v3.md` |
| Session archives | `YYYY-MM-DD-<event>-<project>.md` | `2026-05-26-board-review-stewards-charge.md` |

### 7.3 File Size and Format Rules

| File | Format | Encoding | Max Size | Notes |
|------|--------|----------|---------|-------|
| Manuscript | Plain text (.txt) | UTF-8 | No limit | NO markdown in manuscript body |
| Story bible | Markdown (.md) | UTF-8 | No limit | Uses markdown headers and tables |
| Diff | Plain text (.txt) | UTF-8 | No limit | Output of `diff -u` |
| Reports | Word (.docx) | — | Reasonable | python-docx generated |
| Verification | Plain text (.txt) | UTF-8 | No limit | Auto-generated, append-only |

### 7.4 Key Commands Reference

```bash
# Extract manuscript from DOCX
textutil -convert txt manuscript.docx -output manuscript/manuscript_original.txt

# Word count
wc -w manuscript/manuscript_original.txt

# Generate unified diff
diff -u manuscript/manuscript_original.txt manuscript/manuscript_v1.txt > refactors/refactor_v1_diff.txt

# Diff statistics
diffstat refactors/refactor_v1_diff.txt

# Character count (for token estimation)
wc -c manuscript/manuscript_original.txt

# Chapter map (grep chapter headers)
grep -n "^Chapter\|^CHAPTER\|^Ch " manuscript/manuscript_original.txt
```

### 7.5 Token Estimation Quick Reference

```
Word count × 1.3 ≈ token count (tight prose, mostly dialogue)
Word count × 1.5 ≈ token count (descriptive prose, LitRPG stat blocks)

Models and their context limits:
- DeepSeek v4 Flash: 1,000,000 tokens
- Ring 2.6-1T: 1,000,000 tokens
- Grok 4.3: 1,000,000 tokens
- Claude Sonnet 4-6: 200,000 tokens
- Kimi K2: 128,000 tokens (requires two-pass if > 128K)
```

### 7.6 Verification Checklist for Filesystem Setup

- [ ] Project root directory created
- [ ] All subdirectories exist: manuscript/, drafts/, refactors/, reports/, prompts/, verification/, bible_archive/, references/, templates/, scripts/
- [ ] Story bible created at 01_STORY_BIBLE.md
- [ ] Original manuscript saved to manuscript/manuscript_original.txt
- [ ] .gitignore set up (if using git): ignore *.docx, node_modules/, __pycache__/
- [ ] Git initialized: `git init && git add -A && git commit -m "feat(project): initial book project setup"`
- [ ] Token estimate calculated and noted for model routing decisions

---

## Common Pitfalls

1. **Letting AI rewrite instead of edit.** The author's voice is the product. AI should suggest, the author should decide. Every AI-generated sentence should be reviewed by a human before entering the manuscript.

2. **Stat corrections without full chain re-verification.** Copy-paste errors in stat snapshot additions are the #1 LitRPG bug. Always re-run the full VXP chain after inserting a single correction.

3. **Board review without change log.** If you get feedback but don't track what changed, you can't verify anything. Always produce both diff and change log.

4. **No voice profile before AI editing.** If you don't know the character's voice baseline, you can't detect drift. Extract voice profiles before any AI-assisted editing session.

5. **Treating story bible as static.** The bible is a living document. Update it before every refactoring pass, not after.

6. **DOCX extraction artifacts treated as manuscript issues.** textutil DOCX→TXT conversion can introduce duplicate headers, orphaned text, truncation. Always verify structural findings against the clean .txt file before reporting them.

7. **Mid-chapter splits for context-limited models.** When splitting a manuscript for Kimi K2's 128K limit, always split at a chapter boundary. Mid-chapter splits destroy context.

8. **Underestimating token counts.** If using word_count × 1.3, a 126K-word manuscript ≈ 164K tokens. That fits DeepSeek (1M) but not Kimi K2 (128K). Estimate before choosing models.

9. **OpenRouter keys don't propagate to subagents.** When using `delegate_task` for board reviews, OpenRouter keys are NOT in the subagent environment. Run Ring inline or fall back to Agent Fallback.

10. **Over-iteration.** Each refactoring pass should make targeted improvements. Stop when the only remaining criticism is about already-protected elements (author voice, economic content, genre conventions). Don't flatten the book into blandness.

---

## Verification Checklist (Full Project)

- [ ] Story bible exists and is versioned
- [ ] Original manuscript preserved read-only
- [ ] All refactored versions preserved with version tags
- [ ] Unified diffs generated for every refactoring pass
- [ ] Change log (Option A or B) accompanies every refactoring pass
- [ ] Board review chain ordering: editorial → aesthetic → creative → quality gate (LAST)
- [ ] Every model's response archived with session reference
- [ ] VXP/stat chain verified mathematically (no regressions, no unexplained jumps)
- [ ] Character voice profiles exist for all speaking characters
- [ ] Pre/post voice comparison run on all AI-edited dialogue
- [ ] AI-ism scan run on all generated/edited prose
- [ ] Final delivery package includes: manuscript, diff, change log, board report, prompts used
- [ ] Author has approved all changes before final version lock

---

## Related Skills

| Skill | How It Connects |
|-------|----------------|
| `editorial-review` | Board review protocol for manuscripts — structural analysis, multi-pass strategy |
| `editorial-review-pipeline` | Full pipeline from manuscript prep through board review, report compilation, refactoring, and delivery |
| `board-review-protocol` | Multi-model quality gates — hallucination detection, structured verdicts |
| `model-consulting` | Deliberate model routing, consult/merge patterns, model selection |
