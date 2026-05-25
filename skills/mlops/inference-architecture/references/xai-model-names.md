# xAI API — Model Names & Pricing (2026-05-24)

## Valid Model Names (confirmed via live API test)

| Model Name | HTTP Status | Notes |
|---|---|---|
| `grok-4.20` | 200 | 2M ctx, $0.00125/M in, $0.0025/M out |
| `grok-3-mini` | 200 | 128K ctx, ~$0.10/M in — **chosen for 3rd tier** |
| `grok-2-mini` | 400 | Does not exist |
| `grok3-mini` | 400 | Wrong format (no hyphen) |
| `grok-4-mini` | 400 | Does not exist |

## Rule
xAI model names are hyphenated: `grok-3-mini`, `grok-4.20`.
Always validate with a live curl before adding to config.

See: `inference-architecture` SKILL.md → "Why grok-3-mini over grok-4.20"