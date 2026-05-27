#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
SESSION WATCHDOG — Dead man's switch for Hermes Agent.

Checks if the heartbeat file at ~/.hermes/agent_heartbeat is recent.
If the heartbeat is older than the stale threshold, alerts via Telegram.
Designed to run as a cron job (every 5 minutes) with --no-agent mode.

Usage:
  python3 session_watchdog.py              # Check once, alert if stale
  python3 session_watchdog.py --dry-run    # Check without sending alerts
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
HEARTBEAT_PATH = HERMES_HOME / "agent_heartbeat"
STALE_THRESHOLD = int(os.environ.get("STALE_THRESHOLD", "240"))  # 4 minutes
TELEGRAM_SEND_URL = os.environ.get("TELEGRAM_SEND_URL", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1767184775")


def send_alert(message: str, dry_run: bool = False) -> bool:
    """Send a Telegram alert. Returns True on success."""
    if dry_run:
        print(f"[DRY RUN] Would send: {message}", file=sys.stderr)
        return True

    if not TELEGRAM_SEND_URL:
        print("⚠ No TELEGRAM_SEND_URL set — cannot send alert", file=sys.stderr)
        return False

    try:
        import shlex
        url = f"{TELEGRAM_SEND_URL}&text={shlex.quote(message)}"
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", url],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"✅ Alert sent: {message[:80]}")
            return True
        else:
            print(f"❌ Alert failed: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ Alert exception: {e}", file=sys.stderr)
        return False


def check_heartbeat() -> tuple[bool, str, float | None]:
    """Check if heartbeat is recent. Returns (is_healthy, status_message, age_seconds)."""
    if not HEARTBEAT_PATH.exists():
        return False, "Heartbeat file MISSING — daemon may be dead", None

    try:
        mtime = HEARTBEAT_PATH.stat().st_mtime
        now = datetime.now(timezone.utc).timestamp()
        age = now - mtime

        if age > STALE_THRESHOLD:
            age_min = int(age) // 60
            return False, f"Heartbeat STALE — last beat {age_min}m ago (threshold: {STALE_THRESHOLD // 60}m)", age
        else:
            age_s = int(age)
            return True, f"Heartbeat OK — {age_s}s ago", age
    except OSError as e:
        return False, f"Heartbeat file error: {e}", None


def main():
    parser = argparse.ArgumentParser(description="Session watchdog — dead man's switch")
    parser.add_argument("--dry-run", action="store_true", help="Check without alerting")
    args = parser.parse_args()

    healthy, message, age = check_heartbeat()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"[{now_str}] Watchdog check: {'✅' if healthy else '🔴'} {message}")

    if not healthy:
        alert_msg = (
            f"🔴 HERMES WATCHDOG ALERT\n\n"
            f"Heartbeat check FAILED at {now_str}\n"
            f"Status: {message}\n"
            f"Action: Check launchd/systemd service status.\n"
            f"/logs — recent heartbeat daemon logs"
        )
        success = send_alert(alert_msg, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()