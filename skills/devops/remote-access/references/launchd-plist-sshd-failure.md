# macOS User-Level sshd: Why launchd Failed (2026-05-24)

## Problem

A `~/Library/LaunchAgents/com.lumenhub.sshd.plist` was created to auto-start sshd on boot, but it silently failed after reboot — the process appeared loaded but never bound to port 22222.

## Root Cause (Likely)

macOS launchd with user-level (gui/) agents can fail to run processes that need network binding privileges below port 1024. While port 22222 is above that threshold, launchd agents in gui sessions may not have the correct sandbox entitlements or may load before the network stack is ready.

## What Was Tested

1. Created plist at `~/Library/LaunchAgents/com.lumenhub.sshd.plist`
2. Bootstrapped: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.lumenhub.sshd.plist`
3. `launchctl list` showed the PID
4. `lsof -i :22222` showed **nothing** — no binding
5. After reboot, same result: PID existed but port not listening

## Working Alternative

Start sshd directly from a persistent tmux/screen session or background process:

```bash
/usr/sbin/sshd -f ~/.ssh/sshd_config_mac -D &
```

To make this survive terminal logout, wrap in a startup script or use a launchd plist that runs at login via the loginwindow session (not gui/).

## Lessons

- Don't trust `launchctl list` output showing a PID as proof the service is functional
- Always verify with `lsof -i :<port>` or `ss -tlnp`
- User-level launchd agents on macOS are unreliable for daemon processes — prefer direct execution or full launchd plists in `/Library/LaunchDaemons/` (which require root)