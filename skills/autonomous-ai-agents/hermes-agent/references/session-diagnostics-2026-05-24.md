# Session Diagnostics — 2026-05-24
## Full Hygiene Audit & Recovery

### Context
User requested a full hygiene audit of Hermes gateway setup. Mac Mini M2 (32GB) communicating with Linux box (RTX 3060, 45GB RAM) for local LLM inference via Ollama.

---

## Issues Found (9 total, 7 fixed in session, 2 await user input)

### CRITICAL — Fixed

1. **Config.yaml: `providers` block completely empty**
   - The entire `providers: {}` was wiped, likely from a previous overzealous sed/patch
   - Recovery: Rebuilt via Python + PyYAML, restoring linux/openrouter/deepseek providers

2. **Config.yaml: Fallback chain broken**
   - `fallback_providers: []` and `fallback: ''` — both blank
   - Restored to `fallback_providers: ['openrouter', 'deepseek']`, `fallback: qwen3-14b-128k:latest`
   - Chain: Linux Ollama (primary) -> OpenRouter Ring-2.6-1t -> DeepSeek (last resort)

3. **Config.yaml: Wrong port for remote Linux Ollama**
   - Config pointed to `11434` which binds to `127.0.0.1` only (unreachable from LAN)
   - Linux Ollama user-space process listens on `11435` (all interfaces, `0.0.0.0`)
   - Fixed: `base_url` changed to `http://192.168.1.230:11435/v1`
   - Verification: `curl http://192.168.1.230:11435/api/tags` returned model list

### MODERATE — Fixed

4. **`.env` file bloated (477 lines)**
   - Template had been appended to itself, mixing commented template with real keys
   - Replaced with 8 clean lines containing only active values

5. **`TERMINAL_CWD` deprecation warning**
   - Was set in `.env` as `TERMINAL_CWD=/Users/lumenhubai`
   - Migrated to `config.yaml` -> `terminal.cwd: /Users/lumenhubai`
   - Removed from `.env` — warning eliminated

6. **SSH to Linux box — `ssh-agent` had no identities**
   - `ssh gerald@192.168.1.230` returned `Permission denied (publickey,password)`
   - Root cause: `ssh-agent` process existed but had no loaded keys
   - Fix: `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/lumenhub`
   - Verified: SSH connection works, `hostname` returns Linux box name

### AWAITING USER INPUT

7. **Telegram Bot Token — INVALID**
   - Token `874984...PEqs` contains literal dots — not a valid BotFather token
   - Error: `telegram.error.InvalidToken: Not Found`
   - **This is the primary reason messaging doesn't work**

8. **Discord — No token** (optional, non-blocking)

---

## Performance Notes: Mac M2 vs Linux RTX 3060

| Metric | Mac M2 (32GB unified) | Linux RTX 3060 (12GB VRAM) |
|--------|----------------------|---------------------------|
| qwen3:14b Q4 speed | ~10-20 tok/s | ~20-40+ tok/s |
| 32B model feasibility | Very slow (~5-8 tok/s) | Viable with CUDA offload |

**Routing decision**: 32B qwen-coder on Linux is correct. Ring-2.6-1t via OpenRouter stays as cloud fallback.

---

## Key Learnings for Future Sessions

1. **ssh-agent loses keys between sessions** — always verify with `ssh-add -l` before testing SSH connections
2. **Ollama port conflict pattern** — systemd Ollama binds localhost only (11434), userland Ollama binds all interfaces (11435)
3. **SED can silently empty YAML blocks** — always diff after sed on config.yaml
4. **`.env` bloat pattern** — template content gets duplicated on repeated writes; check `wc -l` before and after
5. **Telegram token validation** — test with `curl https://api.telegram.org/bot<TOKEN>/getMe` before deeper debugging