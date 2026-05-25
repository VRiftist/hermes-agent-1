# Context Orchestrator Gateway Wiring Spec

> Date: 2026-05-25 | Status: **DESIGNED, NOT YET WIRED** | Skill: context-trimming

## Problem

`context_orchestrator.py` works standalone (self-test passed) but is not invoked by the Hermes CLI message processing loop. The context lifecycle is currently manual — the agent does not benefit from active trimming during real conversations.

## Integration Points

The gateway message loop needs to call five orchestrator hooks:

### gateway_message_start(user_input, task_category)
Before first model call in a new turn:
```python
from context_orchestrator import start_session
result = start_session(task=user_input[:100], phase=task_category)
context_string = result["context"]
# Prepend context_string to the model prompt
```

### gateway_register_turn(role, content)
After every user/assistant exchange:
```python
from context_orchestrator import register_conversation_turn
register_conversation_turn(role, content)
```

### gateway_trim_check(current_tokens)
Before each model invocation:
```python
from context_orchestrator import trim_context
result = trim_context(current_usage_tokens)
if result["trimmed_blocks"] > 0:
    # Rebuild context from remaining blocks
    context = rebuild_context_from_blocks()
```

### gateway_register_tool(tool_name, result)
After every tool use:
```python
from context_orchestrator import register_tool_output
register_tool_output(tool_name, json.dumps(result))
```

### gateway_message_end(summary)
On session close:
```python
from context_orchestrator import end_session
result = end_session(summary="...")
```

## Compression Implementation Plan (T5)

Not yet implemented. Architecture decided:

| Tier | Strategy | Implementation Status |
|------|----------|----------------------|
| T5 tool output | Compress + tag with [COMPRESSED] | Pending |
| T6 conversation | Pure deletion | Implemented |
| T2-T4 | Dedup against Palace, then compress | Pending |

### Compression Function Signature
```python
def compress_block(block: dict, target_tokens: int) -> dict:
    """Summarize block content to target token count using a small model."""
    # Tag output with [COMPRESSED] and original token count
    # Preserve key entities and decisions
```

## Token Counting Improvement

Current: 0.25 * len(chars) rough estimate
Target: Use tiktoken for model-specific tokenizers:
```python
import tiktoken
enc = tiktoken.encoding_for_model("qwen3-14b")
tokens = len(enc.encode(text))
```