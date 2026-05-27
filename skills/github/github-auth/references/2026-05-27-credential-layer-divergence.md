# Credential Layer Divergence — 2026-05-27

## Incident

`git push` to `origin feat/gateway-integration-wiring` returned 403
despite a valid GitHub PAT being present in `~/.hermes/.env`.

## Root Cause: Four-Layer Divergence

GitHub authentication in this environment flows through four independent
layers, each with its own credential store. Three of four were stale,
truncated, or duplicated.

| # | Layer | File | Status |
|---|-------|------|--------|
| 1 | `.env` | `~/.hermes/.env` | ✅ Full 93-char PAT |
| 2 | gh CLI hosts | `~/.config/gh/hosts.yml` | ❌ Truncated to ~20 chars |
| 3 | Git config | `~/.gitconfig` | ❌ Multiple `credential.helper` entries (empty + gh) |
| 4 | macOS keyring | System keychain | ❌ Stale token ending `982_` |

`git push` resolved through layer 4 (keyring), which held the oldest
token. The new PAT in `.env` (layer 1) was never used by git.

## Resolution Sequence

```bash
# Step 1: Log out of gh CLI (clears keyring reference)
gh auth logout

# Step 2: Re-authenticate with full PAT
gh auth login --with-token   # paste 93-char PAT from password manager

# Step 3: Fix gitconfig — remove ALL credential helpers, add single gh helper
git config --global --unset-all credential.helper
git config --global --add credential.helper '!gh auth git-credential'

# Step 4: Verify hosts.yml was written by gh auth (should now be full PAT)
cat ~/.config/gh/hosts.yml
# Expected: oauth2_token value ≈ 93 chars

# Step 5: Verify git uses the correct credential path
git credential fill <<< "protocol=https
host=github.com"
# Should return the new token

# Step 6: Test push
git push fork feat/gateway-integration-wiring
```

## Prevention

1. After any credential rotation, run the cross-layer audit:
   ```bash
   echo "=== .env ===" && grep -c "^GITHUB_PAT\|^GITHUB_TOKEN" ~/.hermes/.env
   echo "=== hosts.yml ===" && wc -c ~/.config/gh/hosts.yml
   echo "=== gitconfig ===" && git config --global --get-all credential.helper
   ```

2. `hosts.yml` file size should be >200 bytes (a full 93-char PAT entry
   is ~150 bytes minimum). If it's <100 bytes, suspect truncation.

3. Never manually edit `hosts.yml` with tools that may silently
   truncate. Use terminal heredoc or `gh auth login --with-token`.

## Cross-Reference

- `key-management` skill: Section 4 (Credential Chain), Known Issues
- `github-auth` skill: Troubleshooting table