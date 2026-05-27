#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
KIMI DIRECT CLIENT — Moonshot AI API with dual-key rotation & exponential backoff
Designed for the "temperamental artist" — high usage causes rate limits,
not key failures. Rotates between two keys on 429/401 before backing off.

Uses DIRECT api.moonshot.cn endpoint (NOT OpenRouter proxy).
"""
import os, sys, json, time, random, logging
import urllib.request
import urllib.error

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from api_error_handler import classify_api_error

KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"

# Retry config
MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_DELAY = 60.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
KEY_ROTATE_ON = {401, 429}  # rotate to secondary key on these

# ── Key Management ────────────────────────────────────────────────

def _get_keys() -> list:
    """Load all Kimi keys from .env vault in priority order."""
    env_path = os.path.expanduser("~/.hermes/.env")
    keys = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("KIMI_API_KEY=") or line.startswith("KIMI_API_KEY_2="):
                    val = line.split("=", 1)[1]
                    if val and val not in ("***", "") and not val.startswith("#"):
                        keys.append(val)
    return keys


_keys = _get_keys()
_primary_key = _keys[0] if len(_keys) > 0 else None
_secondary_key = _keys[1] if len(_keys) > 1 else None
_active_key_index = 0  # 0 = primary, 1 = secondary


def is_available() -> bool:
    """Check if Kimi can be used right now (has at least one valid key loaded)."""
    return bool(_primary_key and _primary_key not in ("***", ""))


def _get_active_key() -> str:
    global _active_key_index
    if _active_key_index == 0:
        return _primary_key
    return _secondary_key or _primary_key


def _rotate_key():
    """Switch to the other key. Returns True if rotation happened."""
    global _active_key_index
    if _secondary_key:
        _active_key_index = 1 - _active_key_index
        logging.info(f"Kimi key rotated → index {_active_key_index}")
        return True
    return False


def _reset_key_rotation():
    """Reset back to primary key after cooldown."""
    global _active_key_index
    _active_key_index = 0


# ── Core Request ────────────────────────────────────────────────────

def _make_request(endpoint: str, payload: dict, retries: int = 0, key_rotated: bool = False) -> dict:
    """Make HTTP request with exponential backoff + key rotation."""
    key = _get_active_key()
    if not key or key in ("***", ""):
        return {"error": "NO_KIMI_KEY", "message": "No valid KIMI_API_KEY in .env vault"}

    url = f"{KIMI_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            _reset_key_rotation()
            return json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""

        # Rate limit or key issue → try key rotation before backoff
        if status in KEY_ROTATE_ON and not key_rotated and _secondary_key:
            logging.warning(f"Kimi HTTP {status} on key {_get_active_key()[:12]}... — rotating key")
            _rotate_key()
            return _make_request(endpoint, payload, retries=retries, key_rotated=True)

        # Standard exponential backoff
        if status in RETRYABLE_STATUS_CODES and retries < MAX_RETRIES:
            delay = min(BASE_DELAY * (2 ** retries), MAX_DELAY)
            jitter = delay * 0.1
            delay += random.uniform(-jitter, jitter)
            logging.warning(f"Kimi HTTP {status}, retry {retries+1}/{MAX_RETRIES} in {delay:.1f}s...")
            time.sleep(delay)
            return _make_request(endpoint, payload, retries + 1, key_rotated=key_rotated)

        return {
            "error": f"HTTP_{status}",
            "message": f"Kimi API: {status} — {body[:500]}",
            "status_code": status,
        }

    except Exception as e:
        if retries < MAX_RETRIES:
            delay = min(BASE_DELAY * (2 ** retries), MAX_DELAY)
            logging.warning(f"Kimi network error: {e}, retry {retries+1}/{MAX_RETRIES}")
            time.sleep(delay)
            return _make_request(endpoint, payload, retries + 1, key_rotated=key_rotated)
        return {"error": "NETWORK_ERROR", "message": str(e)}


# ── Public API ────────────────────────────────────────────────────

def chat_completion(messages: list, model: str = None, temperature: float = 0.7,
                    max_tokens: int = 4096) -> dict:
    """Chat completion via Kimi (direct Moonshot API)."""
    payload = {
        "model": model or KIMI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return _make_request("/chat/completions", payload)


def models() -> dict:
    """List available models on this key."""
    key = _get_active_key()
    if not key or key in ("***", ""):
        return {"error": "NO_KIMI_KEY"}
    try:
        req = urllib.request.Request(
            f"{KIMI_BASE_URL}/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"note": "Moonshot /models endpoint not publicly accessible", "error": str(e)[:200]}


def health_check() -> dict:
    """Lightweight health check — returns key status without hitting API hard."""
    key = _get_active_key()
    if not key or key in ("***", ""):
        return {"status": "no_key", "message": "No KIMI_API_KEY in .env"}

    # Only do a real API check if explicitly called for validation
    return {
        "status": "configured",
        "provider": "moonshot_direct",
        "primary_key_loaded": bool(_primary_key and _primary_key not in ("***", "")),
        "secondary_key_loaded": bool(_secondary_key and _secondary_key not in ("***", "")),
        "model": KIMI_MODEL,
    }


def validate_key() -> dict:
    """Full validation — makes a real API call. Use sparingly."""
    result = chat_completion(
        messages=[{"role": "user", "content": "Say 'kimivalid'"}],
        model=KIMI_MODEL,
        max_tokens=5,
        temperature=0.0,
    )
    if "error" in result:
        return {"valid": False, "detail": result}
    return {"valid": True, "detail": "Kimi responded successfully"}


def status() -> dict:
    """Summary of Kimi client state."""
    return {
        "keys_loaded": len([k for k in _get_keys() if k and k not in ("***", "")]),
        "active_key_index": _active_key_index,
        "model": KIMI_MODEL,
        "retry_config": {
            "max_retries": MAX_RETRIES,
            "base_delay": BASE_DELAY,
            "max_delay": MAX_DELAY,
            "rotate_on": list(KEY_ROTATE_ON),
        },
    }


# ── Self-Test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("KIMI DIRECT CLIENT — STATUS CHECK\n")

    st = status()
    print(f"Keys loaded:        {st['keys_loaded']}")
    print(f"Active key index:   {st['active_key_index']}")
    print(f"Model:              {st['model']}")
    print(f"Retry max:          {st['retry_config']['max_retries']}")
    print(f"Rotate on:          {st['retry_config']['rotate_on']}")
    print(f"Primary key:        {_primary_key[:20] if _primary_key else '(none)'}...")
    print(f"Secondary key:      {_secondary_key[:20] if _secondary_key else '(none)'}...")
    print("\n✅ Kimi client configured — keys are loaded, NO API calls made.")
    print("   Call validate_key() or chat_completion() to hit the live API.")