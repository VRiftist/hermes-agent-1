#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
Heartbeat Monitor for Hermes Agent
Monitors gateway health, auto-restarts, sends Telegram alerts.
"""
import os
import sys
import time
import signal
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path

CHECK_INTERVAL = 60
GATEWAY_TIMEOUT = 300
MAX_RESTARTS_PER_HOUR = 3
LOG_DIR = Path(os.path.expanduser("~/.hermes/logs"))
LOG_DIR.mkdir(exist_ok=True)
PID_FILE = Path(os.path.expanduser("~/.hermes/run/heartbeat.pid"))
STATE_FILE = Path(os.path.expanduser("~/.hermes/run/heartbeat_state.json"))

TG_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [heartbeat] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "heartbeat.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

RESTART_COUNT = 0
LAST_RESTART_HOUR = None


def send_telegram_alert(msg):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        log.warning(
            "Telegram not configured — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing. "
            "Run: inject_keys.py --target mac --keys TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID"
        )
        return
    try:
        import urllib.request
        payload = json.dumps({
            "chat_id": TG_CHAT_ID,
            "text": f"🔴 Hermes Heartbeat: {msg}",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"Telegram alert sent: {resp.status}")
    except Exception as e:
        log.error(f"Telegram alert failed: {e}")


def get_gateway_pid():
    """Get the gateway process PID.

    Primary: read from gateway_state.json (written by gateway itself).
    Fallback: pgrep (may not work from subprocess on macOS sandbox).
    """
    try:
        state_file = Path(os.path.expanduser("~/.hermes/gateway_state.json"))
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                pid = state.get("pid")
                if pid:
                    return int(pid)
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                pass

        # Fallback: pgrep
        result = subprocess.run(
            ["pgrep", "-f", "hermes_agent.cli.*--gateway"],
            capture_output=True, text=True, timeout=5
        )
        for p in result.stdout.strip().split("\n"):
            if p.strip():
                return int(p.strip())
    except Exception:
        pass
    return None


def check_gateway_health():
    pid = get_gateway_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def restart_gateway():
    global RESTART_COUNT, LAST_RESTART_HOUR
    now_hour = datetime.now().hour
    if LAST_RESTART_HOUR != now_hour:
        RESTART_COUNT = 0
        LAST_RESTART_HOUR = now_hour

    if RESTART_COUNT >= MAX_RESTARTS_PER_HOUR:
        log.error("Max restarts reached")
        send_telegram_alert("🚨 Max gateway restarts reached")
        return False

    log.info("Restarting Hermes gateway...")
    RESTART_COUNT += 1
    send_telegram_alert(f"Gateway down — restarting (#{RESTART_COUNT})")

    subprocess.Popen(
        [sys.executable, "-m", "hermes_agent.cli", "--gateway"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    time.sleep(5)

    if check_gateway_health():
        log.info("Gateway restarted successfully")
        send_telegram_alert("✅ Gateway back online")
        return True
    else:
        log.error("Gateway restart failed")
        return False


def save_state(state):
    try:
        STATE_FILE.parent.mkdir(exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({**state, "last_update": datetime.now().isoformat()}, f, indent=2)
    except Exception as e:
        log.error(f"Failed to save state: {e}")


def main():
    log.info("=" * 50)
    log.info("Hermes Heartbeat Monitor starting...")
    log.info(f"Interval: {CHECK_INTERVAL}s, Max restarts/hour: {MAX_RESTARTS_PER_HOUR}")
    log.info("=" * 50)

    consecutive_failures = 0
    last_activity = time.time()

    def shutdown(sig, frame):
        log.info("Heartbeat shutting down...")
        save_state({"status": "stopped", "pid": None})
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    PID_FILE.parent.mkdir(exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    while True:
        try:
            healthy = check_gateway_health()

            if healthy:
                consecutive_failures = 0
                last_activity = time.time()
                save_state({
                    "status": "healthy",
                    "pid": get_gateway_pid(),
                    "last_check": datetime.now().isoformat(),
                    "consecutive_failures": 0,
                    "restarts_this_hour": RESTART_COUNT,
                })
                log.debug("Gateway healthy (PID: %s)", get_gateway_pid())
            else:
                consecutive_failures += 1
                elapsed = int(time.time() - last_activity)
                log.warning("Gateway UNHEALTHY (failures: %d, elapsed: %ds)",
                            consecutive_failures, elapsed)
                save_state({
                    "status": "unhealthy",
                    "pid": None,
                    "last_check": datetime.now().isoformat(),
                    "consecutive_failures": consecutive_failures,
                    "restarts_this_hour": RESTART_COUNT,
                })

                if consecutive_failures >= 3:
                    restart_gateway()
                    consecutive_failures = 0
                    last_activity = time.time()

        except Exception as e:
            log.error(f"Heartbeat check failed: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()