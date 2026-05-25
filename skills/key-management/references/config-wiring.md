# Config-YAML Key Wiring Reference

## Problem
`config.yaml` contains hardcoded API keys in plain text. These need to be replaced with `${ENV_VAR}` references so the actual secrets live only in `.env` (chmod 600, gitignored).

## Key Patterns to Replace

| Provider | Prefix pattern | Env var |
|----------|---------------|---------|
| OpenRouter | `sk-or-v1-` + hex | `${OPENROUTER_KEY_1}` |
| DeepSeek | `sk-8ead` + hex | `${DEEPSEEK_API_KEY}` |
| xAI/Grok | `xai-ZC` + alphanumeric | `${XAI_API_KEY}` |

## Replacement Script (Python)

Full key hashes may appear in `config.yaml` — use prefix-based regex, not ellipsis placeholders:

```python
import re

config_path = "/Users/lumenhubai/.hermes/config.yaml"
with open(config_path) as f:
    lines = f.readlines()

replacements = {
    re.compile(r'api_key:\s*sk-or-[a-z0-9-]+'): 'api_key: ${OPENROUTER_KEY_1}',
    re.compile(r'api_key:\s*sk-8ead[a-f0-9]+'): 'api_key: ${DEEPSEEK_API_KEY}',
    re.compile(r'api_key:\s*xai-Z[A-Za-z0-9]+'): 'api_key: ${XAI_API_KEY}',
}

for i, line in enumerate(lines):
    for pattern, replacement in replacements.items():
        if pattern.search(line):
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + replacement + '\n'

with open(config_path, 'w') as f:
    f.writelines(lines)
```

## Gotchas

- Keys may appear multiple times in config (top-level `api_key:` + per-provider `api_key:`)
- Ollama providers use literal `"Ollama"` — do NOT replace those
- Lines with `"${..."` are already correct — skip them
- After patching, verify with: `grep -n 'api_key' config.yaml | grep -v 'Ollama' | grep -v '\${'` — should return nothing