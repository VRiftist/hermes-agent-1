# Credential Truncation Audit — 2026-05-27

## Summary

Two separate credential truncation failures were discovered and fixed
during the session. Both share the same root cause: **write functions
report success when the target buffer or filesystem silently truncates
the content.**

---

## Case 1: `.env` truncation (original, 2026-05-27)

- **What:** A GitHub PAT (~93 chars) was silently truncated to ~20 chars
  inside `~/.hermes/.env`.
- **Symptom:** `gh auth login --with-token` accepted the value without
  error; `git push` returned 403.
- **Root cause:** The `write_file` call reported success despite the OS
  or filesystem truncating the value at the `=` delimiter.
- **Fix:** Post-write verification script added to key_guardian that
  checks `${#value}` against expected ranges per key type.

## Case 2: `hosts.yml` truncation (new, 2026-05-27)

- **What:** The full 93-char GitHub PAT in
  `~/.config/gh/hosts.yml` was truncated to `github_pat_11...LP4U`
  (approximately 20 chars).
- **Symptom:** `gh auth status --show-token` displayed the truncated
  value; `git push` and `gh api` both failed with 401/403.
- **Discovery:** The PAT was manually re-inserted using a heredoc
  (`cat > hosts.yml << 'EOF'`) which bypassed any length-limited write
  path.
- **Fix:** Replaced truncated value with full PAT via terminal
  heredoc + `chmod 600`.

**Key difference from Case 1:** The `.env` write went through the
Hermes `write_file` tool; the `hosts.yml` write likely went through a
prior session's `write_file` call that hit the same silent-truncation
bug in a different filesystem path. This confirms the truncation is
not path-specific — it is a **tool-level behavior** that must be
guarded globally.

---

## Prevention

1. **All credential writes** must include a read-back verification
   step that asserts `len(value) >= expected_min_length`.
2. **Minimum expected lengths:**
   - GitHub PAT: 80 chars
   - OpenRouter API key: 40 chars
   - Kimi API key: 30 chars
   - DeepSeek API key: 40 chars
3. **`hosts.yml` must be in the key_guardian check set** — it was
   previously only verifying `.env`.
4. **Never use `write_file` for credentials without `--verify`.**
   Use terminal heredoc as the safe fallback:
   ```bash
   cd ~/.config/gh && cat > hosts.yml << 'PAT'
   # paste full PAT
   PAT
   chmod 600 hosts.yml
   ```

---

## Cross-Reference

- `operational-integrity` skill: "Credential Integrity" anti-pattern
- `github-auth` skill: troubleshooting entry for truncated PAT