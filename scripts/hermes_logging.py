#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES STRUCTURED LOGGING ENGINE
JSONL logs of every prompt, completion, routing decision, tool call, and error.

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
Always on. Rotate at 10MB, keep 5 backups.
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

LOG_DIR = os.path.expanduser("~/.hermes/logs")
MAIN_LOG = os.path.join(LOG_DIR, "hermes_main.jsonl")
ERROR_LOG = os.path.join(LOG_DIR, "hermes_errors.jsonl")
DECISION_LOG = os.path.join(LOG_DIR, "hermes_decisions.jsonl")
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_BACKUPS = 5


def _ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)


def _rotate_if_needed(log_path: str):
    if os.path.exists(log_path) and os.path.getsize(log_path) > MAX_SIZE_BYTES:
        for i in range(MAX_BACKUPS - 1, 0, -1):
            old = f"{log_path}.{i}"
            new = f"{log_path}.{i + 1}"
            if os.path.exists(old):
                if i + 1 >= MAX_BACKUPS:
                    os.remove(old)
                else:
                    os.rename(old, new)
        if os.path.exists(log_path):
            os.rename(log_path, f"{log_path}.1")


def _write_log(log_path: str, entry: dict):
    _ensure_dirs()
    _rotate_if_needed(log_path)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def log_prompt(model: str, provider: str, messages: list, meta: dict = None, session_id: str = None):
    """Log an outgoing prompt to any model."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "prompt",
        "session_id": session_id or str(uuid.uuid4())[:8],
        "model": model,
        "provider": provider,
        "message_count": len(messages),
        "tokens_estimate": sum(len(m.get("content", "")) for m in messages) // 4,
        "meta": meta or {},
        "messages": messages if len(str(messages)) < 2000 else [{"summary": f"truncated, {len(messages)} messages", "first": messages[0], "last": messages[-1]}],
    }
    _write_log(MAIN_LOG, entry)


def log_completion(model: str, provider: str, response: str,
                   tokens_used: int = 0, latency_ms: int = 0,
                   cost_usd: float = 0, session_id: str = None):
    """Log a model completion response."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "completion",
        "session_id": session_id,
        "model": model,
        "provider": provider,
        "response_length": len(response),
        "response_preview": response[:200] + ("..." if len(response) > 200 else ""),
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
    }
    _write_log(MAIN_LOG, entry)


def log_decision(decision_type: str, data: dict, session_id: str = None):
    """Log a significant routing/model decision."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "decision",
        "session_id": session_id,
        "decision_type": decision_type,
        "data": data,
    }
    _write_log(DECISION_LOG, entry)
    _write_log(MAIN_LOG, entry)


def log_tool_call(tool_name: str, tool_input: dict, result: dict = None,
                  error: str = None, session_id: str = None):
    """Log a tool invocation."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "tool_call",
        "session_id": session_id,
        "tool": tool_name,
        "input": tool_input,
        "result": result,
        "error": error,
    }
    _write_log(MAIN_LOG, entry)


def log_error(error_type: str, message: str, context: dict = None,
              session_id: str = None, severity: str = "ERROR"):
    """Log an error to both main and error logs."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "error",
        "session_id": session_id,
        "severity": severity,
        "error_type": error_type,
        "message": message,
        "context": context or {},
    }
    _write_log(ERROR_LOG, entry)
    _write_log(MAIN_LOG, entry)


def log_model_health(provider: str, model: str, status: int,
                     latency_ms: int, error: str = None):
    """Log model health check results."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "health_check",
        "provider": provider,
        "model": model,
        "http_status": status,
        "latency_ms": latency_ms,
        "error": error,
        "healthy": 200 <= status < 300,
    }
    _write_log(MAIN_LOG, entry)


def get_session_log(session_id: str) -> list:
    """Retrieve all log entries for a session."""
    entries = []
    if not os.path.exists(MAIN_LOG):
        return entries
    with open(MAIN_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                if entry.get("session_id") == session_id:
                    entries.append(entry)
    return entries


if __name__ == "__main__":
    _ensure_dirs()
    print("Logging engine self-test...")

    test_session = "test-session-001"
    log_prompt("qwen3:14b", "mac-ollama",
               [{"role": "user", "content": "hello"}],
               session_id=test_session)
    log_completion("qwen3:14b", "mac-ollama",
                   "Hello! How can I help?", 120, 150, 0.0, test_session)
    log_decision("model_routing",
                 {"from": "user_request", "to": "mac-ollama",
                  "reason": "fast local response"}, test_session)
    log_tool_call("terminal", {"command": "echo test"},
                  {"output": "test", "exit_code": 0}, session_id=test_session)
    log_error("API_TIMEOUT", "DeepSeek did not respond in 60s",
              {"provider": "deepseek"}, test_session)
    log_model_health("deepseek", "deepseek-v4-flash", 200, 45)

    print(f"Session log entries: {len(get_session_log(test_session))}")
    print("Logging engine ready. ✅")