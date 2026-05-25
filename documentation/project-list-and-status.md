# HERMES — PROJECT LIST & STATUS
# Date: 2026-05-25
# Author: Gerald Hibbs / Hermes Agent (co-authored)
# Context: Phase shift from BUILD → USE & TUNE
# Status key: ✅ Done | ⚠️ In Progress | ❌ Blocked | 🔲 Not Started

---

## PHASE: FOUNDATIONAL INFRASTRUCTURE (Mostly Complete)

### 1. Core Agent Stack
| Component | Status | Notes |
|-----------|--------|-------|
| `memory_palace.py` (SQLite) | ✅ Built, tested | 56→69KB, 18 episodes, 47 facts. Working. |
| `context_orchestrator.py` (6-tier trim) | ✅ Built, tested standalone | **NOT wired into gateway loop (P0)** |
| `model_routing.py` (task classification) | ✅ Built, tested | Keyword-based; needs confidence scoring |
| `circuit_breaker.py` (health monitoring) | ✅ Built | Dual-system problem with model_routing health |
| `consult_merge.py` (state machine) | ✅ Built | Full 3-hop paradigm implemented |
| `akashic_engine.py` (layered memory) | ✅ Built | Surface palace → episodic → semantic → working |
| `key_guardian.py` (daily key check) | ✅ Built, deployed | Makes real API calls (docs lie about this) |
| `night_council.py` (nightly review) | ✅ Built, cron active | 03:00 UTC, missing orchestrator integration |

### 2. Configuration & Security
| Component | Status | Notes |
|-----------|--------|-------|
| `config.yaml` (master config) | ✅ Fixed | Ghost fallback_providers line removed, env var refs |
| `.env` vault (keys) | ✅ 3/3 cloud keys | DeepSeek (new, live), xAI/Grok, OpenRouter. chmod 600 |
| `.env.template` | ✅ Created | Clean rotation template |
| `.gitignore` | ✅ Created | Excludes .env, logs, memory palace |
| Security model doc | ✅ Written | Tiered capability model (Safe→Approved→Restricted→Forbidden) |
| Key management strategy | ✅ Written | Centralized vault, 90-day rotation, emergency fallback |

### 3. Context Architecture
| Component | Status | Notes |
|-----------|--------|-------|
| `context-architect.md` (identity block) | ✅ Created, updated | Loads every session. Identity + powers + model chain + protocol |
| Foundational framework doc | ✅ 31KB canonical spec | 11 sections, 18 ratified decisions, decision log |
| Coherency audit | ✅ Completed | 30 issues found, 15 prioritized, logged to Palace |

---

## PHASE: CONNECTIVITY (Partially Blocked)

### 4. Model Chain — Cloud
| Model | Status | Context | Role | Verified |
|-------|--------|---------|------|----------|
| Mac: qwen3:14b | ✅ Live (local) | 16K | Default thinking | Ollama confirmed |
| Mac: qwen3-coder:30b-a3b | ⚠️ On disk, NOT in routing | 32K+ | Deep reasoning | 18.6GB, needs config entry |
| Linux: qwen3:8b | ❌ Offline | 16K | Fast fallback | Hetzner retired, DO pending |
| DeepSeek v4-flash | ✅ LIVE | 32K | Reasoning/code review | HTTP 200 ✅ |
| Grok-4.20-reasoning | ✅ LIVE | 16K | Creative synthesis | HTTP 200 ✅ |
| Ring-2.6-1t (OpenRouter) | ✅ LIVE | 262K | Quality gate | HTTP 200 ✅ |
| Kimi | ❌ No key | — | Cold standby | Awaiting key from Gerald |

### 5. Network/SSH
| Connection | Status | Notes |
|------------|--------|-------|
| SSH: Mac | ❌ Broken | SSH was enabled via launchctl but now unreachable |
| SSH: Linux | ❌ Offline | Hetzner retired, DO droplet not provisioned |
| Ollama: Mac (localhost) | ✅ Active | 7 models, ~45GB reclaimable |
| Ollama: Linux | ❌ Offline | Tied to server availability |

---

## PHASE: DOCUMENTATION & BOARD (Not Started / In Progress)

### 6. Enterprise Edition White Paper
| Item | Status | Notes |
|------|--------|-------|
| White paper (enterprise) | 🔲 Draft exists | Full board review needed |
| Kimi loop-in | ❌ Blocked | No key, no engagement yet |
| Full board review | 🔲 Not started | "Every feature, every menu, everything documented" |
| Assumption re-examination | ⚠️ Partially done | Coherency audit covered infrastructure; enterprise UX not yet |

### 7. Platform Strategy
| Platform | Priority | Status | Notes |
|----------|----------|--------|-------|
| **Mac** | P0 (HEAD UNIT) | ✅ Running | "Beautiful" — primary development environment |
| **Android** | P1 (phone) | 🔲 Not started | Gerald's mobile device |
| **Windows** | P2 (future) | 🔲 License available | Gerald has a Windows key for dev |
| **Linux** | ⚠️ Blocked | Offline | DO provisioning needed |

### 8. Quality Assurance (The "Flawless Pipeline")
| QA Component | Status | Notes |
|--------------|--------|-------|
| Integration tests (full pipeline) | ❌ Not created | Each module self-tests; no end-to-end |
| Metrics & methodology tracking | ❌ Not built | Gerald explicitly requested this |
| Review process (every turn) | ❌ Not built | "Every turn examination of issues" |
| Dead letter queue | ❌ Not created | Failed messages lost on crash |
| Backup / replay mechanism | ❌ Not created | Can't replay failed messages |

---

## PHASE: TUNING & OPTIMIZATION (Future)

### 9. Context Management Tuning
| Item | Status | Notes |
|------|--------|-------|
| Hybrid compression (T5) | 🔲 Described, not implemented | Framework doc done, code not |
| Model-specific tokenizers | 🔲 Not implemented | Using 0.25×char estimate (inaccurate) |
| Interrupt checkpoint | 🔲 Not implemented | No SIGINT/SIGTERM state dump |
| Adaptive budgets per model | ⚠️ Described | In framework doc; not in runtime config |

### 10. Monitoring & Alerting
| Item | Status | Notes |
|------|--------|-------|
| Telegram alerting | ❌ Non-functional | No token/chat_id in .env |
| Model health dashboard | ⚠️ Partial | Night Council generates JSON reports |
| Cost tracking | ⚠️ Partial | Night Council estimates, not real-time |
| PII redaction | ❌ Disabled | `redact_pii: false` in config |

---

## CRITICAL BLOCKERS

| # | Blocker | Unblocks | Priority |
|---|---------|----------|----------|
| 1 | Orchestrator not in gateway loop | All context management | P0 |
| 2 | Telegram alerts dead | Operator visibility | P0 |
| 3 | SSH to Mac broken | Cross-platform dev, Linux provisioning | P0 |
| 4 | Dual health tracking systems | Reliable failover | P0 |
| 5 | Linux offline (DO pending) | 8B fallback, long-context local | P1 |
| 6 | Kimi key missing | Enterprise option, cold standby activation | P1 |
| 7 | qwen3-coder:30b-a3b not in routing | Complete model chain | P1 |
| 8 | No integration tests | Confidence in connected system | P2 |
| 9 | No metrics/tracking methodology | "Using and tuning" phase | P2 |
| 10| No review/audit process per turn | Gerald's "every turn" requirement | P2 |