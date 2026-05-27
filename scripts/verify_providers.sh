#!/bin/bash
# OLLAMA_API_KEY Verification Launcher
# Tests all provider keys from terminal (NOT sandbox — bypasses env isolation)
# Run: bash ~/.hermes/scripts/verify_providers.sh

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'
RESULTS=""

log_ok() { RESULTS="${RESULTS}\n${GREEN}✅ $1${NC}"; }
log_fail() { RESULTS="${RESULTS}\n${RED}❌ $1${NC}"; }
log_warn() { RESULTS="${RESULTS}\n${YELLOW}⚠️  $1${NC}"; }

echo "=========================================="
echo " Provider Key Verification — $(date)"
echo "=========================================="

# --- OLLAMA_API_KEY ---
echo -e "\n${YELLOW}Testing OLLAMA_API_KEY...${NC}"
OLLAMA_KEY=$(grep -i "^OLLAMA_API_KEY" ~/.hermes/.env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | xargs) || true

if [ -z "$OLLAMA_KEY" ]; then
    log_fail "OLLAMA_API_KEY not found in ~/.hermes/.env"
else
    echo "  Key format: ${OLLAMA_KEY:0:12}..."
    # Test against cloud.ollama.com
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "https://cloud.ollama.com/api/tags" \
        -H "Authorization: Bearer $OLLAMA_KEY" \
        --max-time 10 2>/dev/null) || HTTP_CODE="000"

    case "$HTTP_CODE" in
        200) log_ok "OLLAMA_API_KEY — live endpoint OK (HTTP 200)" ;;
        401) log_fail "OLLAMA_API_KEY — invalid auth (HTTP 401), key is bad" ;;
        403) log_warn "OLLAMA_API_KEY — forbidden (HTTP 403), possible key restriction" ;;
        000) log_warn "OLLAMA_API_KEY — connection failed (no internet or DNS block)" ;;
        *)   log_warn "OLLAMA_API_KEY — unexpected response (HTTP ${HTTP_CODE})" ;;
    esac

    # Also test local endpoint (no key needed)
    LOCAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://localhost:11434/api/tags" \
        --max-time 5 2>/dev/null) || LOCAL_CODE="000"

    case "$LOCAL_CODE" in
        200) log_ok "Ollama local — running on localhost:11434" ;;
        000) log_warn "Ollama local — not running on localhost:11434" ;;
        *)   log_warn "Ollama local — response (HTTP ${LOCAL_CODE})" ;;
    esac
fi

# --- ANTHROPIC_API_KEY ---
echo -e "\n${YELLOW}Testing ANTHROPIC_API_KEY...${NC}"
ANTHROPIC_KEY=$(grep -i "^ANTHROPIC_API_KEY" ~/.hermes/.env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | xargs) || true

if [ -z "$ANTHROPIC_KEY" ]; then
    log_fail "ANTHROPIC_API_KEY not found in ~/.hermes/.env"
else
    echo "  Key format: ${ANTHROPIC_KEY:0:8}..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://api.anthropic.com/v1/models" \
        -H "x-api-key: ${ANTHROPIC_KEY}" \
        -H "anthropic-version: 2023-06-01" \
        --max-time 10 2>/dev/null) || HTTP_CODE="000"

    case "$HTTP_CODE" in
        200) log_ok "ANTHROPIC_API_KEY — live endpoint OK" ;;
        401) log_fail "ANTHROPIC_API_KEY — invalid auth" ;;
        000) log_warn "ANTHROPIC_API_KEY — connection failed" ;;
        *)   log_warn "ANTHROPIC_API_KEY — HTTP ${HTTP_CODE}" ;;
    esac
fi

# --- OPENROUTER_API_KEY ---
echo -e "\n${YELLOW}Testing OPENROUTER_API_KEY...${NC}"
OR_KEY=$(grep -i "^OPENROUTER_API_KEY" ~/.hermes/.env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | xargs) || true

if [ -z "$OR_KEY" ]; then
    log_fail "OPENROUTER_API_KEY not found in ~/.hermes/.env"
else
    echo "  Key format: ${OR_KEY:0:8}..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://openrouter.ai/api/v1/models" \
        -H "Authorization: Bearer $OR_KEY" \
        --max-time 10 2>/dev/null) || HTTP_CODE="000"

    case "$HTTP_CODE" in
        200) log_ok "OPENROUTER_API_KEY — live endpoint OK" ;;
        401) log_fail "OPENROUTER_API_KEY — invalid auth" ;;
        000) log_warn "OPENROUTER_API_KEY — connection failed" ;;
        *)   log_warn "OPENROUTER_API_KEY — HTTP ${HTTP_CODE}" ;;
    esac
fi

# --- DEEPSEEK_API_KEY ---
echo -e "\n${YELLOW}Testing DEEPSEEK_API_KEY...${NC}"
DS_KEY=$(grep -i "^DEEPSEEK_API_KEY" ~/.hermes/.env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | xargs) || true

if [ -z "$DS_KEY" ]; then
    log_fail "DEEPSEEK_API_KEY not found in ~/.hermes/.env"
else
    echo "  Key format: ${DS_KEY:0:8}..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://api.deepseek.com/v1/models" \
        -H "Authorization: Bearer $DS_KEY" \
        --max-time 10 2>/dev/null) || HTTP_CODE="000"

    case "$HTTP_CODE" in
        200) log_ok "DEEPSEEK_API_KEY — live endpoint OK" ;;
        401) log_fail "DEEPSEEK_API_KEY — invalid auth" ;;
        000) log_warn "DEEPSEEK_API_KEY — connection failed" ;;
        *)   log_warn "DEEPSEEK_API_KEY — HTTP ${HTTP_CODE}" ;;
    esac
fi

# --- KIMI_API_KEY (Moonshot) ---
echo -e "\n${YELLOW}Testing KIMI_API_KEY...${NC}"
KIMI_KEY=$(grep -i "^KIMI_API_KEY" ~/.hermes/.env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | xargs) || true

if [ -z "$KIMI_KEY" ]; then
    log_fail "KIMI_API_KEY not found in ~/.hermes/.env"
else
    echo "  Key format: ${KIMI_KEY:0:8}..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://api.moonshot.cn/v1/models" \
        -H "Authorization: Bearer $KIMI_KEY" \
        --max-time 10 2>/dev/null) || HTTP_CODE="000"

    case "$HTTP_CODE" in
        200) log_ok "KIMI_API_KEY — live endpoint OK" ;;
        401) log_fail "KIMI_API_KEY — invalid auth (known issue, check rate limits)" ;;
        429) log_warn "KIMI_API_KEY — rate limited (this is the 401-masquerading-as-auth issue)" ;;
        000) log_warn "KIMI_API_KEY — connection failed" ;;
        *)   log_warn "KIMI_API_KEY — HTTP ${HTTP_CODE}" ;;
    esac
fi

# --- SSH to Linux .114 ---
echo -e "\n${YELLOW}Testing SSH to Linux .114...${NC}"
SSH_CODE=$(ssh -o ConnectTimeout=5 -o BatchMode=yes gerald@192.168.1.114 "echo ok" 2>&1) && log_ok "SSH to .114 — reachable" || log_warn "SSH to .114 — failed or unreachable"

echo -e "\n=========================================="
echo -e "Summary:${RESULTS}"
echo "=========================================="
echo ""
echo "To update PROVIDER_STATUS.md after running this:"
echo "  1. Edit ~/.hermes/knowledge_base/PROVIDER_STATUS.md"
echo "  2. Update status emojis based on results above"
echo "  3. Commit: git add knowledge_base/ && git commit -m 'update provider status'"