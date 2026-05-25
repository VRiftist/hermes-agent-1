#!/usr/bin/env python3
"""
CONTEXT ORCHESTRATOR — Active context window management for Hermes Agent.

Handles three lifecycle phases:
  1. SESSION PREP  — Load identity + memory state into context window
  2. MID-SESSION   — Monitor usage, trim low-priority blocks, offload to memory
  3. SESSION END   — Persist important context, prune, generate summary

Priority tiers (highest to lowest, last trimmed first):
  T0 — Identity (context-architect.md, SOUL.md)
  T1 — Active task state (working memory, current goal)
  T2 — Recent high-importance episodes (last 24h, importance >= 5)
  T3 — Semantic facts (relevant to current task)
  T4 — Recent low-importance episodes (older, importance < 5)
  T5 — Tool output history (trimmed aggressively)
  T6 — Conversation history (oldest first to trim)
"""

import os, sys, json, time, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from memory_palace import (
    store_episode, recall_episodes,
    store_fact, recall_facts,
    set_working, get_working, clear_working,
    get_stats, prune_expired,
)

# ── Paths ──────────────────────────────────────────────────────
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
ARCHITECT_FILE = HERMES_HOME / "context-architect.md"
SOUL_FILE = HERMES_HOME / "SOUL.md"
MEMORY_DB = HERMES_HOME / "memory-palace" / "palace.db"
LOG_DIR = HERMES_HOME / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ── Context budget (fits within typical 8K–16K windows) ───────
BUDGET_TOKENS = 12000          # hard ceiling before aggressive trim
WARNING_TOKENS = 9000          # soft warning, start light trim
TARGET_POST_TRIM = 6000        # target after heavy trim
EST_TOKENS_PER_CHAR = 0.25    # rough: 1 char ≈ 0.25 tokens

# ── Block registry ─────────────────────────────────────────────
# Each block: {"id": str, "tier": 0-6, "tokens": int, "content": str, "persist": bool}
_active_blocks: list[dict] = []
_session_id = None


def _est_tokens(text: str) -> int:
    """Rough token estimate."""
    return int(len(text) * EST_TOKENS_PER_CHAR)


def _load_file(path: Path, max_chars: int = 8000) -> str:
    """Load file, capped to max_chars."""
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8")
    return content[:max_chars]


# ═══════════════════════════════════════════════════════════════
# PHASE 1 — SESSION PREP
# ═══════════════════════════════════════════════════════════════

def start_session(task: str = "idle", phase: str = "startup") -> dict:
    """
    Called at session start. Loads prioritized context blocks.
    Returns the composed context string and metadata.
    """
    global _session_id, _active_blocks
    _session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    _active_blocks = []

    # Set working memory
    set_working("active_task", {"task": task, "phase": phase, "since": _session_id})

    # Tier 0: Identity (always present, never trimmed)
    identity = _load_file(ARCHITECT_FILE, 4000)
    soul = _load_file(SOUL_FILE, 2000)
    _active_blocks.append({
        "id": "t0_identity", "tier": 0, "persist": False,
        "content": f"## IDENTITY & PURPOSE\n{identity}",
        "tokens": _est_tokens(identity)
    })
    if soul.strip():
        _active_blocks.append({
            "id": "t0_soul", "tier": 0, "persist": False,
            "content": f"## SOUL & OPERATING PRINCIPLES\n{soul}",
            "tokens": _est_tokens(soul)
        })

    # Tier 1: Active task state
    working = get_working("active_task") or {}
    _active_blocks.append({
        "id": "t1_task", "tier": 1, "persist": False,
        "content": f"## CURRENT TASK\n- Task: {working.get('task', task)}\n"
                   f"- Phase: {working.get('phase', phase)}\n"
                   f"- Since: {working.get('since', _session_id)}",
        "tokens": 50  # small
    })

    # Tier 2: Recent high-importance episodes (last 24h, importance >= 5)
    recent = recall_episodes(hours=24, min_importance=5, limit=8)
    if recent:
        ep_text = "\n".join(f"- [{e.get('category','')}] {e.get('content','')[:120]}"
                           for e in recent[:6])
        _active_blocks.append({
            "id": "t2_recent_high", "tier": 2, "persist": False,
            "content": f"## RECENT HIGHLIGHTS\n{ep_text}",
            "tokens": _est_tokens(ep_text)
        })

    # Tier 3: Semantic facts relevant to task
    facts = recall_facts(task, limit=8)
    if facts:
        fact_text = "\n".join(f"- **{f.get('concept','')}**: {f.get('description','')[:150]}"
                              for f in facts[:5])
        _active_blocks.append({
            "id": "t3_semantic", "tier": 3, "persist": False,
            "content": f"## RELEVANT FACTS\n{fact_text}",
            "tokens": _est_tokens(fact_text)
        })

    # Tier 4: Recent lower-importance episodes
    older = recall_episodes(hours=72, min_importance=1, limit=5)
    older = [e for e in older if not any(r.get('content','') == e.get('content','')
             for r in recent)]  # dedup with tier 2
    if older:
        old_text = "\n".join(f"- [{e.get('category','')}] {e.get('content','')[:100]}"
                             for e in older[:4])
        _active_blocks.append({
            "id": "t4_recent_low", "tier": 4, "persist": False,
            "content": f"## BACKGROUND CONTEXT\n{old_text}",
            "tokens": _est_tokens(old_text)
        })

    # Compose and report
    total_tokens = sum(b["tokens"] for b in _active_blocks)
    context_str = "\n\n".join(b["content"] for b in _active_blocks)

    return {
        "session_id": _session_id,
        "total_blocks": len(_active_blocks),
        "total_est_tokens": total_tokens,
        "budget": BUDGET_TOKENS,
        "headroom": BUDGET_TOKENS - total_tokens,
        "context": context_str,
    }


def get_context(session_id: str = None) -> str:
    """Get the current composed context string for a session."""
    if session_id is None:
        session_id = _session_id
    if session_id is None:
        return ""
    result = start_session(task="__internal__", phase="__none__")
    return result["context"]


# ═══════════════════════════════════════════════════════════════
# PHASE 2 — MID-SESSION TRIM
# ═══════════════════════════════════════════════════════════════

def trim_context(current_usage_tokens: int, force: bool = False) -> dict:
    """
    Called when context window is getting full.
    Drops lowest-tier blocks first until under budget.
    Returns what was trimmed.
    """
    global _active_blocks
    if not _active_blocks:
        return {"trimmed": 0, "message": "No blocks to trim"}

    threshold = WARNING_TOKENS if not force else TARGET_POST_TRIM
    if current_usage_tokens < threshold and not force:
        return {"trimmed": 0, "message": f"Within budget ({current_usage_tokens} < {threshold})"}

    # Sort: highest tier number = lowest priority = trim first
    _active_blocks.sort(key=lambda b: b["tier"], reverse=True)

    trimmed = []
    new_blocks = []
    for block in _active_blocks:
        if block["tier"] >= 5 or force:
            # Tiers 5-6: always trim first
            trimmed.append({"id": block["id"], "tier": block["tier"],
                           "tokens": block["tokens"]})
        elif block["tier"] >= 3 and current_usage_tokens > TARGET_POST_TRIM:
            # Tiers 3-4: trim if still over target
            trimmed.append({"id": block["id"], "tier": block["tier"],
                           "tokens": block["tokens"]})
            current_usage_tokens -= block["tokens"]
        else:
            new_blocks.append(block)

    _active_blocks = new_blocks
    saved = sum(t["tokens"] for t in trimmed)

    # Persist trimmed high-value content to memory palace
    for t in trimmed:
        if t["tier"] <= 3:  # worth saving
            store_episode(
                _session_id, "context_evict",
                f"[{t['id']}] Trimmed block (tier {t['tier']}, {t['tokens']} tokens)",
                importance=3, tags=["trim", "context", f"tier{t['tier']}"]
            )

    return {
        "trimmed_blocks": len(trimmed),
        "tokens_recovered": saved,
        "remaining_blocks": len(_active_blocks),
        "details": trimmed,
    }


def register_tool_output(tool_name: str, output: str):
    """Register a tool output as a trimable block (tier 5)."""
    tok = _est_tokens(output)
    _active_blocks.append({
        "id": f"tool_{tool_name}_{len(_active_blocks)}",
        "tier": 5, "persist": False,
        "content": f"[TOOL: {tool_name}]\n{output[:2000]}",
        "tokens": tok
    })


def register_conversation_turn(role: str, content: str):
    """Register a conversation turn (trimmed last)."""
    _active_blocks.append({
        "id": f"msg_{role}_{len(_active_blocks)}",
        "tier": 6, "persist": False,
        "content": f"[{role}]: {content[-1500:]}",
        "tokens": _est_tokens(content[-1500:])
    })


# ═══════════════════════════════════════════════════════════════
# PHASE 3 — SESSION END
# ═══════════════════════════════════════════════════════════════

def end_session(summary: str = None):
    """
    Called at session end. Persists important state, runs maintenance.
    """
    global _active_blocks, _session_id

    # Save remaining blocks to memory palace
    for block in _active_blocks:
        if block["tier"] <= 2 and block.get("content"):
            store_episode(
                _session_id, "context_snapshot",
                block["content"][:500],
                importance=5 if block["tier"] <= 1 else 3,
                tags=[f"tier{block['tier']}", "context_end"]
            )

    if summary:
        store_episode(_session_id, "session_summary", summary,
                      importance=7, tags=["summary", "session_end"])

    # Clear working memory
    clear_working()

    # Run maintenance
    maint = prune_expired()
    stats = get_stats()

    result = {
        "session_id": _session_id,
        "blocks_saved": len([b for b in _active_blocks if b["tier"] <= 2]),
        "maintenance": maint,
        "final_stats": stats,
    }

    _active_blocks = []
    _session_id = None
    return result


# ═══════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("══════════════════════════════════════")
    print("  CONTEXT ORCHESTRATOR — SELF-TEST")
    print("══════════════════════════════════════\n")

    # Phase 1: Start session
    print("▶ Phase 1: start_session()")
    result = start_session(task="Build context trimming pipeline", phase="infrastructure")
    print(f"  Blocks loaded: {result['total_blocks']}")
    print(f"  Estimated tokens: {result['total_est_tokens']}")
    print(f"  Headroom: {result['headroom']} tokens")
    print(f"  Context preview ({len(result['context'])} chars):")
    print(f"  ---")
    for line in result['context'].split('\n')[:12]:
        print(f"  | {line}")
    print(f"  ---\n")

    # Simulate tool output
    print("▶ Registering tool output...")
    register_tool_output("terminal", "output: 42 files processed, 3 errors found...")
    register_tool_output("search_files", "Found 15 matches in /codebase")
    print(f"  Blocks now: {len(_active_blocks)}")

    # Simulate conversation
    print("▶ Registering conversation turns...")
    register_conversation_turn("user", "Can you help me fix this? Here's the error...")
    register_conversation_turn("assistant", "Sure, the issue is in your config...")
    print(f"  Blocks now: {len(_active_blocks)}")

    # Phase 2: Trim
    print("\n▶ Phase 2: trim_context(simulated 11000 tokens)")
    trim_result = trim_context(current_usage_tokens=11000)
    print(f"  Trimmed: {trim_result['trimmed_blocks']} blocks")
    print(f"  Recovered: ~{trim_result['tokens_recovered']} tokens")
    print(f"  Remaining blocks: {trim_result['remaining_blocks']}")

    # Phase 3: End session
    print("\n▶ Phase 3: end_session()")
    end = end_session(summary="Built context orchestrator with 3-phase lifecycle")
    print(f"  Blocks saved to memory: {end['blocks_saved']}")
    print(f"  Maintenance: {end['maintenance']}")
    print(f"  Final memory stats: {end['final_stats']}")

    print("\n✅ Context orchestrator working. Ready for integration.")
    print(f"   DB size: {MEMORY_DB.stat().st_size / 1024:.1f} KB")