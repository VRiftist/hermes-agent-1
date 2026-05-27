#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES CIRCUIT BREAKER & HEALTH MONITOR
Detects dead models, manages failover, and restores models when healthy.
"""

import time
import json
import os
import subprocess
from typing import Dict, Optional

HEALTH_FILE = os.path.expanduser("~/.hermes/logs/model_health.json")
CHECK_INTERVAL = 300  # Check every 5 minutes
FAILURE_THRESHOLD = 3  # 3 failures → mark dead
COOLDOWN_SECONDS = 300  # 5 min cooldown before retry

MODELS_TO_MONITOR = {
    "deepseek:deepseek-v4-flash": {
        "test_url": "https://api.deepseek.com/v1/chat/completions",
        "test_key_env": "DEEPSEEK_API_KEY",
        "test_model": "deepseek-v4-flash",
    },
    "x-ai:grok-4.20-reasoning": {
        "test_url": "https://api.x.ai/v1/chat/completions",
        "test_key_env": "XAI_API_KEY",
        "test_model": "grok-4.20-reasoning",
    },
    "openrouter:ring-2.6-1t": {
        "test_url": "https://openrouter.ai/api/v1/chat/completions",
        "test_key_env": "OPENROUTER_API_KEY",
        "test_model": "ring-2.6-1t",
    },
    "kimi-coding:moonshot-v1-8k": {
        "test_url": "https://api.moonshot.cn/v1/chat/completions",
        "test_key_env": "KIMI_API_KEY",
        "test_model": "moonshot-v1-8k",
    },
}

LOCAL_MODELS = {
    "mac-ollama:qwen3:8b": {"url": "http://localhost:11434/v1", "model": "qwen3:8b"},
    "mac-ollama:qwen3:14b": {"url": "http://localhost:11434/v1", "model": "qwen3:14b"},
    "linux-ollama:qwen3-14b-128k": {"url": "http://127.0.0.1:11434/v1", "model": "qwen3-14b-128k:latest"},
}


def load_health() -> Dict:
    if os.path.exists(HEALTH_FILE):
        try:
            with open(HEALTH_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_health(health: Dict):
    os.makedirs(os.path.dirname(HEALTH_FILE), exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(health, f, indent=2)


def check_cloud_model(model_key: str, config: Dict) -> Dict:
    """Health check a cloud model via direct API call."""
    import urllib.request
    import urllib.error

    start = time.time()
    try:
        # Read key from .env or environment
        key = os.environ.get(config["test_key_env"], "")
        if not key:
            return {"healthy": False, "error": "no_api_key_configured", "latency_ms": 0}

        req = urllib.request.Request(
            config["test_url"],
            data=json.dumps({
                "model": config["test_model"],
                "messages": [{"role": "user", "content": "health_check"}],
                "max_tokens": 1
            }).encode(),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            latency = (time.time() - start) * 1000
            return {
                "healthy": 200 <= status < 300,
                "http_status": status,
                "latency_ms": round(latency),
                "error": None
            }
    except urllib.error.HTTPError as e:
        return {"healthy": False, "error": f"http_{e.code}", "latency_ms": 0}
    except Exception as e:
        return {"healthy": False, "error": str(e)[:100], "latency_ms": 0}


def check_local_model(model_key: str, config: Dict) -> Dict:
    """Health check a local Ollama model."""
    import urllib.request
    start = time.time()
    try:
        url = f"{config['url']}/api/generate"
        data = json.dumps({"model": config["model"], "prompt": "hello"}).encode()
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency = (time.time() - start) * 1000
            return {"healthy": True, "latency_ms": round(latency), "error": None}
    except Exception as e:
        return {"healthy": False, "error": str(e)[:100], "latency_ms": 0}


def run_health_checks() -> Dict:
    """Run all health checks and return status dict."""
    results = {}

    for model_key, config in MODELS_TO_MONITOR.items():
        result = check_cloud_model(model_key, config)
        results[model_key] = result

    for model_key, config in LOCAL_MODELS.items():
        result = check_local_model(model_key, config)
        results[model_key] = result

    # Save to file
    health = load_health()
    now = time.time()
    for key, result in results.items():
        if key not in health:
            health[key] = {"consecutive_failures": 0, "ok": True}
        h = health[key]
        if result["healthy"]:
            h["consecutive_failures"] = 0
            h["ok"] = True
        else:
            h["consecutive_failures"] += 1
            if h["consecutive_failures"] >= FAILURE_THRESHOLD:
                h["ok"] = False
        h["last_check"] = now
        h["last_result"] = result

    save_health(health)
    return results


def get_failover_chain(exclude: list = None) -> list:
    """Get current active model chain, excluding dead models."""
    health = load_health()
    # Preferred order
    chain = [
        "mac-ollama:qwen3:14b",
        "linux-ollama:qwen3-14b-128k",
        "deepseek:deepseek-v4-flash",
        "x-ai:grok-4.20-reasoning",
        "openrouter:ring-2.6-1t",
    ]
    if exclude is None:
        exclude = set()
    else:
        exclude = set(exclude)

    active = []
    for model in chain:
        h = health.get(model, {})
        is_ok = h.get("ok", True)
        if is_ok and model not in exclude:
            active.append(model)
    return active


def check_health(model_key: str) -> bool:
    """Check if a model is currently healthy (standalone interface)."""
    health = load_health()
    h = health.get(model_key, {})
    if not h:
        return True  # Unknown = assume healthy
    if not h.get("ok", True):
        if time.time() - h.get("last_check", 0) > COOLDOWN_SECONDS:
            return True  # Cooldown expired, retry
    return h.get("ok", True)


def report_health(model_key: str, model_name: str | None, success: bool, latency_ms: int = 0):
    """Report a health check result for a model (standalone interface)."""
    health = load_health()
    if model_key not in health:
        health[model_key] = {"consecutive_failures": 0, "ok": True}
    h = health[model_key]
    h["last_check"] = time.time()
    if success:
        h["consecutive_failures"] = 0
        h["ok"] = True
        h["avg_latency_ms"] = latency_ms
    else:
        h["consecutive_failures"] += 1
        if h["consecutive_failures"] >= FAILURE_THRESHOLD:
            h["ok"] = False
    save_health(health)


if __name__ == "__main__":
    print("Running health checks...")
    results = run_health_checks()
    for key, result in results.items():
        status = "✅" if result["healthy"] else "❌"
        latency = result.get("latency_ms", "?")
        error = result.get("error") or ""
        print(f"  {status} {key}: {latency}ms {error}")

    print(f"\nActive chain: {get_failover_chain()}")
    print("Circuit breaker ready. ✅")