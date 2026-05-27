#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
Heartbeat Task Manager — the agent's autonomous task loop.

Replaces the simple `heartbeat_pulse.sh` with a task-aware heartbeat that:
1. Checks the memory palace for pending/active tasks
2. If tasks exist: picks highest priority, routes to 30B, tracks progress
3. If no tasks: logs idle, sends periodic "waiting" heartbeat
4. Reports status to Telegram on state changes
5. Auto-restarts the gateway if stale heartbeat detected

Architecture role: THIS IS THE ORCHESTRATOR LOOP.
30B is the grinder. This script is the conductor.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import signal
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ─── Paths ──────────────────────────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HOME", "")) / ".hermes"
HEARTBEAT_PATH = HERMES_HOME / "agent_heartbeat"
TASK_STATE_PATH = HERMES_HOME / "heartbeat_task_state.json"
LOG_DIR = HERMES_HOME / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HEARTBEAT] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "heartbeat.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("heartbeat")

# ─── Config ─────────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "120"))       # seconds between beats
TASK_CHECK_INTERVAL = int(os.environ.get("TASK_CHECK_INTERVAL", "300"))      # seconds between task polls
STALE_THRESHOLD = int(os.environ.get("STALE_THRESHOLD", "240"))              # seconds before watchdog alerts
TELEGRAM_SEND_URL = os.environ.get("TELEGRAM_SEND_URL", "")                  # pre-built curl URL prefix
TASK_BATCH_LIMIT = int(os.environ.get("TASK_BATCH_LIMIT", "5"))              # max tasks per cycle
MAX_TASK_RUNTIME = int(os.environ.get("MAX_TASK_RUNTIME", "3600"))           # seconds before task is considered stuck


# ─── State Management ───────────────────────────────────────────────────

def load_state() -> dict:
    """Load persistent heartbeat state from disk."""
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
        "current_task": None,
        "completed_tasks": [],
        "failed_tasks": [],
        "idle_cycles": 0,
        "total_completed": 0,
        "last_status_message": "",
        "gateway_restarts": 0,
    }


def save_state(state: dict):
    """Persist heartbeat state to disk."""
    TASK_STATE_PATH.write_text(json.dumps(state, indent=2))


def touch_heartbeat():
    """Update the heartbeat timestamp file."""
    HEARTBEAT_PATH.write_text(str(time.time()))


# ─── Memory Palace Integration ──────────────────────────────────────────

def get_pending_tasks() -> list:
    """
    Query the memory palace for pending tasks.
    Returns list of task dicts sorted by priority (highest first).
    """
    try:
        # Add HERMES_HOME to path so memory_palace can be imported
        sys.path.insert(0, str(HERMES_HOME))
        from memory_palace import get_working, recall_episodes

        # Check working memory for active task queue
        queue = get_working("task_queue")
        if queue and isinstance(queue, list):
            active = [t for t in queue if t.get("status") in ("pending", "in_progress")]
            # Sort by priority (higher number = higher priority)
            active.sort(key=lambda t: t.get("priority", 0), reverse=True)
            return active

        # Fallback: check episodic memory for recently assigned tasks
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
        logger.warning(f"Could not query memory palace for tasks: {e}")
        return []


def get_completed_recently(hours: float = 1) -> list:
    """Check what tasks have been completed recently."""
    try:
        sys.path.insert(0, str(HERMES_HOME))
        from memory_palace import recall_episodes

        episodes = recall_episodes(hours=hours, category="action")
        return [ep for ep in episodes if "completed" in ep.get("content", "").lower()]
    except Exception:
        return []


# ─── Telegram ───────────────────────────────────────────────────────────

def send_telegram_status(message: str, force: bool = False):
    """Send a status update to Telegram."""
    if not TELEGRAM_SEND_URL:
        logger.debug("No TELEGRAM_SEND_URL configured, skipping Telegram update")
        return

    # Avoid sending duplicate messages
    state = load_state()
    if not force and message == state.get("last_status_message"):
        logger.debug("Duplicate status message, skipping")
        return

    try:
        import shlex
        url = f"{TELEGRAM_SEND_URL}&text={shlex.quote(message)}"
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            logger.info(f"Telegram status sent: {message[:80]}...")
            state["last_status_message"] = message
            save_state(state)
        else:
            logger.warning(f"Telegram send failed: {result.stderr}")
    except Exception as e:
        logger.warning(f"Failed to send Telegram status: {e}")


# ─── 30B Task Execution ────────────────────────────────────────────────

def execute_task_with_30b(task: dict) -> dict:
    """
    Route a task to 30B for execution via the CLI.
    Returns result dict with status, output, and metadata.
    """
    task_id = task.get("id", "unknown")
    description = task.get("description", "Unnamed task")

    logger.info(f"🤖 Dispatching task {task_id} to 30B: {description[:100]}")

    # Build the hermes command for this task
    # Uses local 30B model via olla/llama.cpp
    prompt = task.get("prompt", build_prompt_from_task(task))

    try:
        # Execute via hermes CLI in batch mode
        # This delegates to 30B as the primary orchestrator brain
        result = subprocess.run(
            [
                sys.executable, "-m", "hermes_agent",
                "--model", "qwen3-coder:30b",
                "--task", prompt,
                "--max-tokens", "4096",
                "--no-stream",
            ],
            capture_output=True,
            text=True,
            timeout=MAX_TASK_RUNTIME,
            cwd=str(HERMES_HOME),
        )

        output = result.stdout
        errors = result.stderr
        returncode = result.returncode

        if returncode == 0:
            logger.info(f"✅ Task {task_id} completed by 30B")
            return {
                "task_id": task_id,
                "status": "completed",
                "output": output[-2000:],  # Trim to last 2K chars
                "errors": errors[-500:] if errors else None,
                "returncode": 0,
                "model_used": "qwen3-coder:30b",
                "timestamp": time.time(),
            }
        else:
            logger.warning(f"⚠️ Task {task_id} failed (rc={returncode})")
            return {
                "task_id": task_id,
                "status": "failed",
                "output": output[-1000:],
                "errors": errors[-500:] if errors else f"Exit code: {returncode}",
                "returncode": returncode,
                "model_used": "qwen3-coder:30b",
                "timestamp": time.time(),
            }

    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Task {task_id} timed out after {MAX_TASK_RUNTIME}s")
        return {
            "task_id": task_id,
            "status": "timeout",
            "output": None,
            "errors": f"Task timed out after {MAX_TASK_RUNTIME} seconds",
            "returncode": -1,
            "model_used": "qwen3-coder:30b",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"💀 Task {task_id} crashed: {e}")
        return {
            "task_id": task_id,
            "status": "crashed",
            "output": None,
            "errors": str(e),
            "returncode": -1,
            "model_used": "qwen3-coder:30b",
            "timestamp": time.time(),
        }


def build_prompt_from_task(task: dict) -> str:
    """Construct a clear prompt from a task definition."""
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


# ─── Gateway Health ────────────────────────────────────────────────────

def check_gateway_health() -> bool:
    """Check if the gateway process is alive and responsive."""
    try:
        # Primary method: read PID from gateway_state.json and verify via kill -0
        state_file = HERMES_HOME / "gateway_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                pid = state.get("pid")
                if pid:
                    result = subprocess.run(
                        ["kill", "-0", str(pid)], capture_output=True, timeout=3
                    )
                    if result.returncode == 0:
                        return True
                    logger.warning(f"Gateway PID {pid} from state file not responding")
                    return False
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        # Fallback: try pgrep (may not work from subprocess on macOS)
        result = subprocess.run(
            ["pgrep", "-f", "start_gateway"],
            capture_output=True, text=True, timeout=5
        )
        pids = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        for pid_str in pids:
            try:
                subprocess.run(["kill", "-0", pid_str], capture_output=True, timeout=3)
                return True
            except Exception:
                continue

        # Last resort: check the pid file
        pid_file = HERMES_HOME / "gateway.pid"
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            result = subprocess.run(
                ["kill", "-0", str(pid)], capture_output=True
            )
            if result.returncode == 0:
                return True
            logger.warning(f"Gateway PID {pid} not responding")
            return False
    except Exception as e:
        logger.debug(f"Gateway health check: {e}")
    return False


def restart_gateway():
    """Restart the gateway process if it's dead."""
    state = load_state()
    state["gateway_restarts"] += 1

    if state["gateway_restarts"] >= 3:
        logger.error("Gateway has restarted 3 times — alerting Gerald via Telegram")
        send_telegram_status(
            "🔴 GATEWAY CRASH LOOP: Gateway has restarted 3 times. Manual intervention needed.",
            force=True
        )
        return

    logger.info("🔄 Restarting gateway process...")
    send_telegram_status(
        f"🔄 Gateway not responding (restart #{state['gateway_restarts']}). Auto-restarting...",
        force=True
    )

    try:
        # Start gateway in background
        subprocess.Popen(
            [sys.executable, "-m", "hermes_agent", "gateway", "--start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(HERMES_HOME),
        )
        time.sleep(5)  # Give it time to start
        save_state(state)
    except Exception as e:
        logger.error(f"Failed to restart gateway: {e}")


# ─── Main Loop ─────────────────────────────────────────────────────────

def run_task_cycle():
    """Execute one cycle of task checking and processing."""
    state = load_state()
    now = time.time()

    # Check if it's time to look for tasks
    time_since_last_check = now - state.get("last_task_check", 0)
    if time_since_last_check < TASK_CHECK_INTERVAL:
        return state  # Not time yet

    state["last_task_check"] = now

    # Look for pending tasks
    pending = get_pending_tasks()

    if pending:
        # Process up to TASK_BATCH_LIMIT tasks
        batch = pending[:TASK_BATCH_LIMIT]
        logger.info(f"📋 Found {len(pending)} pending tasks, processing {len(batch)}")

        for task in batch:
            task_id = task.get("id", "unknown")

            # Mark as in_progress in memory palace
            try:
                sys.path.insert(0, str(HERMES_HOME))
                from memory_palace import set_working
                set_working(f"task_{task_id}", {
                    "status": "in_progress",
                    "started_at": now,
                    "description": task.get("description", ""),
                })
            except Exception:
                pass

            state["current_task"] = task_id
            save_state(state)

            # Execute the task through 30B
            result = execute_task_with_30b(task)

            # Log result
            if result["status"] == "completed":
                state["completed_tasks"].append(task_id)
                state["total_completed"] += 1
                logger.info(f"📝 Task {task_id} completed — updating memory palace")

                # Store in memory palace
                try:
                    from memory_palace import store_episode, set_working
                    store_episode(
                        session_id="heartbeat",
                        category="action",
                        content=f"Completed task: {task.get('description', task_id)}",
                        context={"result": result, "model": "30b"},
                        importance=5,
                    )
                    set_working(f"task_{task_id}", {
                        "status": "completed",
                        "completed_at": now,
                        "result": result,
                    })
                except Exception:
                    pass

                send_telegram_status(
                    f"✅ Completed task #{len(state['completed_tasks'])}: {task.get('description', task_id)[:80]}"
                )
            else:
                state["failed_tasks"].append(task_id)
                logger.warning(f"❌ Task {task_id} failed: {result.get('errors', 'unknown')}")

                try:
                    from memory_palace import store_episode
                    store_episode(
                        session_id="heartbeat",
                        category="error",
                        content=f"Failed task: {task.get('description', task_id)} — {result.get('errors', 'unknown')}",
                        context={"result": result},
                        importance=7,
                    )
                except Exception:
                    pass

            state["current_task"] = None
            save_state(state)
    else:
        # No tasks — idle
        state["idle_cycles"] += 1

        # Send periodic idle status (every 10 idle cycles ≈ every ~17 min)
        if state["idle_cycles"] % 10 == 0:
            total = state["total_completed"]
            send_telegram_status(
                f"💤 Idle — waiting for tasks. Completed {total} so far. "
                f"Heartbeat alive. 30B on standby."
            )
        logger.debug(f"Idle cycle {state['idle_cycles']} — no tasks in queue")

    save_state(state)
    return state


def run_heartbeat_cycle():
    """Run a single heartbeat: touch file, check gateway, process tasks."""
    now = time.time()
    state = load_state()

    # 1. Touch heartbeat file
    touch_heartbeat()
    state["last_beat"] = now

    # 2. Check gateway health
    if not check_gateway_health():
        logger.warning("Gateway health check failed")
        restart_gateway()

    # 3. Run task cycle
    state = run_task_cycle()

    save_state(state)


# ─── CLI ──────────────────────────────────────────────────────────────────

def parse_args():
    """Parse command-line arguments for heartbeat mode."""
    parser = argparse.ArgumentParser(
        description="Heartbeat Task Manager — autonomous task loop"
    )
    parser.add_argument(
        "--mode",
        choices=["once", "daemon", "auto"],
        default="auto",
        help=(
            "once:    Run a single cycle and exit (for cron, 65s cap, batch=1)\n"
            "daemon:  Run continuously with sleep loop (for launchd/systemd)\n"
            "auto:    Detect from context — TTY → daemon, non-TTY/cron → once\n"
        ),
    )
    return parser.parse_args()


ARGS = parse_args()

ONCE_FLAG = ARGS.mode == "once" or (
    ARGS.mode == "auto"
    and not sys.stdin.isatty()
)
DAEMON_FLAG = ARGS.mode == "daemon" or (
    ARGS.mode == "auto" and sys.stdin.isatty()
)

# In --once mode (cron), cap resource limits so the framework's 120s wall
# doesn't kill us mid-task.  Leaves ~50s headroom after subprocess for
# save_state + teardown.
if ONCE_FLAG:
    MAX_TASK_RUNTIME = min(MAX_TASK_RUNTIME, 65)
    TASK_BATCH_LIMIT = min(TASK_BATCH_LIMIT, 1)


def main():
    """Main heartbeat loop. With --mode once, run a single cycle and exit."""
    mode_label = {"once": "SINGLE CYCLE", "daemon": "DAEMON", "auto": "AUTO-DETECT"}
    logger.info("=" * 60)
    logger.info(f"🫀 HEARTBEAT TASK MANAGER  [{mode_label.get(ARGS.mode, ARGS.mode)}]")
    if ARGS.mode == "auto":
        logger.info(f"   TTY detected → {'daemon' if DAEMON_FLAG else 'once (cron)'}")
    logger.info(f"   Max task runtime: {MAX_TASK_RUNTIME}s | Batch limit: {TASK_BATCH_LIMIT}")
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
        # Initialize state
        state = load_state()
        send_telegram_status(
            "🫀 Heartbeat task manager online. Monitoring for tasks.",
            force=True
        )

    # Run cycles
    cycle_count = 0
    try:
        while running:
            try:
                run_heartbeat_cycle()
                cycle_count += 1

                if ONCE_FLAG:
                    logger.info(f"✅ Single cycle complete (cycle #{cycle_count})")
                    break

                # Sleep in short intervals so we can respond to signals quickly
                slept = 0
                while slept < HEARTBEAT_INTERVAL and running:
                    time.sleep(min(1, HEARTBEAT_INTERVAL - slept))
                    slept += 1

            except Exception:
                logger.error(f"Heartbeat cycle error:\n{traceback.format_exc()}")
                if ONCE_FLAG:
                    raise
                time.sleep(5)  # Brief pause before retrying
    finally:
        if not ONCE_FLAG:
            # Shutdown
            send_telegram_status("⏹ Heartbeat task manager stopped.", force=True)
            logger.info("Heartbeat task manager stopped.")
        else:
            logger.info("🫁 Heartbeat single-cycle mode finished.")


if __name__ == "__main__":
    main()