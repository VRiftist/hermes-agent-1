#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES HEARTBEAT DAEMON — Unified self-monitoring agent loop.

Replaces the old cron-based heartbeat_task_manager.py + heartbeat_monitor.py
with a single long-running daemon that handles:
  1. Memory palace task polling
  2. LLM task dispatch (via 30B orchestrator brain)
  3. Gateway health monitoring
  4. Auto-restart of dead child processes
  5. Periodic status reporting to Telegram

Usage:
  --mode daemon     Run continuously (for launchd/systemd)
  --mode once       Single cycle and exit (backward compat, cron fallback)
  --mode auto       Detect from TTY context

Install (macOS):
  cp scripts/com.lumenhub.heartbeat.plist ~/Library/LaunchAgents/
  launchctl load ~/Library/LaunchAgents/com.lumenhub.heartbeat.plist

Install (Linux):
  sudo cp scripts/hermes-heartbeat.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now hermes-heartbeat
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ─── Paths ──────────────────────────────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
HEARTBEAT_PATH = HERMES_HOME / "agent_heartbeat"
TASK_STATE_PATH = HERMES_HOME / "heartbeat_task_state.json"
LOG_DIR = HERMES_HOME / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── Logging ────────────────────────────────────────────────────────────────────────
# When SILENT_MODE is active, suppress stdout/stderr logging for cron (--mode once)
# to avoid routine output captured by the cron framework.
_LOG_LEVEL = logging.INFO
_LOG_HANDLERS = [logging.FileHandler(LOG_DIR / "heartbeat_daemon.log")]

if not (SILENT_MODE and ONCE_FLAG):
    _LOG_HANDLERS.append(logging.StreamHandler(sys.stdout))
else:
    _LOG_LEVEL = logging.WARNING

logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s [HEARTBEAT] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=_LOG_HANDLERS,
)
logger = logging.getLogger("heartbeat")

# ─── Config ─────────────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "120"))
TASK_CHECK_INTERVAL = int(os.environ.get("TASK_CHECK_INTERVAL", "300"))
STALE_THRESHOLD = int(os.environ.get("STALE_THRESHOLD", "240"))
TELEGRAM_SEND_URL = os.environ.get("TELEGRAM_SEND_URL", "")
SILENT_MODE = bool(int(os.environ.get("SILENT_MODE", "0")))
TASK_BATCH_LIMIT = int(os.environ.get("TASK_BATCH_LIMIT", "1"))
MAX_TASK_RUNTIME = int(os.environ.get("MAX_TASK_RUNTIME", "3600"))
GATEWAY_CHECK_INTERVAL = int(os.environ.get("GATEWAY_CHECK_INTERVAL", "60"))
MAX_RESTARTS_PER_HOUR = int(os.environ.get("MAX_RESTARTS_PER_HOUR", "3"))

# ─── CLI ────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Heartbeat Daemon — unified autonomous agent loop"
    )
    parser.add_argument(
        "--mode",
        choices=["once", "daemon", "auto"],
        default="auto",
        help=(
            "once:    Single cycle and exit (cron fallback, 65s cap)\n"
            "daemon:  Long-running with internal threads (launchd/systemd)\n"
            "auto:    Detect from TTY — non-TTY → once, TTY → daemon\n"
        ),
    )
    return parser.parse_args()


ARGS = parse_args()
ONCE_FLAG = ARGS.mode == "once" or (ARGS.mode == "auto" and not sys.stdin.isatty())
DAEMON_FLAG = ARGS.mode == "daemon" or (ARGS.mode == "auto" and sys.stdin.isatty())

if ONCE_FLAG:
    MAX_TASK_RUNTIME = min(MAX_TASK_RUNTIME, 65)
    TASK_BATCH_LIMIT = min(TASK_BATCH_LIMIT, 1)


# ─── State Management ───────────────────────────────────────────────────────

def load_state() -> dict:
    if TASK_STATE_PATH.exists():
        try:
            return json.loads(TASK_STATE_PATH.read_text())
        except Exception:
            return _default_state()
    return _default_state()


def _default_state() -> dict:
    return {
        "last_beat": 0,
        "last_task_check": 0,
        "last_health_check": 0,
        "current_task": None,
        "completed_tasks": [],
        "failed_tasks": [],
        "idle_cycles": 0,
        "total_completed": 0,
        "last_status_message": "",
        "gateway_restarts": 0,
        "restart_hour_start": datetime.now().hour,
    }


def save_state(state: dict):
    TASK_STATE_PATH.write_text(json.dumps(state, indent=2))


def touch_heartbeat():
    HEARTBEAT_PATH.write_text(str(time.time()))


# ─── Process Monitoring (replaces pgrep-based heartbeat_monitor.py) ─────────

def find_gateway_pid() -> Optional[int]:
    """Find gateway process by cmdline pattern using psutil."""
    try:
        import psutil
    except ImportError:
        # Fallback to subprocess-based search
        return _find_gateway_fallback()

    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if any("hermes_agent.cli" in arg for arg in cmdline):
                if "--gateway" in cmdline or any("gateway" in arg for arg in cmdline):
                    return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def _find_gateway_fallback() -> Optional[int]:
    """Fallback: use pgrep with correct pattern."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "hermes_agent.cli.*--gateway"],
            capture_output=True, text=True, timeout=5,
        )
        pids = [int(p.strip()) for p in result.stdout.strip().split("\n") if p.strip()]
        return pids[0] if pids else None
    except Exception:
        return None


def check_gateway_health() -> bool:
    pid = find_gateway_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def restart_gateway(state: dict) -> bool:
    """Restart gateway with hourly restart limit."""
    now_hour = datetime.now().hour
    if state.get("restart_hour_start", 0) != now_hour:
        state["gateway_restarts"] = 0
        state["restart_hour_start"] = now_hour

    if state["gateway_restarts"] >= MAX_RESTARTS_PER_HOUR:
        logger.error(f"Gateway restart limit ({MAX_RESTARTS_PER_HOUR}/hr) reached — alerting")
        send_telegram_status(
            "🔴 GATEWAY CRASH LOOP: Max restarts reached. Manual intervention needed.",
            force=True,
        )
        return False

    state["gateway_restarts"] += 1
    logger.info(f"🔄 Restarting gateway (restart #{state['gateway_restarts']}/{MAX_RESTARTS_PER_HOUR})")
    send_telegram_status(
        f"🔄 Gateway not responding — restarting (#{state['gateway_restarts']}/{MAX_RESTARTS_PER_HOUR})",
        force=True,
    )

    try:
        subprocess.Popen(
            [sys.executable, "-m", "hermes_agent.cli", "--gateway"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(HERMES_HOME),
        )
        time.sleep(5)
        if check_gateway_health():
            logger.info("✅ Gateway restarted successfully")
            send_telegram_status("✅ Gateway back online", force=True)
            return True
        else:
            logger.error("❌ Gateway restart failed")
            return False
    except Exception as e:
        logger.error(f"Gateway restart exception: {e}")
        return False


# ─── Memory Palace Integration ──────────────────────────────────────────────

def get_pending_tasks() -> list:
    try:
        sys.path.insert(0, str(HERMES_HOME))
        from memory_palace import get_working, recall_episodes

        queue = get_working("task_queue")
        if queue and isinstance(queue, list):
            active = [t for t in queue if t.get("status") in ("pending", "in_progress")]
            active.sort(key=lambda t: t.get("priority", 0), reverse=True)
            return active

        episodes = recall_episodes(hours=2, category="action", min_importance=3)
        tasks = []
        for ep in episodes:
            content = ep.get("content", "")
            if "task" in content.lower() or "TODO" in content:
                tasks.append({
                    "id": f"ep_{ep['id']}",
                    "description": content[:200],
                    "priority": ep.get("importance", 1),
                    "source": "episodic",
                    "status": "pending",
                })
        return tasks
    except Exception as e:
        logger.warning(f"Could not query memory palace: {e}")
        return []


# ─── Telegram ───────────────────────────────────────────────────────────────

def send_telegram_status(message: str, force: bool = False):
    if not TELEGRAM_SEND_URL:
        logger.debug("No TELEGRAM_SEND_URL — skipping Telegram update")
        return

    if SILENT_MODE and not force:
        logger.debug("Silent mode — suppressing routine status: %s", message[:60])
        return

    state = load_state()
    if not force and message == state.get("last_status_message"):
        return

    try:
        import shlex
        url = f"{TELEGRAM_SEND_URL}&text={shlex.quote(message)}"
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", url],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            logger.info(f"Telegram status sent: {message[:80]}...")
            state["last_status_message"] = message
            save_state(state)
        else:
            logger.warning(f"Telegram send failed: {result.stderr}")
    except Exception as e:
        logger.warning(f"Failed to send Telegram status: {e}")


# ─── Task Execution ─────────────────────────────────────────────────────────

def execute_task(task: dict) -> dict:
    task_id = task.get("id", "unknown")
    description = task.get("description", "Unnamed task")
    prompt = task.get("prompt", build_prompt_from_task(task))

    logger.info(f"🤖 Dispatching task {task_id}: {description[:100]}")

    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "hermes_agent",
                "--model", "qwen3-coder:30b",
                "--task", prompt,
                "--max-tokens", "4096",
                "--no-stream",
            ],
            capture_output=True, text=True,
            timeout=MAX_TASK_RUNTIME,
            cwd=str(HERMES_HOME),
        )
        if result.returncode == 0:
            logger.info(f"✅ Task {task_id} completed")
            return {
                "task_id": task_id, "status": "completed",
                "output": result.stdout[-2000:],
                "errors": result.stderr[-500:] if result.stderr else None,
                "returncode": 0, "model_used": "qwen3-coder:30b",
                "timestamp": time.time(),
            }
        else:
            logger.warning(f"⚠️ Task {task_id} failed (rc={result.returncode})")
            return {
                "task_id": task_id, "status": "failed",
                "output": result.stdout[-1000:],
                "errors": result.stderr[-500:] or f"Exit code: {result.returncode}",
                "returncode": result.returncode, "model_used": "qwen3-coder:30b",
                "timestamp": time.time(),
            }
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Task {task_id} timed out after {MAX_TASK_RUNTIME}s")
        return {
            "task_id": task_id, "status": "timeout",
            "output": None,
            "errors": f"Task timed out after {MAX_TASK_RUNTIME}s",
            "returncode": -1, "model_used": "qwen3-coder:30b",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"💀 Task {task_id} crashed: {e}")
        return {
            "task_id": task_id, "status": "crashed",
            "output": None, "errors": str(e), "returncode": -1,
            "model_used": "qwen3-coder:30b", "timestamp": time.time(),
        }


def build_prompt_from_task(task: dict) -> str:
    description = task.get("description", "")
    context = task.get("context", {})
    prompt_parts = [f"TASK: {description}"]
    if context:
        prompt_parts.append("\nCONTEXT:")
        for k, v in context.items():
            prompt_parts.append(f"  - {k}: {v}")
    prompt_parts.extend([
        "\nINSTRUCTIONS:",
        "  1. Complete the task as described",
        "  2. Log all actions to memory palace as episodic memories",
        "  3. Report results in structured format",
        "  4. If blocked, report what's needed to proceed",
    ])
    return "\n".join(prompt_parts)


# ─── Daemon Main Loop ───────────────────────────────────────────────────────

def run_single_cycle():
    """Execute one cycle: heartbeat → health check → task processing."""
    state = load_state()
    now = time.time()

    # 1. Touch heartbeat file
    touch_heartbeat()
    state["last_beat"] = now

    # 2. Check gateway health
    if not check_gateway_health():
        logger.warning("Gateway UNHEALTHY — attempting restart")
        restart_gateway(state)
    else:
        logger.debug("Gateway health: OK")

    # 3. Process tasks (only if enough time since last check)
    time_since_last = now - state.get("last_task_check", 0)
    if time_since_last >= TASK_CHECK_INTERVAL:
        state["last_task_check"] = now
        pending = get_pending_tasks()

        if pending:
            batch = pending[:TASK_BATCH_LIMIT]
            logger.info(f"📋 {len(pending)} pending tasks, processing {len(batch)}")

            for task in batch:
                task_id = task.get("id", "unknown")
                state["current_task"] = task_id
                save_state(state)

                result = execute_task(task)

                if result["status"] == "completed":
                    state["completed_tasks"].append(task_id)
                    state["total_completed"] += 1
                    logger.info(f"📝 Task {task_id} completed")
                    try:
                        from memory_palace import store_episode
                        store_episode(
                            session_id="heartbeat",
                            category="action",
                            content=f"Completed task: {task.get('description', task_id)}",
                            importance=5,
                        )
                    except Exception:
                        pass
                    send_telegram_status(
                        f"✅ Completed task #{len(state['completed_tasks'])}: "
                        f"{task.get('description', task_id)[:80]}"
                    )
                else:
                    state["failed_tasks"].append(task_id)
                    send_telegram_status(
                        f"❌ Task failed: {task.get('description', task_id)[:60]}"
                    )

                state["current_task"] = None
                save_state(state)
        else:
            state["idle_cycles"] += 1
            if state["idle_cycles"] % 10 == 0:
                send_telegram_status(
                    f"💤 Idle — {state['total_completed']} tasks completed so far. "
                    f"Daemon alive."
                )

    save_state(state)


def main():
    mode_label = {"once": "SINGLE CYCLE", "daemon": "DAEMON", "auto": "AUTO-DETECT"}
    logger.info("=" * 60)
    logger.info(f"🫀 HEARTBEAT DAEMON  [{mode_label.get(ARGS.mode, ARGS.mode)}]")
    if ARGS.mode == "auto":
        logger.info(f"   TTY → {'daemon' if DAEMON_FLAG else 'once (cron)'}")
    logger.info(f"   Task interval: {TASK_CHECK_INTERVAL}s | Health: {GATEWAY_CHECK_INTERVAL}s")
    logger.info(f"   Max task runtime: {MAX_TASK_RUNTIME}s | Batch: {TASK_BATCH_LIMIT}")
    logger.info(f"   Hermes home: {HERMES_HOME}")
    logger.info("=" * 60)

    # Graceful shutdown
    running = True
    def handle_signal(signum, frame):
        nonlocal running
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        running = False

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    if not ONCE_FLAG:
        state = load_state()
        send_telegram_status("🫀 Heartbeat daemon online. Monitoring tasks & gateway.", force=True)

    # Main loop
    cycle_count = 0
    last_health_check = 0
    try:
        while running:
            run_single_cycle()
            cycle_count += 1

            if ONCE_FLAG:
                logger.info(f"✅ Single cycle complete (cycle #{cycle_count})")
                break

            # Sleep in short intervals for responsive shutdown
            slept = 0
            sleep_target = min(HEARTBEAT_INTERVAL, GATEWAY_CHECK_INTERVAL)
            while slept < sleep_target and running:
                time.sleep(min(1, sleep_target - slept))
                slept += 1

    finally:
        if not ONCE_FLAG:
            send_telegram_status("⏹ Heartbeat daemon stopped.", force=True)
            logger.info("Heartbeat daemon stopped.")
        else:
            logger.info("🫁 Single-cycle mode finished.")


if __name__ == "__main__":
    main()