# Remote Ollama Networking & Port Conflicts

## Problem Pattern
Multiple Ollama instances on a single Linux box can silently conflict — one binds to `127.0.0.1` only (systemd service), another to `0.0.0.0` (userland process). A remote Mac client sees "connection refused" even though the systemd Ollama is running.

## Diagnosis Steps

1. **Check what's listening on the Ollama port(s):**
   ```bash
   ss -tlnp | grep -E '1143[0-9]'
   ```
   Expected: `LISTEN ... 127.0.0.1:11434 ... ollama` (systemd) and `LISTEN ... 0.0.0.0:11435 ... ollama` (userland)

2. **Identify userland vs systemd:**
   ```bash
   ps aux | grep -E 'ollama' --color
   systemctl status ollama
   ```

3. **Verify from Mac:**
   ```bash
   ssh -N -L 11435:127.0.0.1:11435 gerald@192.168.1.230 &
   curl http://127.0.0.1:11435/api/tags | python3 -m json.tool
   ```

## Resolution

### Option A: Use userland port directly (simplest)
```yaml
providers:
  linux:
    type: ollama
    base_url: http://192.168.1.230:11435/v1
```

### Option B: Mask systemd Ollama, use userland only
```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo systemctl mask ollama
```

### Option C: SSH tunnel (most secure)
Add to `~/.ssh/config` on Mac:
```
Host latin
  HostName 192.168.1.230
  User gerald
  LocalForward 11435 127.0.0.1:11435
```
Then set `base_url: http://127.0.0.1:11435/v1` in config.

## Key Insight
- Port 11434 = systemd default, binds localhost only (unreachable from LAN)
- Port 11435 = userland default, binds 0.0.0.0 (LAN accessible)
- Always verify with `ss -tlnp` before assuming a port is reachable