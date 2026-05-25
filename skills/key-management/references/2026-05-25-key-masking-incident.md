# .env Key Masking Root Cause Analysis

> Date: 2026-05-25 | Skill: key-management

## Incident

All cloud API calls to DeepSeek and Grok failed with HTTP 401/400. The multi-model blueprint review script (`run_full_review.py`) was rebuilt with forced-model routing, but still failed because the keys themselves were never populated.

## Root Cause

The `.env` file contained placeholder values:

```
DEEPSEEK_API_KEY=***      # 3 chars, literal asterisks
XAI_API_KEY=***           # 3 chars, literal asterisks
```

Config.yaml references `${DEEPSEEK_API_KEY}` resolved to `***`, which DeepSeek correctly rejected as invalid.

Why the placeholder survived:
- Keys were "set" in a prior session by editing config.yaml with the assumption they'd also be in .env
- `key_guardian.py` was never re-run after the supposed key update
- Sandbox display masking (`***`) hid the problem during debugging

## Prevention Protocol

1. After every key change: Run `python3 ~/.hermes/scripts/key_guardian.py` immediately
2. Pre-flight check: Add to any cloud-API script:
   ```python
   assert len(key) > 10, f"{var} appears to be a placeholder"
   ```
3. Verify raw values (not masked display):
   ```python
   env_path = os.path.expanduser("~/.hermes/.env")
   with open(env_path) as f:
       for line in f:
           if "=" in line and not line.startswith("#"):
               k, v = line.split("=", 1)
               if "KEY" in k:
                   print(f"{k}: len={len(v)} masked={'***' in v}")
   ```

## Key Status (2026-05-25)

| Key | Status | Action Needed |
|-----|--------|---------------|
| `DEEPSEEK_API_KEY` | ❌ Placeholder | Complete onboarding at platform.deepseek.com |
| `XAI_API_KEY` | ❌ Placeholder | Get API key from console.x.ai (not Grok-chat token) |
| `OPENROUTER_KEY_1` | ✅ Present (13 chars) | Verify valid via curl test |
| `KIMI_API_KEY` | ✅ Present (51 chars) | Verify via kimi_client.py self-test |
| `KIMI_API_KEY_2` | ✅ Present (51 chars) | Backup key for rotation |