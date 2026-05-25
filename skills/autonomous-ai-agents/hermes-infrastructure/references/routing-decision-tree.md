# Routing Decision Tree (2026-05-25)

Definitive decision logic for Hermes model routing. Used by `model_routing.py` and by the operator when choosing models manually.

## Decision Tree

```
TASK INCOMING
    │
    ├─ Token count < 200 output tokens needed?
    │   └─ YES → qwen3:8b (mac-ollama), simplest path, no consult
    │
    ├─ Requires FILE SYSTEM ACCESS or TOOL USE?
    │   └─ YES → qwen3:14b (mac-ollama), local, all tools available
    │
    ├─ Requires CODE GENERATION?
    │   ├─ Simple/moderate → qwen3:14b (mac-ollama), fast + capable
    │   └─ Complex/needs review → deepseek-v4-flash (CONSULT pattern)
    │       └─ After review → qwen3:14b generates final code
    │
    ├─ Requires DEEP REASONING (>3 hops of logic)?
    │   │
    │   ├─ Context fits 32K → deepseek-v4-flash ($0.14/M, strong reasoner)
    │   ├─ Needs burst creativity/architectural → grok-4.20-reasoning ($1.25/M)
    │   └─ Needs longest coherent chain → qwen3-14b-128k (linux, 128K, free)
    │
    ├─ ARCHITECTURE or SYSTEM DESIGN?
    │   └─ grok-4.20-reasoning (best at structural thinking, then ALWAYS ring QC)
    │
    ├─ RESEARCH / LONG DOCUMENT?
    │   └─ qwen3-14b-128k (linux, 128K, free, fits the most)
    │       └─ If needs semantic extraction → deepseek-v4-flash (cheapest cloud)
    │
    ├─ EDITORIAL REVIEW / CRITIQUE?
    │   └─ Athena persona → deepseek-v4-pro or ring-2.6-1t
    │
    └─ FINAL VERIFICATION / QUALITY GATE?
        └─ ring-2.6-1t (always the FINAL model before delivery)
```

## Model Selection Criteria Matrix

| Criterion | Best First Choice | Second Choice |
|-----------|-------------------|---------------|
| Cost optimization (free) | mac-ollama (any model) | linux-ollama (any model) |
| Context window size | qwen3-14b-128k (128K) | deepseek-v4-flash (32K) |
| Reasoning quality | grok-4.20-reasoning | ring-2.6-1t |
| Code generation | qwen3:14b (local) | deepseek-v4-flash |
| Code review | deepseek-v4-flash | grok-4.20-reasoning |
| Creative writing | grok-4.20-reasoning | qwen3:14b |
| Crunching (structured data) | qwen3:8b or qwen3:14b (local) | — |
| Long document analysis | qwen3-14b-128k | grok-4.20-reasoning |

## Priority Rules When Multiple Models Qualify

1. Free before paid (if local model is adequate)
2. Smaller context model if conversation fits (save context budget)
3. Different provider for resilience on critical tasks
4. Always end sequence with ring-2.6-1t for quality gate on important outputs

## Cost Budget Rules
- Default daily budget: $5.00
- Warning at 80% ($4.00)
- Hard stop at 100% ($5.00) — unless operator overrides
- Monthly ceiling: $100.00
- Free models (Ollama) exempt from budget calculations