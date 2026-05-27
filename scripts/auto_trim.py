#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
auto_trim.py — Qwen-powered context compression engine
Ported to Mac workspace from linux_prod/auto_trim.py

Reads Hive boxes, calls Qwen/Ollama for relevance scoring, compresses or evicts cold entries.
Called by the gateway integration when context exceeds threshold.

Usage:
    python3 auto_trim.py [--dry-run] [--target-tokens N] [--model qwen3:8b]
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# ─── Configuration (Mac-adapted paths) ────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
BASE_DIR = HERMES_HOME  # scripts/ lives under .hermes/
WORKSPACE = HERMES_HOME
BRIDGE_DIR = WORKSPACE / "bridge"
SIGNALS_DIR = BRIDGE_DIR / "signals"
ARCHIVE_DIR = WORKSPACE / "logs" / "archive"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
TARGET_MODEL = os.environ.get("TRIM_MODEL", "qwen3:8b")
COMPRESSION_PROMPT = """You are a context compression engine. Given a conversation summary,
produce a dense 2-3 sentence summary that preserves all facts, decisions, and action items.
Return ONLY the compressed summary, no preamble.

Input: {text}
Compressed summary:"""

TRIM_THRESHOLD_TOKENS = int(os.environ.get("TRIM_THRESHOLD_TOKENS", "100000"))
TARGET_TOKENS = int(os.environ.get("TARGET_TOKENS", "60000"))
DRY_RUN = "--dry-run" in sys.argv


# ─── Ollama API ────────────────────────────────────────────────────────────────
def query_ollama(model: str, prompt: str, max_tokens: int = 2048) -> str:
    """Send a prompt to Ollama and return the response text."""
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[auto_trim] Ollama error: {e}", file=sys.stderr)
        return ""


def count_tokens(text: str) -> int:
    """Rough token count — good enough for threshold checks."""
    return max(len(text.split()), len(text) // 4)


# ─── Compression logic ─────────────────────────────────────────────────────────
def compress_block(text: str, model: str = TARGET_MODEL) -> dict:
    """Compress a single text block via Ollama. Returns dict with result or error."""
    prompt = COMPRESSION_PROMPT.format(text=text[:4000])
    result = query_ollama(model, prompt)
    if not result:
        return {"status": "error", "error": "empty response from model"}
    return {
        "status": "ok",
        "original_tokens": count_tokens(text),
        "compressed_text": result,
        "compressed_tokens": count_tokens(result),
        "saved_tokens": max(0, count_tokens(text) - count_tokens(result)),
        "ratio": round(count_tokens(result) / max(count_tokens(text), 1), 2),
    }


def trim_context(context_blocks: list[dict], budget: int = TARGET_TOKENS) -> dict:
    """
    Trim context to fit within budget. Strategy:
    1. Sort blocks by priority (lower = trim first)
    2. Delete T5/T6 blocks (tool output, raw conversation)
    3. Compress T3/T4 blocks (semantic, background)
    4. Keep T0-T2 intact (identity, task, high-importance)
    """
    total_tokens = sum(count_tokens(b.get("content", "")) for b in context_blocks)
    if total_tokens <= budget:
        return {"status": "ok", "action": "none", "tokens_before": total_tokens, "tokens_after": total_tokens}

    overage = total_tokens - budget
    deleted = 0
    compressed = 0
    saved = 0
    remaining = []

    # Phase 1: Delete low-priority blocks
    for block in context_blocks:
        priority = block.get("priority", 6)
        block_tokens = count_tokens(block.get("content", ""))
        if priority >= 5 and overage > 0:
            deleted += 1
            saved += block_tokens
            overage -= block_tokens
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            archive_file = ARCHIVE_DIR / f"trimmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{block.get('id', 'unknown')}.json"
            archive_file.write_text(json.dumps(block, indent=2, default=str))
            continue
        remaining.append(block)

    # Phase 2: Compress medium-priority blocks if still over budget
    if overage > 0 and not DRY_RUN:
        for block in remaining:
            priority = block.get("priority", 6)
            if priority in (3, 4) and overage > 0:
                result = compress_block(block["content"])
                if result.get("status") == "ok":
                    compressed += 1
                    saved += result["saved_tokens"]
                    overage -= result["saved_tokens"]
                    block["content"] = result["compressed_text"]
                    block["compressed"] = True
                    block["compressed_at"] = datetime.now().isoformat()

    return {
        "status": "ok",
        "tokens_before": total_tokens,
        "tokens_after": total_tokens - saved,
        "tokens_saved": saved,
        "blocks_deleted": deleted,
        "blocks_compressed": compressed,
        "compression_ratio": round((total_tokens - saved) / max(total_tokens, 1), 2),
        "overage_resolved": overage <= 0,
    }


# ─── IPC signal handling ───────────────────────────────────────────────────────
def write_signal(filename: str, data: dict) -> None:
    """Write a signal file for the bridge to pick up."""
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    path = SIGNALS_DIR / filename
    path.write_text(json.dumps(data, indent=2, default=str))


def read_latest_telegram() -> dict:
    """Read the latest Telegram message from bridge signal."""
    path = BRIDGE_DIR / "latest-from-telegram.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


# ─── Main entry point ──────────────────────────────────────────────────────────
def main():
    global DRY_RUN
    if "--dry-run" in sys.argv:
        DRY_RUN = True

    # Check if trim is triggered via signal file
    trigger = SIGNALS_DIR / "trigger-trim.json"
    if trigger.exists():
        try:
            signal = json.loads(trigger.read_text())
            trigger.unlink()  # Consume the signal
            mode = signal.get("mode", "auto")
            target = signal.get("target_tokens", TARGET_TOKENS)
            print(f"[auto_trim] Triggered via signal: mode={mode}, target={target}")
        except Exception as e:
            print(f"[auto_trim] Signal parse error: {e}", file=sys.stderr)
            mode = "auto"
            target = TARGET_TOKENS
    else:
        mode = "auto"
        target = TARGET_TOKENS

    # Read context blocks
    context_file = BRIDGE_DIR / "context-status.json"
    if not context_file.exists():
        print("[auto_trim] No context-status.json found, nothing to trim")
        sys.exit(0)

    try:
        with open(context_file) as f:
            data = json.load(f)
        blocks = data.get("blocks", [])
    except Exception as e:
        print(f"[auto_trim] Error reading context: {e}", file=sys.stderr)
        sys.exit(1)

    if not blocks:
        print("[auto_trim] No blocks to process")
        sys.exit(0)

    # Run trim
    print(f"[auto_trim] Processing {len(blocks)} blocks, budget={target} tokens, dry_run={DRY_RUN}")
    result = trim_context(blocks, budget=target)

    # Write response
    response_file = SIGNALS_DIR / "responses" / f"trim_{int(time.time())}.json"
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    (SIGNALS_DIR / "responses").mkdir(parents=True, exist_ok=True)
    response_file.write_text(json.dumps(result, indent=2))

    print(f"[auto_trim] Result: saved={result.get('tokens_saved', 0)} tokens, "
          f"deleted={result.get('blocks_deleted', 0)}, compressed={result.get('blocks_compressed', 0)}, "
          f"ratio={result.get('compression_ratio', '?')}")

    # Archive to Memory Palace
    palace = WORKSPACE / "wiki" / "MEMORY-PALACE.md"
    if palace.exists():
        with open(palace, "a") as f:
            f.write(f"\n---\n### 📦 Auto-Trim — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> Mode: {mode} | Saved: {result.get('tokens_saved', 0)} tokens | "
                    f"Deleted: {result.get('blocks_deleted')} | Compressed: {result.get('blocks_compressed')}\n")

    print("[auto_trim] Complete.")


if __name__ == "__main__":
    main()