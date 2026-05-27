---
name: operational-integrity
category: meta
description: Ensuring reported state matches actual state. Preventing phantom completions, verifying work actually happened, and maintaining workflow discipline across sessions.
tags:
  - "state-verification"
  - "phantom-completion"
  - "workflow-discipline"
  - "audit"
  - "credential-integrity"
version: "1.0.0"
updated: "2026-05-27T16:45"
related_skills:
  - key-management
  - hermes-infrastructure
references:
  - references/2026-05-27-phantom-completion-audit.md
---

## Purpose

This skill governs a meta-discipline: **making sure work that was reported as done actually happened.** It covers the patterns, pitfalls, and verification workflows that prevent phantom completions — the most insidious class of failure in long-running agent sessions.

## The Problem

In multi-turn agent sessions, context window compaction causes a specific failure mode:

1. Agent performs an action (e.g., "creates KIMI_HANDLING_LOCKED.md")
2. Context is compacted between turns
3. The status summary carries forward the action marker ("done")
4. On the next turn, the agent reads the summary and believes the work is done
5. The work was never actually completed

This is not a memory bug — it's a **verification gap**. The system has no habit of checking its own work.

## Core Principle

> **Never trust a status marker without a file-system proof.**
> Before reporting "X is done," verify X exists on disk.

## Verification Workflow

After any action that claims to create, modify, or sync a file:

### Step 1: Read-back
```python
# Immediately after write:
with open(path) as f:
    content = f.read()
assert len(content) > 0, f"{path} is empty"
assert expected_marker in content, f"{path} missing expected content"
```

### Step 2: Cross-reference
If a status file claims "X was synced to Y," verify the sync:
```bash
diff /path/to/source /path/to/destination
# Must return: (identical)
```

### Step 3: Status audit (periodic)
At session boundaries, do a quick sweep:
- Do files claimed as "created" actually exist?
- Do files claimed as "modified" reflect the claimed changes?
- Do status markers match filesystem reality?

## Known Anti-Patterns

### Phantom Completion
**Pattern:** Marking an action as "✅ Done" in a status summary when the underlying work was not performed.

**Example (2026-05-27):**
- Status claimed: "`KIMI_HANDLING_LOCKED.md` — Created, synced to linux_prod"
- Reality: File did not exist on disk. Never written.
- Cause: The original action was performed in a prior session, reported in the compacted summary, but the write was lost (possibly due to context window truncation of the actual write call).
- Detection: `find ~/.hermes -name "KIMI_HANDLING_LOCKED.md"` → not found

### Credential Drift
**Pattern:** Assuming a credential is in one state while it's in another.

**Example (2026-05-27):**
- `gh auth status` showed an old token (ending `982_`) while `.env` and `hosts.yml` had been updated with a new PAT.
- The three credential layers (keyring, hosts.yml, .gitconfig) were out of sync.
- Detection: `gh auth status --show-token` + `cat ~/.config/gh/hosts.yml` + `cat ~/.ssh/config` comparison

### Ghost Reference
**Pattern:** A file or document referenced in status/plan entries that doesn't exist.

**Detection:** Periodically grep status files for file paths and verify each exists:
```bash
grep -oP '~/\S+\.(md|py|sh|yml)' ~/.hermes/STATUS_*.md | sort -u | while read f; do
    [ -f "$f" ] || echo "MISSING: $f"
done
```

## Session Integration

This skill should be consulted at these points:

1. **End of every session** — Run a quick verification sweep of all artifacts claimed as "created" or "modified"
2. **Start of every session** — Verify status file claims against actual filesystem state before acting on them
3. **After any `write_file` or `patch` call** — Read the file back and verify content
4. **Before pushing to git** — Verify committed files match what was intended (check `git diff --stat`)

## The "Trust but Verify" Checklist

Run this at session boundaries:

- [ ] All files mentioned in STATUS_*.md exist on disk
- [ ] All claimed modifications are reflected in actual file content (not just file existence)
- [ ] All credential writes verified with read-back
- [ ] All "synced to linux_prod" claims verified with `diff`
- [ ] No orphaned references to files that were never created
- [ ] Cron entries match actual scripts on disk
- [ ] Config env var names match between `.env` and `config.yaml`

## Loading This Skill

```
/skill operational-integrity
```