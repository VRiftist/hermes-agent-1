# macOS User-Level sshd on Non-Standard Port (Updated 2026-05-24)

## Summary

The system sshd (`/System/Library/LaunchDaemons/ssh.plist`) cannot be used on macOS without SIP-disabled root access. Additionally, managed launchd plists (`~/Library/LaunchAgents/`) can fail silently — PID stays up but the plist doesn't auto-restart or bind correctly after reboot.

**Working pattern (session 2026-05-24):** Run sshd directly as a user-level process on a non-privileged port.

## Setup (Mac mini, macOS 25)

### 1. Generate host keys in user directory (SIP workaround)

macOS System Integrity Protection makes `/etc/ssh/` host keys root-owned and empty.
Generate user-level host keys instead:

```bash
mkdir -p ~/.ssh/server_keys
ssh-keygen -t ed25519 -f ~/.ssh/server_keys/ssh_host_ed25519_key -N "" -C "mac-mini-host"
ssh-keygen -t rsa -b 4096 -f ~/.ssh/server_keys/ssh_host_rsa_key -N "" -C "mac-mini-host"
```

### 2. Create custom sshd config

```bash
cat > ~/.ssh/sshd_config_mac << 'EOF'
Port 22222
ListenAddress 0.0.0.0
ListenAddress ::

HostKey ~/.ssh/server_keys/ssh_host_ed25519_key
HostKey ~/.ssh/server_keys/ssh_host_rsa_key

PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

UsePAM no
PidFile ~/.ssh/sshd.pid
EOF
```

### 3. Start sshd

```bash
/usr/sbin/sshd -f ~/.ssh/sshd_config_mac -D &
```

### 4. Verify

```bash
lsof -i :22222
ssh -p 22222 lumenhubai@127.0.0.1 "echo SSH WORKS"
```

### 5. Make it persistent (launchd plist — optional, tested unreliable)

The launchd approach below worked initially but stopped auto-restarting:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lumenhub.sshd</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/sbin/sshd</string>
        <string>-f</string>
        <string>/Users/lumenhubai/.ssh/sshd_config_mac</string>
        <string>-D</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/lumenhubai/.ssh/sshd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/lumenhubai/.ssh/sshd.error.log</string>
</dict>
</plist>
```

Install: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.lumenhub.sshd.plist`

> **⚠ Known issue:** launchd plist may load but sshd won't bind after reboot. Fall back to a userland startup script or `cron @reboot` entry if reliability is critical.

## Key Learnings (2026-05-24)

- **Port 2222 vs 22222:** Earlier configs used 2222 (from a launchd plist). Switched to 22222 for the user-level sshd to avoid privilege issues.
- **Host keys must be in user space:** SIP protects `/etc/ssh/` — host keys there are empty. `~/.ssh/server_keys/` works fine with a custom sshd config.
- **SSH key naming:** Use descriptive names like `linkey_linux` for cross-machine client keys. Avoid generic names like `id_ed25519` when managing multiple key pairs.
- **Password auth rejection from Linux:** When Linux rejects both pubkey and password, it usually means either the pubkey isn't in `authorized_keys` OR `PasswordAuthentication no` is set on the Linux side. Check `sshd_config` on Linux.