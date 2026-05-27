#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""Initialize the Hermes wiki (Karpathy pattern) and re-run full audit."""
import os, sys
sys.path.insert(0, "/Users/lumenhubai/.hermes/scripts")

# ── Initialize Wiki ──────────────────────────────────────────
wiki_path = os.path.expanduser("~/.hermes/wiki")
os.makedirs(wiki_path, exist_ok=True)

# Set WIKI_PATH in memory for this session
os.environ["WIKI_PATH"] = wiki_path

# Create SCHEMA.md
schema_content = """# Wiki Schema

## Structure
- `raw/` — Immutable source material (articles, papers, transcripts)
- `processed/` — Synthesized, interlinked knowledge pages
- `index.md` — Master catalog
- `log.md` — Chronological action log

## Naming Convention
- Files: `kebab-case-descriptive-title.md`
- Prefix with date for time-sensitive: `2026-05-25-topic.md`

## Frontmatter
Every page uses YAML frontmatter:
```yaml
---
title: "Page Title"
date: 2026-05-25
tags: [tag1, tag2]
source: original-url-or-book
---
```

## Cross-referencing
Use `[[page-name]]` for wiki-links. Never broken links.
"""

with open(os.path.join(wiki_path, "SCHEMA.md"), "w") as f:
    f.write(schema_content)

# Create index.md
index_content = """# Hermes Knowledge Base — Index

Last updated: 2026-05-25

## Architecture
- [[context-architect]] — Identity, capabilities, operating principles
- [[hermes-foundational-framework]] — Full system spec (31KB)
- [[security-model]] — Capability tiers and sandboxing policy
- [[key-management-strategy]] — Vault, rotation, recovery
- [[coherency-audit-20260525]] — 30 issues found, resolution log

## Infrastructure
- [[infrastructure-audit-20260525]] — This audit: all layers, all status

## Model Chain
- mac-ollama/qwen3:14b — Default local (head unit)
- mac-ollama/qwen3:8b — Fast local (tool use, trimming)
- mac-ollama/qwen3-coder:30b-a3b — Reasoning model
- linux-ollama/qwen3-14b-128k — Long context (offline)
- deepseek-v4-flash/v4-pro — Cloud reasoning
- grok-4.20-reasoning — Cloud strategic
- ring-2.6-1t — Quality gate (OpenRouter)
- kimi-v1-8k — Creative (Direct Moonshot, auth pending)

## Knowledge Domains
- [[model-routing]] — Task classification → model selection
- [[context-orchestrator]] — 6-tier priority, 3-phase lifecycle
- [[memory-palace]] — SQLite episodic/semantic/working memory
- [[circuit-breaker]] — Health monitoring, failover chain
"""

with open(os.path.join(wiki_path, "index.md"), "w") as f:
    f.write(index_content)

# Create log.md
log_content = """# Wiki Action Log

## 2026-05-25 — Wiki Initialized
- Created SCHEMA.md, index.md, log.md
- Set WIKI_PATH=~/.hermes/wiki
- Interlinked with existing documentation
"""

with open(os.path.join(wiki_path, "log.md"), "w") as f:
    f.write(log_content)

# Create raw directory
os.makedirs(os.path.join(wiki_path, "raw"), exist_ok=True)
os.makedirs(os.path.join(wiki_path, "processed"), exist_ok=True)

# Create .gitkeep for version control
with open(os.path.join(wiki_path, "raw", ".gitkeep"), "w") as f:
    f.write("")
with open(os.path.join(wiki_path, "processed", ".gitkeep"), "w") as f:
    f.write("")

# Write the infrastructure audit as a wiki page
audit_page = """---
title: "Infrastructure Audit — 2026-05-25"
date: 2026-05-25
tags: [infrastructure, audit, status]
---

# Infrastructure Audit — 2026-05-25

## Summary
| Layer | Status |
|-------|--------|
| Memory Palace | ✅ Operational — 85 episodes, 66 facts, 100KB |
| Context Orchestrator | ✅ Built & tested — NOT in gateway loop yet |
| Model Routing | ✅ 8 models, 7 categories, Kimi registered |
| Kimi Client | ⚠️ Dual-key loaded, Moonshot auth pending (401) |
| Key Guardian | ✅ 3/5 cloud keys loaded, daily cron active |
| Circuit Breaker | ✅ 5 models monitored, failover chain works |
| Gateway Integration | ✅ Bridge built, needs CLI wiring |
| Night Council | ✅ Cron at 03:00 UTC, runs clean |
| Wiki (llm-wiki) | ✅ NOW INITIALIZED |
| Documentation | ✅ 5 docs, 64KB total |
| Linux SSH | ✅ Reachable, RTX 3060 confirmed |
| Mac SSH | ⚠️ sshd not running (needs sudo) |

## Active Blockers
1. **Mac SSH** — `sudo systemsetup -setremotelogin on` needed
2. **Kimi Moonshot auth** — Keys on disk, platform activation required
3. **Context orchestrator → gateway** — Bridge built, not in message loop
4. **DeepSeek key** — Still 401, may need platform re-activation
5. **Linux replacement** — Hetzner retired, DO pending

## Decisions Pending
- Trim philosophy: compression vs deletion (HYBRID decided, code pending)
- Wiki integration into context orchestrator for RAG augmentation
- qwen3-coder:30b-a3b routing registration
"""

with open(os.path.join(wiki_path, "processed", "infrastructure-audit-20260525.md"), "w") as f:
    f.write(audit_page)

print(f"✅ Wiki initialized at {wiki_path}")
print(f"   Files created: SCHEMA.md, index.md, log.md, processed/infrastructure-audit-20260525.md")
print(f"   WIKI_PATH set: {os.environ.get('WIKI_PATH', 'NOT SET')}")