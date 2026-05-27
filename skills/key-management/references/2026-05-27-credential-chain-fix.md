# 2026-05-27 — Credential Chain Fix: Full Session Record

## Summary

Four credential-layer failures discovered and fixed in one session.
Root cause: siloed credential management across four independent systems
(GitHub .env, gh CLI hosts.yml, gitconfig helpers, macOS keyring).

---

## Failure #1 — GitHub PAT Silently Truncated on Write

**Symptom:** `git push` returned 403 despite a valid 93-char PAT.
**Cause:** `write_file` to `~/.hermes/.env` silently truncated the PAT value
from `github_pat_11AFKNZOA0BpCCUWcl2982_...` (93 chars) to `github...LP4U` (~20 chars).
**Evidence:** `wc -c` on the GITHUB_PAT line showed only 20 chars post-write.
**Fix:** Replaced with full value using raw Python file I/O. Verified with
`grep GITHUB_PAT .env | awk -F= '{print length($2)}'` → 93.

**Prevention pattern:**
```python
# Always read-back after write
with open(path) as f:
    actual = f.read()
assert expected_value in actual, f"Write failed: value not found in {path}"
```

---

## Failure #2 — `gh` CLI Resolving Stale Keyring Token

**Symptom:** `gh auth status` showed token ending `...982_` not our new PAT.
**Cause:** macOS keyring held a prior `gh auth login` token. Even after
writing the full PAT to `hosts.yml`, `gh` resolved the keyring entry first.
**Fix:**
```bash
gh auth logout
gh auth login --with-token   # paste full PAT from .env
gh auth status --show-token  # verify starts with github_pat_11A
```
**Verification:** Token in `gh auth status` now ends `...C7p4` (matches PAT).

---

## Failure #3 — Duplicate `credential.helper` in `.gitconfig`

**Symptom:** `python3 configparser` threw DuplicateOptionError reading `~/.gitconfig`.
**Cause:** Multiple `[credential]` sections with empty `helper =` lines
plus `[credential "https://github.com"]` with gh helper. Git resolved
ambiguously, sometimes using the empty helper (which does nothing).
**Fix:** Rewrote `.gitconfig` to two clean sections:
```ini
[credential "https://github.com"]
    helper = !/opt/homebrew/bin/gh auth git-credential
[credential "https://gist.github.com"]
    helper = !/opt/homebrew/bin/gh auth git-credential
```

---

## Failure #4 — `openai_api_key` env var not found

**Symptom:** `openai_api_key` referenced in code but no entry in `.env`.
**Cause:** Key was never injected; the app falls back to an empty string
which produces cryptic errors downstream.
**Fix:** Noted in audit. Needs `OPENAI_API_KEY=sk-...` added.

---

## Verification Checklist (Post-Fix)

- [x] `cat ~/.hermes/.env | grep GITHUB_PAT | wc -c` → 93+ chars
- [x] `gh auth status` → token starts with `github_pat_11A`
- [x] `git config --global --list | grep credential` → no duplicates
- [x] `python3 -c "import configparser; configparser.ConfigParser().read('~/.gitconfig')"` → no error
- [x] `python3 -c "from api_error_handler import classify_api_error"` → import works
- [x] `crontab -l` → expected entries present

---

## Preventing Recurrence

1. **Credential writes must include read-back verification.**
   Never report "written" without verifying the actual file content.

2. **Env var renames must grep the full repo.**
   `grep -r "OPENROUTER_KEY_1" ~/.hermes/` before and after rename.

3. **`gh auth status` should be part of deploy checklist.**
   Token mismatch between keyring and hosts.yml is silent and hard to debug.

4. **Value-length assertion on env vars:**
   ```bash
   # In any deploy script:
   for var in GITHUB_PAT OPENROUTER_API_KEY KIMI_API_KEY; do
     val=$(grep "^${var}=" ~/.hermes/.env | cut -d= -f2)
     min_len=$([ "$var" = "GITHUB_PAT" ] && echo 90 || echo 30)
     [ ${#val} -ge $min_len ] || echo "ERROR: $var is too short (${#val} chars)"
   done
   ```