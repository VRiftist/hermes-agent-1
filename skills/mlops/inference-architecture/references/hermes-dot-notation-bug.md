# Hermes Config: Dot-Notation Provider Name Bug

## What happened

Running `hermes config set providers.ring-2.6-1t.api_key "sk-or-..."` created this broken YAML:

```yaml
providers:
  ring-2:
    6-1t:
      api_key: sk-or-...e220
```

The dot in the provider name (`ring-2.6-1t`) was interpreted as nested YAML keys by the CLI's dot-notation parser.

## How to fix

The CLI cannot safely write provider blocks with dots in names. Two options:

1. **Manual Python edit**:
   ```python
   import yaml
   with open("~/.hermes/config.yaml") as f:
       data = yaml.safe_load(f)
   data["providers"]["ring-2.6-1t"] = { ... }
   with open("~/.hermes/config.yaml", "w") as f:
       yaml.dump(data, f, default_flow_style=False, sort_keys=False)
   ```

2. **Add the block manually to config.yaml** then never touch it via CLI again.

## Prevention

- Avoid `hermes config set providers.<name-with-dots>.*` — always edit config.yaml directly for such providers.
- After any CLI edit of provider sections, verify the YAML structure before relying on it.