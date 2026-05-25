# Connectivity Test Matrix — Mac ↔ Linux

## Current Status (2026-05-24)

| Test | Command | Status | Notes |
|------|---------|--------|-------|
| Mac→Linux SSH | `ssh gerald@192.168.1.230` | ❌ FAIL | Permission denied (publickey). No authorized_keys for lumenhubai |
| Linux→Mac SSH | `ssh lumenhubai@192.168.1.240` | ❌ UNKNOWN | Mac sshd status unknown (launchctl?) |
| Mac Ollama direct | `curl localhost:11434/api/tags` | ✅ LIVE | qwen3:14b + qwen2.5-coder:32b confirmed |
| Linux Ollama via SSH tunnel | `ssh gerald@192.168.1.230 curl localhost:11435/api/tags` | ✅ LIVE | qwen3:14b confirmed on port 11435 |
| Telegram | Gateway reconnect | ⚠️ BLOCKED | Token 401 — need new token from @BotFather |
| Discord | Gateway reconnect | ❌ DISABLED | User said "don't use discord" |
| OpenRouter (Ring) | Cloud fallback | ✅ CONFIGURED | Key injected in config.yaml |
| DeepSeek | Cloud fallback | ✅ CONFIGURED | Key injected in config.yaml |

## SSH Fix Checklist

### On Linux (192.168.1.230):
```bash
# 1. Ensure sshd is running
sudo systemctl start sshd
sudo systemctl enable sshd

# 2. Allow key auth (should be default)
sudo grep -q "PubkeyAuthentication yes" /etc/ssh/sshd_config || echo "PubkeyAuthentication yes" | sudo tee -a /etc/ssh/sshd_config
sudo systemctl restart sshd

# 3. Add Mac's public key to authorized_keys
# (from Mac, do this step)
```

### On Mac:
```bash
# 1. Generate ED25519 key if missing
ssh-keygen -t ed25519 -f ~/.ssh/lumenhub -C "lumenhub-mac-mini"

# 2. Copy to Linux
ssh-copy-id -i ~/.ssh/lumenhub.pub gerald@192.168.1.230

# 3. Add to SSH config
cat >> ~/.ssh/config << 'EOF'

Host linux
    HostName 192.168.1.230
    User gerald
    IdentityFile ~/.ssh/lumenhub
    ForwardAgent yes
EOF

# 4. Test
ssh linux "echo OK && hostname"
```