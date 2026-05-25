# M2 32GB Context Window Bisection Results

Date: 2026-05-24
Hardware: Mac Mini M2, 32GB RAM
Model: qwen2.5-coder:32b-instruct-q4_K_M (Ollama, CPU inference)

## Test Results

| Context Length | Result |
|----------------|--------|
| 256K           | Not tested (model not configured) |
| 96K            | OOM — runner crashed, consumed 9GB+ |
| 64K            | Loads, responds to "Say hello", but runner becomes unstable |
| 48K            | NOT YET TESTED |
| 32K            | NOT YET TESTED |

## Chrome Impact

- Chrome with 20+ renderer processes: ~4.8GB
- After killing Chrome: ~2GB reclaimed, 9.5GB free
- Recommendation: kill Chrome before any inference session

## Pending Tests

Bisection path to find max stable window:
1. Test 48K context — if stable, try 56K
2. If 48K unstable, test 32K
3. Once stable point found, set config to 80% of that value

## Notes

- Metal acceleration suspected worse than CPU on M2 — stick with CPU
- Ollama runner processes need to be fully killed between tests (`pkill -f "ollama run*"`)
- `timeout` command not available on this Mac — use background process + wait pattern