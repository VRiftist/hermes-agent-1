# Session Audit Findings — 2026-05-27

## Audit Scope

End-to-end operational integrity review of Hermes Agent infrastructure,
credential state, deployment artifacts, and status documentation.

---

## 1. Context-Compaction Phantom Completions

### Finding
Status summary from a prior session listed
`KIMI_HANDLING_LOCKED.md` as "Created ✅" and "Synced to linux_prod ✅."
The file did not exist on disk — it was a **ghost entry** carried forward
through context window compaction.

### Mechanism
- Original write happened in a prior session (Session A).
- Session A's summary marked the action as complete.
- Context compaction between sessions preserved the "✅" marker.
- This session (Session B) accepted the marker at face value until a
  manual `find` revealed the file was missing.

### Lesson
Status markers are **claims**, not proofs. The operational-integrity
checklist must include a filesystem probe for every "created" or
"modified" entry, not just a grep of the STATUS file itself.

### Detection Script
```bash
# Find files mentioned as "created" or "synced" in STATUS files
# that don't actually exist on disk
grep -oP '(?<=["\x27])(?:~|\$HOME)[^"\x27]+(?=["\x27])' \
  ~/.hermes/STATUS_*.md | sort -u | while read f; do
    [ -f "$f" ] || echo "PHANTOM: $f"
done
```

---

## 2. Stale PID in STATUS.md

### Finding
`SESSION_PIN.md` line 26 stated PID `56166`; actual gateway PID was
`64251`. The PID had drifted across restarts without the status file
being updated.

### Lesson
PID references in status files have a **half-life** — they are accurate
only until the next restart. Any status file referencing a PID should
include a verification note and a TTL (time-to-live) marker.

### Recommendation
Replace static PIDs with a script reference:
```bash
# Instead of: PID 64251
# Use: $(pgrep -f "hermes gateway" | head -1)
```

---

## 3. nginx Dual-Master State Divergence

### Finding
Two nginx master processes were running simultaneously, each serving
from a different config. The reported state ("nginx running") was
technically correct but **misleadingly singular** — it implied one
instance, not two competing ones.

### Detection
```bash
ps aux | grep nginx | grep -v grep
# Expected: 1 master + N workers
# Actual:   2 masters + N workers
```

### Lesson
"Is service X running?" is the wrong question. **"How many instances
of service X are running?"** is the correct one. State checks should
count, not just boolean.

---

## 4. Credential Layer Divergence

### Finding
Four credential layers for GitHub auth were out of sync:

| Layer | State |
|-------|-------|
| `.env` (GITHUB_PAT) | ✅ Correct (93-char) |
| `~/.config/gh/hosts.yml` | ❌ Truncated (~20 chars) |
| `~/.gitconfig` | ❌ Duplicate `credential.helper` entries |
| macOS keyring | ❌ Stale token ending in `982_` |

### Lesson
Each credential layer can independently drift. A single-layer check
(e.g., `gh auth status`) may report one layer while another layer is
actually being used by `git push`.

### Recommendation
Cross-layer audit script:
```bash
echo "=== .env ===" && grep GITHUB_PAT ~/.hermes/.env | cut -c1-20
echo "=== hosts.yml ===" && cat ~/.config/gh/hosts.yml | head -3
echo "=== gitconfig ===" && git config --global --get-all credential.helper
echo "=== gh status ===" && gh auth status --show-token 2>/dev/null | head -2
```

---

## 5. Config YAML Env-Var Name Mismatch

### Finding
`config.yaml` referenced `${OPENROUTER_KEY_1}` but `.env` had been
renamed to `OPENROUTER_API_KEY`. This caused Ring quality gate and
model routing to silently fail.

### Lesson
Env var renames must trigger a **grep across all config files** for the
old name. A single missed reference causes silent failures.

### Detection
```bash
# After renaming an env var, search all configs for the old name
OLD_NAME="OPENROUTER_KEY_1"
grep -rn "$OLD_NAME" ~/.hermes/hermes-agent/config.yaml \
  ~/.hermes/config.yaml 2>/dev/null
```

---

## Trust-But-Verify Checklist (Updated)

- [ ] All files mentioned in STATUS_*.md exist on disk
- [ ] All "created" / "synced" claims verified with `diff` or content read
- [ ] All credential writes verified with `wc -c` length check
- [ ] No orphaned references to files that were never created
- [ ] Cron entries match actual scripts on disk
- [ ] Config env var names match between `.env` and `config.yaml`
- [ ] PID references in status files are verified at session start
- [ ] Service instance counts verified (not just running/stopped)
- [ ] All credential layers cross-referenced for consistency
- [ ] `hosts.yml` checked for truncation after any write operation