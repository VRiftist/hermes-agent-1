# config.yaml API Key Injection Issues (2026-05-24)

## Problem

Automated key updates via `sed` / `perl` on `config.yaml` repeatedly corrupted API key values, particularly for DeepSeek.

## Root Cause

1. **Shell escaping**: Keys containing special characters (`=`, `_`, mixed case) interact badly with sed regex delimiters.
2. **Credential store interference**: The `redact_secrets` feature in the gateway may intercept writes to known credential patterns, truncating values.
3. **YAML structure breakage**: Using `hermes config set providers.<name>.api_key` for provider names containing dots/hyphens creates broken nested YAML blocks (see `hermes-dot-notation-bug.md`).

## What Failed

- `perl -pi -e 's/.../.../' config.yaml` — truncated DeepSeek key to `sk-e96...1b7e`
- `sed -i` patterns — mangled case or dropped trailing characters
- `hermes config set` — caused dot-notation nesting bugs

## Correct Approach

### Method 1: Python yaml library (recommended)

```python
import yaml, os
os.chdir(os.path.expanduser('~/.hermes'))

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['providers']['deepseek']['api_key'] = 'sk-xxxxxxxxxxxxxxxxxxxx'

with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

### Method 2: Direct file write with exact string replacement

```python
with open('config.yaml', 'r') as f:
    content = f.read()
content = content.replace('OLD_EXACT_VALUE', 'NEW_EXACT_VALUE')
with open('config.yaml', 'w') as f:
    f.write(content)
```

### Method 3: Write keys to `keys.txt` instead

Format: `PROVIDER_API_KEY=<value>`

## Lessons Learned

- **Never use sed/perl for credential values** in config files — shell escaping is unreliable.
- **Always verify** with a raw byte-level read after programmatic edits: `python3 -c "open('config.yaml','rb').read()"`
- **Validate YAML** after every edit: `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"`
- Stripe/sed on credential fields is the #1 cause of corrupted provider configs.