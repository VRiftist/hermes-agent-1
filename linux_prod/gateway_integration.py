"""
gateway_integration.py — Laravel Gateway ↔ Hermes bridge (Mac-local)
Handles the Telegram → Gateway → Ollama message flow.

Replaces the broken laravel-hermes-telegram package with direct
API calls over Unix socket (no SSH hop needed).

Usage:
    from gateway_integration import GatewayClient
    client = GatewayClient()
    await client.send_to_gateway("user_id", "Hello from Telegram")
"""

import json
import os
import socket
import time
from pathlib import Path
from typing import Optional

# Dynamic path resolution — never hard-coded
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("WORKSPACE", str(BASE_DIR.parent.parent)))

# Configuration via environment
GATEWAY_HOST = os.environ.get("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", "8080"))
GATEWAY_SOCKET = os.environ.get("GATEWAY_SOCKET", "/tmp/hermes-gateway.sock")
PACKAGE_TOKEN = os.environ.get("GATEWAY_PACKAGE_TOKEN", "")


class GatewayClient:
    """HTTP/Unix-socket client for the Laravel Hermes Gateway."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or f"http://{GATEWAY_HOST}:{GATEWAY_PORT}"
        self.use_unix_socket = os.environ.get("GATEWAY_USE_UNIX", "1") == "1"

    def send_to_gateway(self, user_id: str, message: str, context: dict | None = None) -> dict:
        """Send a message through the gateway to Ollama and return the response."""
        payload = {
            "user_id": user_id,
            "message": message,
            "context": context or {},
            "timestamp": time.time(),
        }

        if self.use_unix_socket:
            return self._send_unix(payload)
        return self._send_http(payload)

    def _send_unix(self, payload: dict) -> dict:
        """Send payload via Unix domain socket."""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(GATEWAY_SOCKET)
            sock.sendall((json.dumps(payload) + "\n").encode())

            # Read response (newline-delimited JSON)
            buffer = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                if b"\n" in buffer:
                    break
            sock.close()

            response = json.loads(buffer.decode().strip())
            return response
        except FileNotFoundError:
            return {"error": f"Socket not found: {GATEWAY_SOCKET}", "status": "disconnected"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {e}", "status": "error"}
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def _send_http(self, payload: dict) -> dict:
        """Send payload via HTTP."""
        try:
            import requests
            resp = requests.post(f"{self.base_url}/api/telegram", json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def health_check(self) -> bool:
        """Check if the gateway is reachable."""
        if self.use_unix_socket:
            return Path(GATEWAY_SOCKET).exists()
        try:
            import requests
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


class ContextBuffer:
    """Manages the rolling context window sent to Ollama via the gateway."""

    def __init__(self, max_tokens: int = 12000, trim_threshold: float = 0.8):
        self.max_tokens = max_tokens
        self.trim_threshold = trim_threshold
        self.messages: list[dict] = []
        self.current_tokens = 0

    def add(self, role: str, content: str, priority: int = 5) -> None:
        tokens = max(len(content.split()), len(content) // 4)
        self.messages.append({
            "role": role,
            "content": content,
            "priority": priority,
            "tokens": tokens,
            "timestamp": time.time(),
        })
        self.current_tokens += tokens

    def should_trim(self) -> bool:
        return self.current_tokens > (self.max_tokens * self.trim_threshold)

    def get_context(self) -> list[dict]:
        """Return sorted messages (highest priority last = most likely to be kept)."""
        return sorted(self.messages, key=lambda m: m["priority"])

    def trim(self, auto_trim_script: Path | None = None) -> dict:
        """Trigger auto-trim via signal file."""
        if auto_trim_script and isinstance(auto_trim_script, Path):
            signal_file = auto_trim_script.parent / "bridge" / "signals" / "trigger-trim.json"
            signal_file.parent.mkdir(parents=True, exist_ok=True)
            signal_file.write_text(json.dumps({
                "mode": "auto",
                "target_tokens": int(self.max_tokens * 0.6),
                "timestamp": time.time(),
            }))
            return {"status": "signal_sent", "target": int(self.max_tokens * 0.6)}
        return {"status": "no_script"}


# Convenience singleton for the gateway
def get_client() -> GatewayClient:
    return GatewayClient()