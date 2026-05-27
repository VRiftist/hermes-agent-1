# Agent Context — Preload for Every Session
> This file is loaded into every agent session as system-level context.
> Keeps the agent from asking questions it already knows the answer to.

## How to Use LumenHub
- You prefer terse, signal-dense answers over verbose explanations
- You delegate with "your call" but expect a clear recommendation + default option
- You correct once and expect the fix to stick permanently
- You use "baby"/"bro" ONLY for Gerald Hibbs — never others
- You are building a fork (hermes_lumenhub/) as a thin override layer

## Current Setup
- **Agent backend:** Hermes Agent (forked at ~/.hermes/hermes-agent)
- **Package structure:** hermes_lumenhub/skills/ contains preloaded skills
- **Gateway:** Running PID 64251, Telegram connected, heartbeat stable
- **30B model:** Active on both Linux .114 and macOS, Track 2 only
- **Devices:** macOS (primary dev), Linux .114 (deployment target), Termux (mobile)
- **Tauri desktop:** Barebones renderer, no IDE chrome yet (Phase 1)
- **VS Code extension:** Skeleton only

## Known Provider Behaviors
- **Kimi/Moonshot:** Primary key intermittently 401s under rate limit. NOT a bad key. Dual-rotation coded but needs second key to activate.
- **DeepSeek:** Intermittent timeouts. Circuit breaker should route to Claude fallback.
- **Claude/Anthropic:** Primary reasoning model. UNLIMITED budget. Stable.
- **OLLAMA (cloud):** Key format valid, live endpoint not yet tested from terminal. Local models work without key.
- **OpenRouter:** Catalog + routing. Stable.

## Key Preferences
- Quality gate: Advisory for 100 responses → auto-reject (OR B — pending Gerald final)
- Track 1: Autonomous code gen within QG thresholds
- Track 2: Board review chain with human sign-off on final
- Delegation scope: Auto-approve terminal commands in project dir + file writes

## Rejected Approaches (Don't Suggest These Again)
- Forking VS Code (Cursor space already occupied)
- SaaS model (offloads risk to user by design)
- Running 30B on Track 1 (reserved for Track 2 shadow review)
- Disabling context trimmer (causes memory poisoning — HARD INVARIANT)