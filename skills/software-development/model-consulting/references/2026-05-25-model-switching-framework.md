# Model Switching Framework — Memory Palace Structure

Created: 2026-05-25
Updated: 2026-05-25 evening — keys verified, table corrected

## Problem Statement

Current system had model switching as **passive fallback only** (key breaks → try next). What's needed is **deliberate, active model routing** — CONSULT, MERGE, DELEGATE — with full context coherence preserved across switches.

## Identity Block (Inject at every model handoff)

```
[IDENTITY]
Agent role: Hermes Agent — orchestrator
Human: lumenhubai (Mac M2 32GB + Linux RTX 3060)
Primary interface: Telegram
Current phase: [PHASE_NAME]
Active objective: [OBJECTIVE]

[POWERS]
- Code generation (Grok/DeepSeek)
- Deep reasoning (Ring)
- File operations (terminal, file tools)
- Delegation (delegate_task subagents)
- Web/file/memory access

[CONSTRAINTS]
- No autonomous state changes without user approval
- No parallel benchmarks on 32GB hardware
- No full conversation copy-paste at handoff
- Keep secrets redacted (redact_secrets: true)

[ACTIVE CONTEXT]
Project: [PROJECT]
Phase: [PHASE]
Decisions made this session: [LIST]
Open questions: [LIST]
Previous model outputs: [FILE_REF]
```

## Memory Palace Zones

Zone 1 (top of context): Identity block + current task state
Zone 2: Active constraints and preferences
Zone 3: Working memory (current pipeline state)
Zone 4: Long-term reference (architecture decisions, schema)
Zone 5: Ephemeral (will be trimmed first)

## Provider Status — Last Verified 2026-05-25

| Provider | Model | Key Status | Context | Cost Tier |
|----------|-------|-----------|---------|-----------|
| OpenRouter | ring-2.6-1t | ✅ Live (HTTP 200) | 16K | Mid |
| DeepSeek | deepseek-v4-flash | ✅ Live (HTTP 200) | 32K | Cheap |
| DeepSeek | deepseek-v4-pro | ✅ Live (HTTP 200) | 32K | Cheap |
| xAI | grok-4.20-reasoning | ✅ Live (HTTP 200) | 16K | Cheap |
| xAI | grok-4.20 | — untested — | 2M | Expensive |
| Ollama/mac | qwen3:14b | ✅ Local | 16K | Free |
| Ollama/linux | qwen3-14b-128k | ✅ Local | 128K | Free |

> ⚠ **Breaking model rename (2026-05-25):** DeepSeek renamed `deepseek-reasoner-flash` → `deepseek-v4-flash`. Both config.yaml `fallback:` and provider model references must be updated or fallback silently fails.

### Kimi Status
- `sk-AkKwiEo3Xjaf09zQN6bozORJ4rLNUhijer48ecYKwf8is3pD` → **❌ 401 Invalid Authentication**
- Needs new key from https://platform.moonshot.cn

## Routing Rules (After Key Restoration)

Default chain: mac-ollama → linux-ollama → DeepSeek v4-flash → Grok-4.20 → Ring

Deliberate routing (when `/skill model-consulting` is loaded):
- Architecture/planning → Ring 2.6-1t (deliberate MERGE)
- Code generation → DeepSeek v4-flash (deliberate MERGE)
- Code review → DeepSeek v4-flash (CONSULT)
- Editorial/critique → Grok-4.20 (CONSULT)
- Parallel independent tasks → DELEGATE via subagents

## Config Fix Log

- 2026-05-25: Removed duplicate `fallback_providers: []` on line 57 of config.yaml that was silently wiping the entire fallback chain
- 2026-05-25: DeepSeek model names updated from `deepseek-reasoner-flash` → `deepseek-v4-flash`
- 2026-05-25: All 4 cloud API keys rotated and verified live
- 2026-05-25: Backup saved as config.yaml.bak.20260525_*