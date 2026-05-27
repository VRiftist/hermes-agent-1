#!/bin/bash
# auto-trim.sh — Thin wrapper → auto_trim.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/auto_trim.py" "$@"
