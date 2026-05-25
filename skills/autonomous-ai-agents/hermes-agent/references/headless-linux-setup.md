# Headless Linux Setup

When running Hermes on a headless Linux box (no desktop environment), several configuration and platform considerations apply.

## Model Selection (RTX 3060, 12GB VRAM)

| Model | VRAM | Speed | Context | Best Use |
|-------|------|-------|---------|----------|
| `qwen3-14b-128k:latest` | ~8GB | Fast | 128K | Primary — best context-to-size ratio for context checking |
| `qwen3:8b` | ~4GB | Very fast | 64K | Fallback / lightweight tasks |
| `qwen2.5-coder:14b` | ~8GB | Fast | 64K | Coding-specific fallback |
| `qwen2.5-coder:32b-instruct-q4_K_M` | ~20GB | Slower | 96K | Too large for 12GB GPU — avoid on this hardware |

## Config Pitfalls

1. Duplicate provider definitions — consolidate into a single `providers.linux` entry referenced by `model.provider`.
2. Wrong ports — default Ollama is 11434, not 11435. Verify with `curl http://<host>:11434/api/tags`.
3. localhost vs actual IP — never use 127.0.0.1 when Hermes runs on Mac but Ollama is on Linux; use the LAN IP (e.g. 192.168.1.230).
4. Stale model.default — if the model name does not match any model in the provider's `models` map, Hermes falls back or errors. Verify with `hermes doctor`.

## Platform Connectivity (Headless)

- **Telegram**: Works headless in userbot mode — no desktop app needed.
- **Discord**: Requires desktop app or token-based connection; gateway retries indefinitely with "failed to connect" on headless Linux.
- **Slack/WhatsApp/Signal/Mattermost/Matrix**: All gateway-only, no desktop dependency.

## Restart / Resilience

- **Mac (launchd)**: Gateway plist with `KeepAlive: true` auto-restarts on crash and at login.
- **Linux (systemd)**: Create a `systemd --user` unit so the gateway survives reboots without a login session.