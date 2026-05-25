# Linux sshd & Remote Ollama — Session Reference

**Date:** 2026-05-24
**Context:** Hermes agent with Linux box as remote Ollama provider

## The Problem

Linux box at 192.168.1.230 (user gerald) had sshd stopped. Hermes config pointed an ollama provider at it, but without sshd running the provider was unreachable — broke the entire fallback chain.

## Key Lesson

**You cannot start sshd remotely via SSH if sshd is stopped.** Requires physical/console access, existing working SSH session, or remote management (iDRAC, IPMI, cloud console).

## Resolution Steps (user performs on Linux box)

```bash
sudo systemctl start sshd
sudo systemctl enable sshd
sudo firewall-cmd --add-service=ssh --permanent && sudo firewall-cmd --reload
sudo systemctl start ollama
sudo systemctl enable ollama
```

Verify from Mac:
```bash
ssh linux "echo SSH_OK && hostname && systemctl is-active ollama"
curl -s http://192.168.1.230:11435/api/tags | python3 -m json.tool
```

**NOTE (2026-05-24):** The Linux box has two Ollama listeners — port 11434 (localhost-only via systemd) and port 11435 (all interfaces, userland). The Ollama watchdog script (`~/ai-team-shared/scripts/ollama-watchdog.sh`) starts a process on 11435 that's reachable from other machines. Port 11434 only accepts connections from localhost.

**Mac ssh-agent fix:** If SSH fails with "Permission denied" despite keys existing, the ssh-agent may have no loaded identities. Fix: `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/lumenhub`. If the key file is `~/.ssh/lumenhub_mac` instead, use that path.

## Mac SSH Daemon

Mac SSH enabled via launchd agent on port 2222:
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.lumenhub.sshd.plist
```

Allows Linux box to SSH back into Mac via `ssh mac-mini`.

## Hermes Config Impact

The `providers.linux` block only works when both sshd and ollama are running on the Linux box. If either is down, Hermes silently falls through to the next provider in the fallback chain.