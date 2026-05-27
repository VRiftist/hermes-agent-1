#!/usr/bin/env python3
"""
hermes_wrapper.py — Consolidated entry point for Hermes Agent on Linux.

Handles .env loading (with box-drawing char stripping), validation,
auto-trimmer integration, and exec() of the main bridge process.
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path

# ─── Resolve paths ────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("WORKSPACE", str(SCRIPT_DIR.parent)))
PIPELINE_DIR = WORKSPACE  # root of the hermes-pipeline repo

# ─── .env loading with Unicode stripping ──────────────────────────────────────

def strip_unicode_box_chars(text: str) -> str:
    """Replace Unicode box-drawing characters (U+2500-U+257F) with ASCII."""
    replacements = {
        '\u2500': '=',  # ─  BOX DRAWINGS LIGHT HORIZONTAL
        '\u2501': '=',  # ━  BOX DRAWINGS HEAVY HORIZONTAL
        '\u2502': '|',  # │  BOX DRAWINGS LIGHT VERTICAL
        '\u2503': '|',  # ┃  BOX DRAWINGS HEAVY VERTICAL
        '\u253c': '+',  # ┼  BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL
        '\u2510': '+',  # ┐  BOX DRAWINGS LIGHT DOWN AND LEFT
        '\u250c': '+',  # ┌  BOX DRAWINGS LIGHT DOWN AND RIGHT
        '\u2518': '+',  # ┘  BOX DRAWINGS LIGHT UP AND LEFT
        '\u2514': '+',  # └  BOX DRAWINGS LIGHT UP AND RIGHT
        '\u251c': '+',  # ├  BOX DRAWINGS LIGHT VERTICAL AND RIGHT
        '\u2524': '+',  # ┤  BOX DRAWINGS LIGHT VERTICAL AND LEFT
        '\u252c': '+',  # ┬  BOX DRAWINGS LIGHT DOWN AND HORIZONTAL
        '\u2534': '+',  # ┴  BOX DRAWINGS UP AND HORIZONTAL
        '\u2550': '=',  # ═  BOX DRAWINGS DOUBLE HORIZONTAL
        '\u2551': '|',  # ║  BOX DRAWINGS DOUBLE VERTICAL
    }
    for uni, ascii_char in replacements.items():
        text = text.replace(uni, ascii_char)
    return text


def load_env():
    """Load .env file with safe handling of Unicode characters."""
    env_file = PIPELINE_DIR / ".env"
    if not env_file.exists():
        print("[Wrapper] No .env file found at %s — using existing environment", file=sys.stderr)
        return

    content = env_file.read_text(encoding="utf-8")
    content = strip_unicode_box_chars(content)

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        eq_idx = line.find("=")
        if eq_idx <= 0:
            continue
        key = line[:eq_idx].strip()
        value = line[eq_idx + 1:].strip().strip('"').strip("'")
        # Skip placeholders
        if value.startswith("[REDACTED]") or value == "your_token_here":
            print(f"[Wrapper] Skipping placeholder: {key}")
            continue
        os.environ[key] = value
        print(f"[Wrapper] Loaded: {key}")

    # Validate required vars
    required = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_IDS"]
    for var in required:
        val = os.environ.get(var, "")
        if not val or val.startswith("["):
            print(f"[Wrapper] ⚠️  {var} not properly set in .env", file=sys.stderr)


# ─── Signal handling ──────────────────────────────────────────────────────────

child_proc = None

def shutdown(sig, frame):
    global child_proc
    print(f"\n[Wrapper] Received signal {sig}, shutting down...")
    if child_proc:
        child_proc.terminate()
        try:
            child_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child_proc.kill()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)


# ─── Subprocess helpers ───────────────────────────────────────────────────────

def kill_existing():
    """Kill any existing hermes bridge processes."""
    import shutil
    for tool in ["pkill", "killall"]:
        proc_path = shutil.which(tool)
        if proc_path:
            subprocess.run(
                [tool, "-f", "run_bridge.py"],
                capture_output=True, timeout=5
            )
            break


def run_auto_trim():
    """Run the context trimmer if trigger file exists or enough time has passed."""
    trim_script = PIPELINE_DIR / "scripts" / "auto_trim.py"
    if not trim_script.exists():
        print("[Wrapper] auto_trim.py not found, skipping trim")
        return

    trigger = PIPELINE_DIR / "bridge" / "signals" / "trigger-trim.json"
    if trigger.exists():
        print("[Wrapper] Trigger file found, running auto_trim.py...")
        result = subprocess.run(
            [sys.executable, str(trim_script), "--dry-run"],
            capture_output=True, text=True, timeout=120,
            cwd=str(PIPELINE_DIR)
        )
        print(result.stdout[-500:] if result.stdout else "")
        if result.stderr:
            print("[Wrapper/Trim]", result.stderr[:500])
    else:
        print("[Wrapper] No trim trigger file — skipping")


def run_validation():
    """Run pipeline validation."""
    validate_script = PIPELINE_DIR / "scripts" / "run_tests.sh"
    if validate_script.exists():
        print("[Wrapper] Running pipeline validation...")
        result = subprocess.run(
            ["bash", str(validate_script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(PIPELINE_DIR)
        )
        print(result.stdout[-2000:] if result.stdout else "")
        if result.stderr:
            print("[Wrapper/Validate]", result.stderr[:500])
    else:
        print("[Wrapper] No run_tests.sh found, skipping validation")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  HERMES WRAPPER — Linux Pipeline Entry Point")
    print("=" * 60)
    print()

    # 1. Load environment
    print("[Wrapper] Loading .env...")
    load_env()
    print()

    # 2. Validate basic setup
    print("[Wrapper] Checking paths...")
    bridge = PIPELINE_DIR / "run_bridge.py"
    if not bridge.exists():
        print(f"❌ run_bridge.py not found at {bridge}", file=sys.stderr)
        sys.exit(1)
    print(f"  ✅ Pipeline root: {PIPELINE_DIR}")
    print(f"  ✅ Bridge script: {bridge}")
    print()

    # 3. Kill stale processes (cleanup from previous crashes)
    print("[Wrapper] Cleaning stale processes...")
    kill_existing()
    print()

    # 4. Run auto-trimmer if triggered
    print("[Wrapper] Running auto-trimmer check...")
    run_auto_trim()
    print()

    # 5. Launch main bridge
    print("[Wrapper] Starting run_bridge.py --standalone...")
    print("-" * 60)

    global child_proc
    child_proc = subprocess.Popen(
        [sys.executable, str(bridge), "--standalone", "--telegram"],
        cwd=str(PIPELINE_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    try:
        rc = child_proc.wait()
    except KeyboardInterrupt:
        shutdown(None, None)
    finally:
        child_proc = None

    print(f"[Wrapper] Bridge exited with code {rc}")
    sys.exit(rc)


if __name__ == "__main__":
    main()