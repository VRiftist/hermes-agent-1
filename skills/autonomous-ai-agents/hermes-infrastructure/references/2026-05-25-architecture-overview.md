# Hermes 5-Model Architecture (2026-05-25)

Current verified topology for the multi-machine, local-first Hermes agent.

## Hardware Nodes

| Node | Role | CPU | RAM | GPU | OS | Hostname |
|------|------|-----|-----|-----|----|---------|
| Mac Mini | Primary interactive | Apple M2 | 32GB unified | None | macOS 26.5 | LumenHubs-Mini |
| Linux Box | GPU inference | — | 45GB | RTX 3060 12GB | Linux | 192.168.1.230 |
| User | Input/output | — | — | — | — | Telegram (@Gmano_bot) |

## Network Topology

```
User (Phone)
    │  Telegram HTTPS
    ▼
Mac Mini (LumenHubs-Mini)
    ├── Ollama:qwen3:14b (16K, local, Primary)
    ├── Ollama:qwen3:8b (32K, local, Quick tasks)
    ├── Hermes Gateway (Telegram bot, launchd)
    ├── SSH → Linux Box
    └── Cloud APIs (OpenRouter, DeepSeek, xAI)
    │
    └── Linux Box (via SSH tunnel)
        ├── Ollama:qwen3-14b-128k (128K, local, Heavy)
        └── Ollama:qwen3:8b (32K, local, Fast)
```

## 5-Model Chain

| # | Model | Provider | Node | Context | Cost | Source | Verified |
|---|-------|----------|------|---------|------|--------|----------|
| 1 | qwen3:14b | mac-ollama | Mac | 16K | Free | Local | ✅ HTTP |
| 2 | qwen3:8b | mac-ollama | Mac | 32K | Free | Local | ✅ HTTP |
| 3 | qwen3-14b-128k | linux-ollama | Linux | 128K | Free | Local | ✅ HTTP |
| 4 | deepseek-v4-flash | deepseek | Cloud | 32K | $0.14/M | OpenRouter | ✅ HTTP 200 |
| 5 | grok-4.20-reasoning | x-ai | Cloud | 16K | $1.25/M | xAI | ✅ HTTP 200 |
| 6 | ring-2.6-1t | openrouter | Cloud | 16K | $0.88/M | OpenRouter | ✅ HTTP 200 |

**Dead:** kimi-coding (moonshot-v1) → HTTP 401 — awaiting valid API key

## Routing Decision (Simplified)

```
                    ┌──────────────┐
                    │  TASK INCOMES │
                    └──────┬───────┘
                           │
                ┌──────────▼──────────┐
                │  Under 200 tokens?  │
                └────┬─────────┬──────┘
                  YES│         │NO
                      ▼         ▼
              ┌──────────┐  ┌──────────────────┐
              │ qwen3:8b │  │ Need reasoning?   │
              │ (fast)   │  └──┬────────┬───────┘
              └──────────┘ YES │        │ NO
                     ┌─────────▼──┐  ┌──▼───────────────────┐
                     │grok-4.20   │  │ Need long context?   │
                     │(creative)  │  ├── YES → qwen3-14b-128k (linux)
                     └─────┬──────┘  ├── YES → deepseek-v4-flash (cloud)
                           │        └── NO  → qwen3:14b (mac, free)
                    ┌──────┴───────┐
                    │ FINAL GATE   │
                    │ ring-2.6-1t  │
                    │ (verification)│
                    └──────────────┘
```

## Latency Estimates

| Mode | First Token | Full Response |
|------|------------|---------------|
| mac-ollama (qwen3:8b) | ~0.5s | ~1-2s |
| mac-ollama (qwen3:14b) | ~1s | ~3-5s |
| linux-ollama (qwen3-14b-128k) | ~1s | ~3-8s |
| deepseek-v4-flash (cloud) | ~2s | ~5-15s |
| grok-4.20-reasoning (cloud) | ~4s | ~15-45s |
| ring-2.6-1t (cloud) | ~3s | ~10-30s |

## Context Budget

Default working context per model:
- qwen3:8b → max 16K tokens
- qwen3:14b → max 8K tokens (peaks ~4K onward with compression)
- qwen3-14b-128k → max 64K tokens
- deepseek-v4-flash → max 32K tokens
- grok-4.20-reasoning → max 12K tokens
- ring-2.6-1t → max 12K tokens

Active context trimming preserves top-of-context identity block + last N relevant messages.