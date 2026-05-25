# SSH Connectivity Testing Matrix

Quick-reference for verifying bidirectional SSH and service reachability.

## Quick Test Commands

```bash
# Mac → Linux
ssh -o BatchMode=yes linux "echo OK && hostname"

# Linux → Mac (non-standard port)
ssh -o BatchMode=yes -p 2222 lumenhubai@192.168.1.240 "echo OK && hostname"

# Ollama on Linux
curl -s http://192.168.1.230:11434/api/tags | python3 -m json.tool | head -5

# Ollama on Mac
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool | head -5
```

## Provider URLs (Updated 2026-05-24)

| Provider | URL | Notes |
|----------|-----|-------|
| Linux Ollama | `http://192.168.1.230:11435/v1` | **Port 11435** (all interfaces), NOT 11434 (localhost-only) |
| Mac Ollama | `http://127.0.0.1:11434/v1` | Local only |
| OpenRouter | `https://openrouter.ai/api/v1` | Cloud fallback |
| DeepSeek | `https://api.deepseek.com/v1` | Direct API fallback |

## Known Gotchas
- Linux Ollama systemd service listens on 11434 (localhost). A separate userland process listens on 11435 (all interfaces).
- The watchdog script (`~/ai-team-shared/scripts/ollama-watchdog.sh`) monitors port 11434 — but the userland Ollama on 11435 is what actually serves remote requests.
- If `curl http://192.168.1.230:11434/api/tags` fails from Mac but `:11435` works, that's expected — it's a firewall/binding issue, not a broken setup.