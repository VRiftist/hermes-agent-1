#!/bin/bash
# setup-bidirectional-ssh.sh
# Sets up bidirectional SSH between Mac (lumenhubai) and Linux (gerald@192.168.1.230)
# Usage: ./setup-bidirectional-ssh.sh [linux-host] [linux-user]
#
# This script is intended to run on the Mac. It:
# 1. Installs Mac pubkey on Linux authorized_keys
# 2. Installs Linux pubkey on Mac authorized_keys
# 3. Creates/updates Linux ~/.ssh/config with mac-mini alias
# 4. Updates Mac ~/.ssh/config with ForwardAgent

set -euo pipefail

LINUX_HOST="${1:-192.168.1.230}"
LINUX_USER="${2:-gerald}"
LINUX_ALIAS="linux"
MAC_ALIAS="mac-mini"
KEY_FILE="${HOME}/.ssh/lumenhub"
MAC_SSH_CONFIG="${HOME}/.ssh/config"
MAC_PUBKEY=$(cat "${KEY_FILE}.pub")

echo "=== Bidirectional SSH Setup ==="
echo "Mac user: $(whoami)"
echo "Linux target: ${LINUX_USER}@${LINUX_HOST}"
echo ""

# --- Step 1: Ensure key exists ---
if [ ! -f "${KEY_FILE}.pub" ]; then
    echo "ERROR: No pubkey found at ${KEY_FILE}.pub"
    echo "Generate one: ssh-keygen -t ed25519 -f ${KEY_FILE} -C \"lumenhub-mac-mini\""
    exit 1
fi
echo "[✓] ED25519 key found: $(ssh-keygen -lf "${KEY_FILE}")"

# --- Step 2: Install Mac pubkey on Linux ---
echo ""
echo "--- Installing Mac pubkey on Linux ---"
scp -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    "${KEY_FILE}.pub" "${LINUX_USER}@${LINUX_HOST}:/tmp/lumenhub_mac.pub"

ssh -o BatchMode=yes "${LINUX_USER}@${LINUX_HOST}" \
    "mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
     grep -qF '$(echo "${MAC_PUBKEY}" | sed 's/ /\\ /g')' ~/.ssh/authorized_keys 2>/dev/null || \
     cat /tmp/lumenhub_mac.pub >> ~/.ssh/authorized_keys && \
     chmod 600 ~/.ssh/authorized_keys && rm /tmp/lumenhub_mac.pub && \
     sort -u ~/.ssh/authorized_keys > /tmp/ak_tmp && mv /tmp/ak_tmp ~/.ssh/authorized_keys"
echo "[✓] Mac pubkey installed on Linux"

# --- Step 3: Install Linux pubkey on Mac ---
echo ""
echo "--- Installing Linux pubkey on Mac ---"
LINUX_PUBKEY=$(ssh -o BatchMode=yes "${LINUX_USER}@${LINUX_HOST}" "cat ~/.ssh/id_ed25519.pub")
if [ -n "${LINUX_PUBKEY}" ]; then
    if ! grep -qF "${LINUX_PUBKEY}" "${HOME}/.ssh/authorized_keys" 2>/dev/null; then
        echo "${LINUX_PUBKEY}" >> "${HOME}/.ssh/authorized_keys"
        chmod 600 "${HOME}/.ssh/authorized_keys"
        echo "[✓] Linux pubkey added to Mac authorized_keys"
    else
        echo "[✓] Linux pubkey already in Mac authorized_keys"
    fi
fi

# Deduplicate
sort -u "${HOME}/.ssh/authorized_keys" > /tmp/ak_tmp && mv /tmp/ak_tmp "${HOME}/.ssh/authorized_keys"
chmod 600 "${HOME}/.ssh/authorized_keys"

# --- Step 4: Update Mac SSH config ---
echo ""
echo "--- Updating Mac SSH config ---"
cat > "${MAC_SSH_CONFIG}" << EOF
Host ${LINUX_ALIAS}
    HostName ${LINUX_HOST}
    User ${LINUX_USER}
    IdentityFile ${KEY_FILE}
    ForwardAgent yes

Host ${MAC_ALIAS}
    HostName 127.0.0.1
    User $(whoami)
    Port 2222
    IdentityFile ${KEY_FILE}
    ForwardAgent yes
EOF
chmod 600 "${MAC_SSH_CONFIG}"
echo "[✓] Mac SSH config updated"

# --- Step 5: Create Linux SSH config ---
echo ""
echo "--- Updating Linux SSH config ---"
cat > /tmp/linux_ssh_config << EOF
Host ${LINUX_ALIAS}
    HostName 127.0.0.1
    User ${LINUX_USER}
    IdentityFile ~/.ssh/lumenhub
    ForwardAgent yes

Host ${MAC_ALIAS}
    HostName ${LINUX_HOST}
    Port 2222
    User $(whoami)
    ForwardAgent yes
EOF

scp -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    /tmp/linux_ssh_config "${LINUX_USER}@${LINUX_HOST}:~/.ssh/config.new"
ssh -o BatchMode=yes "${LINUX_USER}@${LINUX_HOST}" \
    "mv ~/.ssh/config.new ~/.ssh/config && chmod 600 ~/.ssh/config"
echo "[✓] Linux SSH config updated"

# --- Step 6: Test connections ---
echo ""
echo "=== Testing Connections ==="

echo ""
echo "Test 1: Mac → Linux"
ssh -o BatchMode=yes -o ConnectTimeout=5 "${LINUX_ALIAS}" "echo 'PASS'; hostname; whoami"

echo ""
echo "Test 2: Linux → Mac"
ssh -o BatchMode=yes -o ConnectTimeout=5 "${LINUX_ALIAS}" \
    "ssh -o BatchMode=yes -o ConnectTimeout=5 '${MAC_ALIAS}' 'echo PASS; hostname; whoami'"

echo ""
echo "Test 3: Mac → Mac (via ${MAC_ALIAS})"
ssh -o BatchMode=yes -o ConnectTimeout=5 "${MAC_ALIAS}" "echo 'PASS'; hostname"

echo ""
echo "=== All done! ==="