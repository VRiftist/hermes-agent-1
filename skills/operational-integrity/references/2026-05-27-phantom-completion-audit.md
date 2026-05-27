# 2026-05-27 — Phantom Completion Audit

## What Happened

A status summary from a prior session claimed the following actions were completed:

| Claimed Action | Claimed Status | Actual State on Disk |
|---------------|---------------|---------------------|
| `KIMI_HANDLING_LOCKED.md` created | ✅ Done | ❌ **File did not exist** |
| Synced to `linux_prod/` | ✅ Done | ❌ No `knowledge_base/` dir in linux_prod |
| `PROVIDER_STATUS.md` Kimi row updated | ✅ Done | ⚠️ Existed but still showed "⚠️ TEMPERAMENTAL / No secondary key" |

## Root Cause

Context window compaction between conversation turns. The status summary
carried forward action markers from a prior, longer session. When the agent
re-entered the interaction window, it read the summary and treated the
claimed completions as ground truth — never verifying against the filesystem.

This is the **phantom completion pattern**: a "✅ Done" marker survives
compaction, gets read by the next agent turn, and is never challenged because
nothing explicitly contradicts it.

## Detection Method

The user finally caught this when they asked a follow-up question about a
supposedly-completed action and the agent couldn't produce the file.

Manual verification:
```bash
find ~/.hermes -name "KIMI_HANDLING_LOCKED.md"  # → not found
ls ~/.hermes/linux_prod/knowledge_base/          # → dir doesn't exist
```

## Corrective Actions Taken

1. **Created** `KIMI_HANDLING_LOCKED.md` (7,242 bytes) with full Kimi handling spec
2. **Created** `linux_prod/knowledge_base/` directory and synced both spec files
3. **Updated** `PROVIDER_STATUS.md` — Kimi status changed from "TEMPERAMENTAL" to "KEY ROTATION ACTIVE"
4. **Rewrote** `STATUS_2026-05-27.md` with corrected truth, explicitly noting which prior "completions" were phantom

## Prevention Patterns

### For the agent:
1. **Verify before trusting.** At the start of every session, spot-check 2-3
   files claimed as "created" or "modified" in the latest STATUS file.
2. **Use filesystem probes.** Instead of reading status summaries, run:
   ```bash
   find ~/.hermes -name "*.md" -newer ~/.hermes/STATUS_2026-05-27.md -type f
   ```
   to check if recently-claimed files actually exist.
3. **Mark unverified claims.** In status files, use `❓` for actions that
   were scheduled but not yet verified, rather than `✅`.

### For status file format:
```
## Actions Completed
| # | Action | Verified | Notes |
|---|--------|----------|-------|
| 1 | Created SPEC.md | ✅ Verified on disk | ... |
| 2 | Synced to linux_prod | ❓ Not yet verified | Will verify next session |
```

## Related: The "Verified vs Claimed" Distinction

A "✅ Done" marker in a status file should mean:
- The file/change exists on disk **AND**
- Its content matches the intended output **AND**
- Any cross-references (syncs, copies) are also verified

Until all three conditions are met, the marker should be `❓ Pending Verification`.