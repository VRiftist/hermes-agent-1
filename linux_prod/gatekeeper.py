#!/usr/bin/env python3
"""
gatekeeper.py — Local approval daemon (Mac-local version)
Sits between the gateway and the operator. Receives prompts requiring
human approval, notifies via Telegram, and injects responses.

No heavy dependencies. Pure stdlib + optional requests for Telegram.

Usage:
    python3 gatekeeper.py                    # Start daemon (foreground)
    python3 gatekeeper.py --background       # Start in background
    python3 gatekeeper.py --stop             # Stop background daemon
    python3 gatekeeper.py --status           # Show daemon state
"""

import json
import os
import sys
import time
import signal as sig_module
import socket
import struct
import subprocess
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============ Configuration ============

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("WORKSPACE", str(BASE_DIR.parent.parent)))

SOCKET_PATH = "/tmp/hermes-gatekeeper.sock"
PENDING_DIR = WORKSPACE / "logs" / "gatekeeper" / "pending"
RESPONSE_DIR = WORKSPACE / "logs" / "gatekeeper" / "responses"
HISTORY_DIR = WORKSPACE / "logs" / "gatekeeper" / "history"
CONFIG_DIR = WORKSPACE / "config"
CONFIG_FILE = CONFIG_DIR / "gatekeeper.json"
SIGNALS_DIR = WORKSPACE / "bridge" / "signals"

# Learning thresholds
AUTO_RESOLVE_THRESHOLD = 3
AUTO_RESOLVE_COOLDOWN = 300

# ============ Default Config ============

DEFAULT_CONFIG = {
    "telegram_bot_token": None,
    "telegram_chat_ids": [],
    "auto_resolve_threshold": AUTO_RESOLVE_THRESHOLD,
    "auto_resolve_cooldown": AUTO_RESOLVE_COOLDOWN,
    "notification_method": "telegram",
    "quiet_hours": None,
    "known_commands": {},
    "max_pending": 50,
}


def ensure_dirs():
    """Create all required directories."""
    for d in [PENDING_DIR, RESPONSE_DIR, HISTORY_DIR, CONFIG_DIR, SIGNALS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()


# ============ Config Management ============

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            merged = {**DEFAULT_CONFIG, **data}
            return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


config = load_config()


# ============ Notification System ============

def notify_telegram(message: str):
    """Send a Telegram notification if token is configured."""
    token = config.get("telegram_bot_token")
    chat_ids = config.get("telegram_chat_ids", [])
    if not token or not chat_ids:
        print(f"[Gatekeeper] Telegram not configured, logging only: {message[:100]}")
        return

    import requests
    for chat_id in chat_ids:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            print(f"[Gatekeeper] Telegram notify failed: {e}")


def notify(prompt_type: str, message: str):
    """Send notification based on configured method."""
    method = config.get("notification_method", "telegram")
    if method in ("telegram", "both"):
        notify_telegram(f"⚠️ *Gatekeeper: {prompt_type}*\n\n{message}")
    if method in ("log", "both"):
        print(f"[Gatekeeper] [{prompt_type}] {message}")


# ============ Memory System ============

class Memory:
    """Persistent learning system — remembers approvals and auto-resolves patterns."""

    def __init__(self):
        self.data_file = HISTORY_DIR / "memory.json"
        self.data = self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except Exception:
                pass
        return {
            "approvals": [],
            "known_hosts": [],
            "command_patterns": {},
            "last_auto_resolve": {},
            "total_notifications": 0,
            "total_auto_resolved": 0,
            "total_manual": 0,
        }

    def save(self):
        self.data_file.write_text(json.dumps(self.data, indent=2))

    def record_approval(self, prompt_type: str, command: str, response: str, auto: bool = False):
        resp_hash = hashlib.sha256(response.encode()).hexdigest()[:16]
        entry = {
            "type": prompt_type,
            "command": command,
            "response_hash": resp_hash,
            "auto": auto,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["approvals"].append(entry)

        key = f"{command}:{prompt_type}"
        if key not in self.data["command_patterns"]:
            self.data["command_patterns"][key] = {
                "count": 0,
                "response_hash": resp_hash,
                "last_used": None,
            }
        self.data["command_patterns"][key]["count"] += 1
        self.data["command_patterns"][key]["last_used"] = time.time()

        if auto:
            self.data["total_auto_resolved"] += 1
        else:
            self.data["total_manual"] += 1

        self.save()

    def check_auto_resolve(self, command: str, prompt_type: str) -> tuple[bool, str | None]:
        key = f"{command}:{prompt_type}"
        pattern = self.data["command_patterns"].get(key)
        threshold = config.get("auto_resolve_threshold", AUTO_RESOLVE_THRESHOLD)

        if pattern and pattern["count"] >= threshold:
            last = pattern.get("last_used", 0)
            cooldown = config.get("auto_resolve_cooldown", AUTO_RESOLVE_COOLDOWN)
            if time.time() - last < cooldown:
                return False, "In cooldown period"
            return True, pattern["response_hash"]
        return False, None


memory = Memory()


# ============ Pending Request Queue ============

class PendingQueue:
    """Thread-safe pending request queue with file backing."""

    def __init__(self):
        self._lock = threading.Lock()

    def add(self, request_id: str, prompt: str, command: str, prompt_type: str):
        with self._lock:
            PENDING_DIR.mkdir(parents=True, exist_ok=True)
            entry = {
                "id": request_id,
                "prompt": prompt,
                "command": command,
                "type": prompt_type,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
            }
            (PENDING_DIR / f"{request_id}.json").write_text(json.dumps(entry, indent=2))
            self._enforce_limit()

    def get(self, request_id: str) -> dict | None:
        path = PENDING_DIR / f"{request_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def resolve(self, request_id: str, approved: bool, response: str):
        with self._lock:
            path = PENDING_DIR / f"{request_id}.json"
            if path.exists():
                entry = json.loads(path.read_text())
                entry["status"] = "approved" if approved else "denied"
                entry["response"] = response
                entry["resolved_at"] = datetime.now().isoformat()

                # Move to history
                HISTORY_DIR.mkdir(parents=True, exist_ok=True)
                path.rename(HISTORY_DIR / f"{request_id}.json")
                HISTORY_DIR.joinpath(f"{request_id}.json").write_text(json.dumps(entry, indent=2))

    def _enforce_limit(self):
        max_pending = config.get("max_pending", 50)
        files = sorted(PENDING_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
        while len(files) > max_pending:
            oldest = files.pop(0)
            oldest.unlink()

    def pending_count(self) -> int:
        return len(list(PENDING_DIR.glob("*.json"))) if PENDING_DIR.exists() else 0


pending = PendingQueue()


# ============ Request Handler ============

class GatekeeperHandler(BaseHTTPRequestHandler):
    """HTTP handler for incoming gatekeeper requests."""

    def log_message(self, format: str, *args):
        print(f"[Gatekeeper HTTP] {format % args}")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        prompt = data.get("prompt", "")
        command = data.get("command", "")
        prompt_type = data.get("type", "unknown")
        request_id = data.get("request_id", hashlib.md5(f"{time.time()}{prompt}".encode()).hexdigest()[:12])

        self._handle_request(request_id, prompt, command, prompt_type)

    def _handle_request(self, request_id: str, prompt: str, command: str, prompt_type: str):
        # Check auto-resolve
        auto, resp_hash = memory.check_auto_resolve(command, prompt_type)
        if auto:
            self._respond(200, {
                "decision": "auto_approved",
                "response_hash": resp_hash,
                "request_id": request_id,
            })
            return

        # Check quiet hours
        if self._in_quiet_hours():
            self._respond(200, {
                "decision": "queued",
                "reason": "quiet_hours",
                "request_id": request_id,
            })
            return

        # Queue for manual approval
        pending.add(request_id, prompt, command, prompt_type)

        # Notify operator
        notify(prompt_type, f"New pending request `{request_id}`:\n\n> {prompt[:200]}")

        self._respond(200, {
            "decision": "pending_approval",
            "request_id": request_id,
            "pending_count": pending.pending_count(),
        })

    def _in_quiet_hours(self) -> bool:
        qh = config.get("quiet_hours")
        if not qh:
            return False
        from datetime import datetime as dt
        now = dt.now().strftime("%H:%M")
        start = qh.get("start", "23:00")
        end = qh.get("end", "07:00")
        return start <= now or now <= end

    def _respond(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


# ============ Unix Socket Server ============

class UnixSocketServer:
    """Unix domain socket server for local IPC."""

    def __init__(self, path: str):
        self.path = path
        self.running = False

    def start(self):
        # Clean up stale socket
        if Path(self.path).exists():
            Path(self.path).unlink()

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.path)
        self.sock.listen(5)
        self.running = True
        print(f"[Gatekeeper] Listening on {self.path}")

        while self.running:
            try:
                self.sock.settimeout(1.0)
                conn, _ = self.sock.accept()
                threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_connection(self, conn):
        try:
            data = conn.recv(4096).decode()
            if not data:
                return
            request = json.loads(data)
            # Dispatch to handler logic
            request_id = request.get("request_id", "unknown")
            prompt = request.get("prompt", "")
            command = request.get("command", "")
            prompt_type = request.get("type", "unknown")

            auto, resp_hash = memory.check_auto_resolve(command, prompt_type)
            if auto:
                response = {"decision": "auto_approved", "request_id": request_id}
            else:
                pending.add(request_id, prompt, command, prompt_type)
                notify(prompt_type, f"Pending: {prompt[:100]}")
                response = {"decision": "pending", "request_id": request_id}

            conn.sendall((json.dumps(response) + "\n").encode())
        except Exception as e:
            conn.sendall((json.dumps({"error": str(e)}) + "\n").encode())
        finally:
            conn.close()

    def stop(self):
        self.running = False
        if Path(self.path).exists():
            Path(self.path).unlink()


# ============ Background Daemon ============

class Daemon:
    """Background daemon with PID file management."""

    PID_FILE = Path("~/.hermes/run/gatekeeper.pid").expanduser()

    def __init__(self):
        self.server = UnixSocketServer(SOCKET_PATH)

    def start(self, background: bool = False):
        if self.PID_FILE.exists():
            pid = int(self.PID_FILE.read_text().strip())
            try:
                os.kill(pid, 0)
                print(f"[Gatekeeper] Already running (PID {pid})")
                return
            except OSError:
                self.PID_FILE.unlink()

        if background:
            pid = os.fork()
            if pid > 0:
                print(f"[Gatekeeper] Started in background (PID {pid})")
                return
            os.setsid()

        self.PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.PID_FILE.write_text(str(os.getpid()))

        print(f"[Gatekeeper] Started (PID {os.getpid()})")
        print(f"[Gatekeeper] Config: {CONFIG_FILE}")
        print(f"[Gatekeeper] Pending dir: {PENDING_DIR}")

        try:
            self.server.start()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        print("\n[Gatekeeper] Shutting down...")
        self.server.stop()
        if self.PID_FILE.exists():
            self.PID_FILE.unlink()
        print(f"[Gatekeeper] Memory: {len(memory.data['approvals'])} approvals recorded")


# ============ CLI ============

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nStarting foreground...")
        Daemon().start(background=False)
        return

    cmd = sys.argv[1]

    if cmd == "--background":
        Daemon().start(background=True)
    elif cmd == "--stop":
        pid_file = Path("~/.hermes/run/gatekeeper.pid").expanduser()
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            try:
                os.kill(pid, sig_module.SIGTERM)
                print(f"[Gatekeeper] Stopped PID {pid}")
                pid_file.unlink()
            except OSError:
                print(f"[Gatekeeper] Process {pid} not found, cleaning up stale PID file")
                pid_file.unlink()
        else:
            print("[Gatekeeper] No PID file found — not running?")
    elif cmd == "--status":
        pid_file = Path("~/.hermes/run/gatekeeper.pid").expanduser()
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            try:
                os.kill(pid, 0)
                print(f"[Gatekeeper] Running (PID {pid})")
                print(f"  Config: {CONFIG_FILE}")
                print(f"  Pending: {pending.pending_count()} items")
                print(f"  Memory: {len(memory.data['approvals'])} approvals")
            except OSError:
                print(f"[Gatekeeper] Stale PID file (PID {pid} not running)")
        else:
            print("[Gatekeeper] Not running")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()