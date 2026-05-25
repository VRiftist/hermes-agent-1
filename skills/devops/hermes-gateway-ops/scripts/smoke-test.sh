#!/usr/bin/env bash
# Smoke test script for Hermes gateway — run after any config change or restart

set -euo pipefail

echo "=== Hermes Gateway Smoke Test ==="
echo "Timestamp: $(date -Iseconds)"

# 1. Check .env is readable
echo -n "[1/6] .env file readable... "
if [ -r "$HOME/.hermes/.env" ]; then
    echo "OK ($(wc -l < "$HOME/.hermes/.env") lines)"
else
    echo "FAIL — cannot read $HOME/.hermes/.env"
    exit 1
fi

# 2. Check TELEGRAM_BOT_TOKEN is set in .env
echo -n "[2/6] TELEGRAM_BOT_TOKEN in .env... "
if grep -q "^TELEGRAM_BOT_TOKEN=" "$HOME/.hermes/.env"; then
    echo "OK"
else
    echo "FAIL — TELEGRAM_BOT_TOKEN not found in .env"
    exit 1
fi

# 3. Check gateway process is running
echo -n "[3/6] Gateway process running... "
if pgrep -f "hermes.*gateway.*run" > /dev/null 2>&1; then
    echo "OK (PID $(pgrep -f 'hermes.*gateway.*run' | head -1))"
else
    echo "FAIL — no gateway process found"
    exit 1
fi

# 4. Check gateway log exists and is recent
echo -n "[4/6] Gateway log recent... "
LOGFILE="$HOME/.hermes/logs/gateway.log"
if [ -f "$LOGFILE" ]; then
    AGE_SECONDS=$(( $(date +%s) - $(stat -f %m "$LOGFILE" 2>/dev/null || stat -c %Y "$LOGFILE" 2>/dev/null || echo 0) ))
    if [ "$AGE_SECONDS" -lt 300 ]; then
        echo "OK (modified ${AGE_SECONDS}s ago)"
    else
        echo "WARN — log last modified ${AGE_SECONDS}s ago"
    fi
else
    echo "FAIL — no log file at $LOGFILE"
    exit 1
fi

# 5. Check no recent SIGTERM in logs
echo -n "[5/6] No SIGTERM in recent logs... "
if grep -q "signal-initiated shutdown" "$LOGFILE" 2>/dev/null; then
    echo "WARN — SIGTERM detected in log"
else
    echo "OK"
fi

# 6. Count stderr errors
echo -n "[6/6] Recent errors... "
ERROR_LOG="$HOME/.hermes/logs/gateway.error.log"
if [ -f "$ERROR_LOG" ]; then
    RECENT_ERRORS=$(grep -c "ERROR\|Exception\|Traceback" "$ERROR_LOG" 2>/dev/null || echo "0")
    if [ "$RECENT_ERRORS" -gt 10 ]; then
        echo "WARN — $RECENT_ERRORS errors in error log"
    else
        echo "OK ($RECENT_ERRORS errors)"
    fi
else
    echo "OK (no error log)"
fi

echo ""
echo "=== Smoke test complete ==="