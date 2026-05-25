# Hermes Knowledge Base — Index

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
