# Gateway Restart & Config Safety Notes (2026-05-25)

## Process Detection
Gateway: `hermes gateway run --replace` (PID 9457)
Agent: PID 10436

Port 9090 may not respond even when the process is alive.

## Stale model.api_key Gotcha
When switching `model.provider`, the old `model.api_key` field may persist in config.yaml. Delete it if it belongs to a different provider. The provider block under `providers:<name>.api_key` is authoritative.

## keys.txt Hygiene
- `chmod 600 ~/.hermes/keys.txt`
- Format: `PROVIDER_API_KEY=<value>`
- Never store keys in config.yaml outside the credential store

## Dot-notation Bug (historical)
Using `hermes config set providers.ring-2.6-1t.api_key` created a nested `ring-2 → 6-1t` YAML block. Fix via Python yaml library. Prefer Python over CLI for provider names with dots/hyphens.