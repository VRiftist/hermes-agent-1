#!/usr/bin/env python3
"""
telegram_bridge.py - Standalone Telegram -> Gatekeeper -> Ollama bridge for Linux.

Runs as a subprocess spawned by run_bridge.py --standalone.
Polls Telegram for updates via getUpdates long-polling and routes messages
through a Gatekeeper Unix socket (if available) or directly to Ollama.
"""

import json
import os
import socket
import sys
import time
import signal
from pathlib import Path
from http.client import HTTPSConnection
from urllib.parse import urlencode

BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = os.environ.get("TELEGRAM_CHAT_IDS", "").split(",")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
GATEKEEPER_SOCKET = "/tmp/hermes-gatekeeper.sock"
DEFAULT_MODEL = os.environ.get("HERMES_MODEL", "qwen3:8b")
POLL_INTERVAL = int(os.environ.get("TELEGRAM_POLL_INTERVAL", "2"))

running = True


def signal_handler(sig, frame):
    global running
    print("\n[Bridge] Shutting down...")
    running = False


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def tg_request(method, **params):
    """Call Telegram Bot API over HTTPS."""
    conn = HTTPSConnection("api.telegram.org", 443, timeout=30)
    token = TELEGRAM_BOT_TOKEN
    url = "/bot" + token + "/" + method
    if params:
        conn.request("POST", url, body=urlencode(params),
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    else:
        conn.request("GET", url)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return data


def tg_send(chat_id, text):
    """Send message to Telegram."""
    try:
        tg_request("sendMessage", chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        print("[Bridge] Send failed to %s: %s" % (chat_id, e))


def ollama_chat(model, messages):
    """Stream chat completion from Ollama."""
    try:
        import requests
        resp = requests.post(
            "http://%s/api/chat" % OLLAMA_HOST,
            json={"model": model, "messages": messages, "stream": False},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "(no response)")
        return "(Ollama error: HTTP %d)" % resp.status_code
    except Exception as e:
        return "(Ollama unreachable: %s)" % e


def query_gatekeeper(prompt, command, prompt_type="direct"):
    """Send prompt to Gatekeeper via Unix socket for approval routing."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)
        if Path(GATEKEEPER_SOCKET).exists():
            sock.connect(GATEKEEPER_SOCKET)
            request = json.dumps({"prompt": prompt, "command": command, "type": prompt_type})
            sock.sendall(request.encode())
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if response.endswith(b"\n"):
                    break
            sock.close()
            return json.loads(response.decode().strip())
        sock.close()
    except Exception:
        pass
    return None


def process_message(msg):
    """Route incoming Telegram message through Gatekeeper -> Ollama."""
    from telegram_bridge import tg_send, ollama_chat, query_gatekeeper

    text = msg.get("text", "").strip()
    chat_id = msg.get("chat", {}).get("id")
    from_user = msg.get("from", {}).get("first_name", "unknown")

    if not text or not chat_id:
        return

    if text.startswith("/"):
        if text.startswith("/start"):
            tg_send(chat_id, "🤖 *Hermes Agent* running. Send any message.")
        return

    print("[Bridge] Message from %s: %s" % (from_user, text[:80]))

    decision = query_gatekeeper(text, text, "telegram")

    if decision and decision.get("decision") == "auto_approved":
        response = ollama_chat(DEFAULT_MODEL, [{"role": "user", "content": text}])
        tg_send(chat_id, response)
    elif decision and decision.get("decision") == "pending_approval":
        tg_send(chat_id, "Pending approval: %s" % decision.get("request_id", "?"))
    else:
        response = ollama_chat(DEFAULT_MODEL, [{"role": "user", "content": text}])
        tg_send(chat_id, response)


def get_updates(offset=None):
    """Fetch updates via getUpdates long polling."""
    params = {"offset": offset, "timeout": POLL_INTERVAL} if offset else {"timeout": POLL_INTERVAL}
    return tg_request("getUpdates", **params)


def main():
    global running

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_IDS[0]:
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_IDS required in environment")
        print("  Set them in .env or export before running.")
        sys.exit(1)

    print("[Bridge] Telegram Bridge starting...")
    print("  Token: %s..." % TELEGRAM_BOT_TOKEN[:12])
    print("  Chats: %s" % TELEGRAM_CHAT_IDS)
    print("  Ollama: %s" % OLLAMA_HOST)
    print("  Model: %s" % DEFAULT_MODEL)
    print("  Gatekeeper socket: %s" % GATEKEEPER_SOCKET)

    updates = get_updates()
    offset = None
    if updates.get("ok"):
        results = updates.get("result", [])
        if results:
            offset = results[-1]["update_id"] + 1

    print("[Bridge] Listening for messages...")

    while running:
        try:
            updates = get_updates(offset=offset)
            if not updates.get("ok"):
                print("[Bridge] getUpdates error: %s" % updates, file=sys.stderr)
                time.sleep(POLL_INTERVAL)
                continue

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    process_message(update["message"])
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("[Bridge] Poll error: %s" % e, file=sys.stderr)
            time.sleep(POLL_INTERVAL)

    print("[Bridge] Stopped.")


if __name__ == "__main__":
    main()