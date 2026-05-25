#!/bin/bash
LOG=/tmp/tunnel.log
if ! lsof -i :11435 >/dev/null 2>&1; then
  ssh -f -N -i /Users/lumenhubai/.ssh/linkey_linux \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -L 11435:127.0.0.1:11434 \
    gerald@192.168.1.230 -p 22
  echo "$(date): tunnel reconnected" >> "$LOG"
fi