#!/usr/bin/env python3
"""
key_guardian.py — Daily key health check + Telegram alert.
Scans ~/.hermes/.env, tests each key against its provider, reports dead/missing.
Runs via cron: 0 6 * * * cd ~/.hermes && python3 scripts/key_guardian.py
"""

import os, sys, json, subprocess, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

ENV_PATH = os.path.expanduser("~/.hermes/.env")
HEALTH_FILE = os.path.expanduser("~/.hermes/logs/model_health.json")
LOG_DIR = os.path.expanduser("~/.hermes/logs")

# Provider test config: env var name → (test_url, test_method, test_payload)
PROVIDERS = {
    "DEEPSEEK_API_KEY": {
        "name": "DeepSeek",
        "test_endpoint": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
    },
    "XAI_API_KEY": {
        "name": "xAI (Grok)",
        "test_endpoint": "https://api.x.ai/v1/chat/completions",
        "model": "grok-4.20-reasoning",
    },
    "OPENROUTER_KEY_1": {
        "name": "OpenRouter (key 1)",
        "test_endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": "inclusionai/ring-2.6-1t",
    },
    "OPENROUTER_KEY_2": {
        "name": "OpenRouter (key 2)",
        "test_endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": "inclusionai/ring-2.6-1t",
    },
    "KIMI_API_KEY": {
        "name": "Kimi",
        "test_endpoint": "https://api.moonshot.cn/v1/chat/completions",
        "model": "kimi-1t",
    },
}


def load_env():
    """Parse .env into dict, stripping comments and whitespace."""
    env = {}
    if not os.path.exists(ENV_PATH):
        return env
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env
def test_key(provider_name, config, api_key):
    """Quick health ping — send a minimal completion request, check for 200/401/4xx.

    For Moonshot/Kimi, use the dedicated kimi_client with built-in retry/backoff,
    since her errors are rate-limit transient, not key failures.
    """
    # Use dedicated Kimi client for Moonshot — handles retry + rate limits
    if provider_name == "Kimi":
        try:
            from kimi_client import health_check as kimi_health
            result = kimi_health()
            if result.get("status") == "healthy":
                return "alive", 200
            else:
                return "unhealthy", result.get("detail", {}).get("error", "unknown")
        except Exception as e:
            return "error", str(e)[:120]

    import urllib.request, urllib.error

    url = config["test_endpoint"]
    payload = json.dumps({
        "model": config["model"],
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read(512).decode()
            if status == 200:
                return "alive", status
            else:
                return "unhealthy", status
    except urllib.error.HTTPError as e:
        return "dead", e.code
    except Exception as e:
        return "error", str(e)[:120]


def send_telegram_alert(message):
    """Send alert via curl to Telegram bot."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        print(f"[key_guardian] Telegram not configured, skipping alert.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    subprocess.run([
        "curl", "-s", "-X", "POST", url,
        "-d", f"chat_id={chat_id}",
        "-d", f"text={message}",
        "-d", "parse_mode=Markdown"
    ], capture_output=True, timeout=30)


def run_checks():
    """Main check loop. Returns dict of results."""
    env = load_env()
    results = {}
    dead_keys = []
    missing_keys = []

    for var, config in PROVIDERS.items():
        key = env.get(var, "")
        if not key:
            missing_keys.append(config["name"])
            results[var] = {"status": "missing", "detail": "not in .env"}
            continue

        status, detail = test_key(config["name"], config, key)
        results[var] = {"status": status, "detail": detail}
        if status in ("dead", "error", "unhealthy"):
            dead_keys.append(f"{config['name']} ({var}) → {status}: {detail}")

    # Load previous health for comparison
    prev = {}
    if os.path.exists(HEALTH_FILE):
        try:
            with open(HEALTH_FILE) as f:
                prev = json.load(f)
        except json.JSONDecodeError:
            prev = {}

    # Write current state
    health = {
        "last_check": datetime.datetime.utcnow().isoformat() + "Z",
        "providers": results,
    }
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(health, f, indent=2)

    # Alert if anything changed to dead
    if dead_keys:
        alert = "🚨 **Key Guardian Alert**\n\nThe following keys failed health check:\n"
        for k in dead_keys:
            alert += f"• `{k}`\n"
        alert += f"\nTimestamp: {health['last_check']}"
        send_telegram_alert(alert)
        print(alert)
    else:
        print(f"[key_guardian] All keys healthy at {health['last_check']}")

    # Also flag previously-dead keys that are now alive (recovery)
    prev_dead = prev.get("dead_keys", [])
    if prev_dead:
        recovered = [k for k in prev_dead if k not in dead_keys]
        if recovered:
            recovery_msg = "✅ **Key Guardian Recovery**\n\nKeys back online:\n"
            for k in recovered:
                recovery_msg += f"• `{k}`\n"
            send_telegram_alert(recovery_msg)

    # Persist dead keys list for next comparison
    if dead_keys:
        health["dead_keys"] = dead_keys
        with open(HEALTH_FILE, "w") as f:
            json.dump(health, f, indent=2)

    return results


if __name__ == "__main__":
    run_checks()