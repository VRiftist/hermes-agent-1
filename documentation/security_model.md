# ═══════════════════════════════════════════════════════════════
# HERMES SECURITY MODEL & SANDBOXING POLICY
# ═══════════════════════════════════════════════════════════════

## Threat Model
The agent operates with significant power: file I/O, network access,
code execution, SSH to remote machines, and API keys for cloud models.
This document defines the containment strategy.

## Capability Tiers

### Tier 1: SAFE (Always Available)
- Read files within ~/.hermes/
- Read project files (read-only, no mutation)
- Web search and content extraction (read-only)
- Memory palace read/write
- Logging and observability
- Telegram messaging (send only to configured channels)

### Tier 2: APPROVED (With Operator Confirmation)
- Write files to project directories
- Execute code in isolated subprocess
- SSH connections to Linux box
- Ollama model management (pull/start/stop)
- git operations (commit, push — no force push or branch delete)
- GitHub PR creation

### Tier 3: RESTRICTED (Explicit per-action Approval)
- Shell commands with network access
- File deletion (any location)
- npm/pip install global packages
- Modifying system configuration files
- Sending messages to new/different Telegram targets

### Tier 4: FORBIDDEN
- Executing arbitrary downloaded binaries
- Modifying ~/.hermes/config.yaml directly (must use hermes CLI)
- Sharing API keys in messages or logs
- Access to production infrastructure beyond defined hosts
- Running code as root/sudo

## Data Flow Rules

1. **PII Handling**: User may share PII in conversation. NEVER log PII in
   structured logs (use hashes). Never send PII to cloud model APIs unless
   explicitly approved per session.

2. **Key Management**: API keys stored in ~/.hermes/.env (protected).
   Never output full keys in logs or messages. Log only last 4 chars
   for debugging (e.g., sk-...c887).

3. **Network Isolation**: Cloud API calls go through direct HTTPS only.
   No proxy chains, no third-party relay of API keys.

4. **Sandboxed Execution**: All code execution runs in subprocess with:
   - Timeout: 120s default, 600s max
   - Working directory scoped to project root
   - No access to parent process environment (clean env)
   - Resource limits: 2GB RAM, 1 CPU core

## Audit Trail
- All Tier 2+ actions logged with: timestamp, operator approval, action type
- Approval evidence stored in ~/.hermes/logs/approvals.jsonl
- Health checks run every 5 minutes, results in ~/.hermes/logs/model_health.json

## Incident Response
If the agent attempts an unauthorized action:
1. Action is blocked
2. Incident logged to ~/.hermes/logs/incidents.jsonl
3. Operator notified via Telegram
4. Agent enters "safe mode" — Tier 1 only until operator review