#!/bin/bash
# ~/.hermes/launch-terminal.sh
# Waits for the Hermes gateway to be ready, then opens a Terminal window

# Wait for launchd to fully settle
sleep 3

# Wait for gateway process to be running
for i in {1..30}; do
  if pgrep -f "hermes.*gateway.*run" > /dev/null 2>&1; then
    echo "Gateway is up, launching Terminal..."
    break
  fi
  sleep 1
done

# If gateway still not up after waiting, warn but continue
if ! pgrep -f "hermes.*gateway.*run" > /dev/null 2>&1; then
  echo "WARNING: Gateway not detected, still launching Terminal..."
fi

# Open Terminal with Hermes interactive CLI
# Use osascript to spawn a new Terminal tab/window
osascript <<'SCRIPT'
tell application "Terminal"
  activate
  do script "/Users/lumenhubai/.local/bin/hermes chat --inference-model ollama"
end tell
SCRIPT