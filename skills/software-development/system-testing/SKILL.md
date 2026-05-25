---
name: system-testing
category: software-development
description: Hermes Agent full-stack test suite — 9-module self-test, CI patterns, known failure modes, and sandbox-specific workarounds.
tags:
  - "testing"
  - "self-test"
  - "CI"
  - "validation"
  - "sandbox"
  - "modules"
version: "1.1.0"
updated: "2026-05-25T20:00"
related_skills:
  - hermes-infrastructure
  - context-trimming
  - key-management
  - hermes-gateway-ops
references:
  - references/full-selftest-results.md
  - references/sandbox-environment-notes.md
  - references/2026-05-25-10of10-results.md
---

# System Testing — Hermes Agent Full-Stack Test Suite

## Test Suite Location

`scripts/full_selftest.py` — runs all 9 core modules in sequence. Executes in a sandboxed environment that differs from the live runtime in several important ways.

## Modules Tested

1. **Task Classification** (`model_routing.py`) — 7/7 patterns pass
2. **Model Selection** (`model_routing.py`) — Category routing works; Kimi selected for creative ✅
3. **Context Orchestrator** (`context_orchestrator.py`) — 3/3 phases, `get_context()` works ✅
4. **Memory Palace** (`memory_palace.py`) — Store/recall functional ✅
5. **Kimi Client** (`kimi_client.py`) — Keys loaded, retry config correct ✅
6. **Key Guardian** (`key_guardian.py`) — Env var loading works ✅
7. **Gateway Integration** (`gateway_integration.py`) — Lifecycle functions callable ✅
8. **Circuit Breaker** (`circuit_breaker.py`) — Health reporting works ✅
9. **Night Council** (`night_council.py`) — Maintenance runs ✅ (returns `None`, not dict — by design)

## Known Sandbox-Only Failures

These failures occur in the sandbox environment only and do NOT indicate real bugs:

| Failure | Cause | Workaround |
|---------|-------|------------|
| `sudo` blocked | Sandbox restricts privilege escalation | Run `sudo systemsetup -setremotelogin on` in your terminal |
| `.env` reads as empty | Sandbox env vars not inherited | Keys are on disk; validated in live runs |
| Night Council `run()` returns `None` | Function prints report to stdout, returns nothing | Normal behavior — check printed output, not return value |
| `report_health` signature mismatch | Test used old 3-param signature | Fixed in `full_selftest.py` — now matches updated `report_health(key, model_name, success, latency_ms)` |

## Bugs Found During Testing

### 1. `circuit_breaker.py` — `report_health` signature (FIXED)
- **Problem:** Added `model_name` parameter but test still used old 3-arg call
- **Fix:** Updated signature to `report_health(model_key, model_name, success, latency_ms=0)`
- **Impact:** All code calling `report_health` must pass `model_name` (use `None` if unknown)

### 2. `model_routing.py` — Review misclassification (FIXED)
- **Problem:** "Review this code for bugs" → `code_generation` (should be `review`)
- **Fix:** Added multi-word pattern matching with 2x weight in `classify_task()`
- **Impact:** Review tasks now correctly route to Ring/quality-gate models

### 3. `model_routing.py` — Sort key removed (FIXED)
- **Problem:** Removing `sort_key` variable caused crash in `select_model()`
- **Fix:** Replaced with inline lambda that prioritizes category-match → local → cheapest
- **Impact:** Kimi now correctly prioritized for creative tasks over local fallback

### 4. `night_council.py` — Malformed health JSON crash (FIXED)
- **Problem:** `analyze_model_health()` crashed on non-dict entries in health file
- **Fix:** Added `isinstance(status, dict)` guard
- **Impact:** Gracefully handles corrupted/stale `model_health.json`

## Running the Suite

```bash
cd ~/.hermes
python3 scripts/full_selftest.py
```

Expected: all 9 modules print ✅, no traceback in stderr.

## Loading This Skill

```
/skill system-testing
```

Load before running or modifying the test suite.