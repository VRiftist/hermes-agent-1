# Config Corruption Recovery — Session Reference

**Date:** 2026-05-24
**Context:** Full config rebuild after corruption caused gateway crash-loop

---

## What Happened

`~/.hermes/config.yaml` became corrupted with:
- **Duplicate `[model]` blocks** (lines 1–9 and 10–14)
- **Stale OpenRouter API key** references
- **Duplicate `[providers]`, `[model_catalog]`, `[custom_providers]`, `[ollama]`** blocks scattered through the file
- **Conflicting `fallback_providers`** declared at both top level and inside the `model:` block

## Symptoms Observed
- Gateway crash-loop (8 restarts visible in `gateway-exit-diag.log`)
- Telegram messages returning errors
- No models loaded in Ollama
- SSH to Linux box unreachable (sshd not running)

## Recovery Actions Taken

1. Backed up broken config as `config.yaml.broken.<timestamp>`
2. Rebuilt `config.yaml` from scratch using `config.yaml.bak.headless2` as structural reference
3. Clean three-tier fallback chain established:
   - Primary: `ring-2.6-1t` (OpenRouter)
   - First fallback: `qwen3-14b-128k:latest` (Linux Ollama)
   - Second fallback: `deepseek-reasoner-flash` (direct API)
4. Killed stale gateway processes, restarted with `--replace`
5. Gateway PID 3130 confirmed stable

**Prevention**

- Always edit config via `hermes config edit` or `hermes config set` — CLI validates on write
- If hand-editing, diff against a known-good backup first
- Before any major change: `cp config.yaml config.yaml.bak.$(date +%s)`

**Lessons from 2026-05-24 audit:**

- **Duplicate `fallback_providers`** can appear at both the top level and inside the `model:` block — having two copies causes silent corruption. After editing config, always verify: `grep -n "fallback_providers" ~/.hermes/config.yaml` — should return exactly ONE match.
- **Port mismatch**: Linux Ollama runs systemd on port `11434` (localhost-only) but a userland process on port `11435` (all interfaces). The `providers.linux.base_url` in config.yaml MUST use `11435` for remote access from Mac. Port `11434` silently fails from outside the box. Verify with: `ssh linux 'ss -tlnp | grep 1143'` to see which port is on which interface.
- **`.env` bloating**: The `.env` file can silently accumulate duplicate template content. Always verify line count (`wc -l ~/.hermes/.env`) — if >100 lines, it's probably corrupted with duplicate templates. Clean it to only the keys you actually need.