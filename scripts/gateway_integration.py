#!/usr/bin/env python3
"""
Hermes Gateway Integration — Context Orchestrator Bridge
This is the glue between the Hermes CLI gateway and context_orchestrator.py.

The gateway should call these functions at each lifecycle point:
  - gateway_message_start()   → at the beginning of each user message
  - gateway_register_turn()   → after each assistant/user exchange
  - gateway_register_tool()   → after each tool call result
  - gateway_trim_check()      → before sending response if context is large
  - gateway_message_end()     → at session end
"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from context_orchestrator import (
    start_session, trim_context, end_session,
    register_conversation_turn, register_tool_output,
    get_context, _active_blocks, _session_id
)
from memory_palace import get_working

# ── Public API for Gateway ──────────────────────────────────────

def gateway_message_start(user_input: str, task_category: str = "general") -> dict:
    """Call at the start of each user message. Returns context to prepend."""
    result = start_session(task=task_category, phase="processing")
    return {
        "session_id": result["session_id"],
        "context_header": result["context"],
        "est_tokens": result["total_est_tokens"],
        "headroom": result["headroom"],
    }


def gateway_register_turn(role: str, content: str):
    """Register a user or assistant turn."""
    register_conversation_turn(role, content)


def gateway_register_tool(tool_name: str, tool_result: str):
    """Register a tool call result."""
    register_tool_output(tool_name, json.dumps(tool_result) if isinstance(tool_result, dict) else tool_result)


def gateway_trim_check(current_tokens: int = 0, force: bool = False) -> dict:
    """Check if trimming is needed. Call before generating response."""
    return trim_context(current_usage_tokens=current_tokens, force=force)


def gateway_message_end(summary: str = None) -> dict:
    """Call at session end. Persists state and runs maintenance."""
    return end_session(summary=summary)


def gateway_get_context() -> str:
    """Get the current composed context string."""
    return get_context(_session_id) if _session_id else ""


def gateway_status() -> dict:
    """Return current gateway status for monitoring."""
    return {
        "session_id": _session_id,
        "active_blocks": len(_active_blocks),
        "has_session": _session_id is not None,
    }


# ── Self-Test ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("HERMES GATEWAY INTEGRATION — SELF-TEST\n")

    # Simulate a full message lifecycle
    print("1. gateway_message_start()")
    start = gateway_message_start("Write a Python function to parse JSON", task_category="code_generation")
    print(f"   Session: {start['session_id']}")
    print(f"   Context tokens: {start['est_tokens']}, Headroom: {start['headroom']}")
    print(f"   ✅ Context header loaded ({len(start['context_header'])} chars)")

    print("\n2. gateway_register_turn(user)")
    gateway_register_turn("user", "Write a Python function to parse JSON strings safely")
    print(f"   ✅ Turn registered, blocks: {len(_active_blocks)}")

    print("\n3. gateway_register_turn(assistant)")
    gateway_register_turn("assistant", "```python\nimport json\ndef parse_json(s):\n    return json.loads(s)\n```")
    print(f"   ✅ Turn registered, blocks: {len(_active_blocks)}")

    print("\n4. gateway_register_tool()")
    gateway_register_tool("execute_code", {"output": "All tests passed", "exit_code": 0})
    print(f"   ✅ Tool output registered, blocks: {len(_active_blocks)}")

    print("\n5. gateway_trim_check() — should be within budget")
    trim = gateway_trim_check(current_tokens=5000)
    print(f"   Trimmed: {trim['trimmed_blocks']} blocks, Message: {trim['message']}")

    print("\n6. gateway_status()")
    status = gateway_status()
    print(f"   Status: {status}")

    print("\n7. gateway_message_end()")
    end = gateway_message_end("Successfully generated JSON parser function")
    print(f"   Blocks saved: {end['blocks_saved']}, Maintenance: {end['maintenance']}")
    print(f"   Final stats: {end['final_stats']}")

    print("\n✅ Gateway integration layer working. Ready to wire into message loop.")