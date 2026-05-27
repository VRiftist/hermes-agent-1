#!/bin/bash
# run_hermes.sh — Start the full Hermes pipeline on Linux
# Usage: ./run_hermes.sh
#
# Starts: Gatekeeper + Gateway + Bridge
# Stops gracefully on Ctrl+C

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Preflight ──────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════"
echo "  HERMES PIPELINE — Linux Startup"
echo "═══════════════════════════════════════════════════"

# Source .env if present (export filtered key=value pairs)
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Check required env vars
MISSING=""
[ -z "$TELEGRAM_BOT_TOKEN" ] && MISSING="$MISSING TELEGRAM_BOT_TOKEN"
[ -z "$TELEGRAM_CHAT_IDS" ] && MISSING="$MISSING TELEGRAM_CHAT_IDS"
# Cloud keys are advisory — local-only mode works without them
CLOUD_WARN=""
[ -z "$OPENROUTER_API_KEY" ] && CLOUD_WARN="$CLOUD_WARN OPENROUTER_API_KEY"
[ -z "$DEEPSEEK_API_KEY"   ] && CLOUD_WARN="$CLOUD_WARN DEEPSEEK_API_KEY"
[ -z "$XAI_API_KEY"        ] && CLOUD_WARN="$CLOUD_WARN XAI_API_KEY"

if [ -n "$MISSING" ]; then
    echo "❌ Missing required env vars:$MISSING"
    echo "   Fill them in .env file: $SCRIPT_DIR/.env"
    echo ""
    echo "   Telegram setup:"
    echo "   1. Message @BotFather → /newbot → copy token"
    echo "   2. Message @userinfobot → copy your chat ID"
    echo "   3. Cloud API keys (optional): https://openrouter.ai/keys"
    exit 1
fi

if [ -n "$CLOUD_WARN" ]; then
    echo "⚠️  Cloud keys missing (local-only mode):$CLOUD_WARN"
    echo "   Hermes will run locally via Ollama. Add keys to .env for cloud fallback."
    echo "   OpenRouter: https://openrouter.ai/keys"
    echo "   DeepSeek:   https://platform.deepseek.com/api"
    echo "   xAI:        https://console.x.ai/"
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama not responding on :11434"
    echo "   Start it: ollama serve"
    exit 1
fi

# Validate
echo ""
echo "▶ Running pre-flight validation..."
python3 run_bridge.py --validate
if [ $? -ne 0 ]; then
    echo "❌ Validation failed — fix errors above"
    exit 1
fi

# Cleanup trap
cleanup() {
    echo ""
    echo "⏹  Shutting down..."
    kill $GATEKEEPER_PID 2>/dev/null
    kill $GATEWAY_PID 2>/dev/null
    echo "   Done."
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Start Gatekeeper (background) ─────────────────────────────────
echo ""
echo "▶ Starting Gatekeeper..."
python3 gatekeeper.py &
GATEKEEPER_PID=$!
sleep 2

# Verify it started
if ! kill -0 $GATEKEEPER_PID 2>/dev/null; then
    echo "❌ Gatekeeper died on startup"
    exit 1
fi
echo "   ✅ Gatekeeper PID: $GATEKEEPER_PID"

# ── Start Gateway (background) ────────────────────────────────────
echo ""
echo "▶ Starting Gateway..."
python3 gateway_integration.py &
GATEWAY_PID=$!
sleep 2

if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "❌ Gateway died on startup"
    cleanup
fi
echo "   ✅ Gateway PID: $GATEWAY_PID"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🟢 HERMES PIPELINE RUNNING"
echo "  Gatekeeper:  PID $GATEKEEPER_PID"
echo "  Gateway:     PID $GATEWAY_PID"
echo "  Ollama:      :11434"
echo "═══════════════════════════════════════════════════"

# Keep alive — wait for background processes
wait