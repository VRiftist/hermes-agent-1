# Session-Specific Config Notes — 2026-05-24

## What Was Fixed
1. `config.yaml` rebuilt: fallback chain set to mac → linux → deepseek → ring
2. DeepSeek API key injected (line ~5)
3. OpenRouter Ring API key injected (line ~24)
4. Duplicate `fallback_providers` removed (was at line 8 AND 29)
5. `.env` rebuilt from 477-line corrupted state to 8 valid lines
6. Discord disabled (commented out)

## Outstanding Issues
- Telegram token `8749847449:AAHn9lvhN7uZpxYjv3SwUUdgPRI98dgPEqs` returns 401 — **needs valid replacement from @BotFather**
- Duplicate API keys still present at 3 locations in config.yaml (2 distinct values)
- `providers:` block may be structurally weakened after sed line deletion — verify on next audit
- SSH not working: `sshd` not running on Linux box, no `authorized_keys` entry for `lumenhubai`
- Gateway PID 5836 (launchd)