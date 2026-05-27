#!/usr/bin/env python3
"""
run_bridge.py - Unified process manager & pre-flight validator
Runs the full Telegram -> Gateway -> Ollama pipeline on a single machine.

Usage:
    python3 run_bridge.py --validate         # Pre-flight checks
    python3 run_bridge.py --with-gatekeeper  # Full pipeline + telegram bridge
    python3 run_bridge.py --standalone       # Telegram + Ollama (linux fallback)
    python3 run_bridge.py --gateway-only     # Gateway + Ollama (no gatekeeper)
    python3 run_bridge.py --dry-run          # Validate only, start nothing
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

import requests

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("WORKSPACE", str(BASE_DIR.parent.parent)))
LOGS_DIR = WORKSPACE / "logs" / "bridge"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_FILES = [
    "scripts/auto_trim.py",
    "gateway_integration.py",
    "telegram_bridge.py",
    "gatekeeper.py",
    "test_pipeline.py",
]

REQUIRED_ENVS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_IDS",
]

PORTS_MUST_BE_FREE = {
    8080: "Gateway HTTP",
}

PORTS_MUST_RESPOND = {
    11434: "Ollama API",
}


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print("[%s] [%s] %s" % (ts, level, msg))


def check_file(name):
    path = BASE_DIR / name
    if not path.exists():
        return False, "Missing: %s" % name
    if path.stat().st_size == 0:
        return False, "Empty file: %s (0 bytes)" % name
    return True, "OK: %s (%d bytes)" % (name, path.stat().st_size)


def check_env(name):
    val = os.environ.get(name)
    if not val:
        return False, "Missing env: %s" % name
    if val.startswith("[REDACTED]") or val.startswith("REPLACE"):
        return False, "Placeholder value: %s - set real value" % name
    return True, "OK: %s=%s" % (name, "*" * min(len(val), 8))


def check_port_free(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    if result == 0:
        return False, "Port %d already in use" % port
    return True, "Port %d available" % port


def check_port_responding(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    if result == 0:
        return True, "Port %d responding" % port
    return False, "Port %d not responding" % port


def check_ollama():
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code != 200:
            return False, "Ollama returned HTTP %d" % resp.status_code
        data = resp.json()
        models = data.get("models", [])
        if not models:
            return False, "Ollama running but no models pulled."
        names = [m["name"] for m in models]
        return True, "Ollama OK - models: %s" % ", ".join(names)
    except requests.exceptions.ConnectionError:
        return False, "Ollama not running on port 11434"
    except Exception as e:
        return False, "Ollama check error: %s" % e


def validate():
    log("=" * 60)
    log("VALIDATION - Pre-flight checks")
    log("=" * 60)

    all_pass = True

    log("")
    log("--- Files ---")
    for f in REQUIRED_FILES:
        ok, msg = check_file(f)
        log("  [%s] %s" % ("OK" if ok else "FAIL", msg))
        if not ok:
            all_pass = False

    log("")
    log("--- Environment ---")
    for e in REQUIRED_ENVS:
        ok, msg = check_env(e)
        log("  [%s] %s" % ("OK" if ok else "FAIL", msg))
        if not ok:
            all_pass = False

    log("")
    log("--- Ports (must be free) ---")
    for port, label in PORTS_MUST_BE_FREE.items():
        ok, msg = check_port_free(port)
        log("  [%s] %s (%s)" % ("OK" if ok else "FAIL", msg, label))
        if not ok:
            all_pass = False

    log("")
    log("--- Ports (must be responding) ---")
    for port, label in PORTS_MUST_RESPOND.items():
        ok, msg = check_port_responding(port)
        log("  [%s] %s (%s)" % ("OK" if ok else "FAIL", msg, label))
        if not ok:
            all_pass = False

    log("")
    log("--- Ollama ---")
    ok, msg = check_ollama()
    log("  [%s] %s" % ("OK" if ok else "FAIL", msg))
    if not ok:
        all_pass = False

    log("")
    log("--- Test Pipeline ---")
    test_file = BASE_DIR / "test_pipeline.py"
    if test_file.exists() and test_file.stat().st_size > 0:
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True, text=True, timeout=30, cwd=str(BASE_DIR),
            )
            if result.returncode == 0:
                log("  [OK] test_pipeline.py passed")
            else:
                log("  [FAIL] test_pipeline.py failed:\n%s" % result.stderr)
                all_pass = False
        except subprocess.TimeoutExpired:
            log("  [FAIL] test_pipeline.py timed out (>30s)")
            all_pass = False
        except Exception as e:
            log("  [FAIL] Could not run test_pipeline.py: %s" % e)
            all_pass = False
    else:
        log("  [FAIL] test_pipeline.py missing or empty - skipping")
        all_pass = False

    log("")
    log("=" * 60)
    if all_pass:
        log("ALL CHECKS PASSED - Ready to deploy")
    else:
        log("SOME CHECKS FAILED - Fix before deploying")
    log("=" * 60)
    return all_pass


def start_pipeline(with_gatekeeper=False, telegram=False, standalone=False):
    modes = []
    if standalone:
        modes.append("standalone (telegram + ollama)")
    else:
        if telegram:
            modes.append("telegram bridge")
        if with_gatekeeper:
            modes.append("gatekeeper")
        if not modes:
            modes.append("gateway only")
    log("Starting pipeline... " + " + ".join(modes))

    processes = []

    # 1. Ensure Ollama running
    log("Checking Ollama...")
    result = subprocess.run(["pgrep", "-f", "ollama"], capture_output=True, text=True)
    if result.returncode != 0:
        log("Starting Ollama...")
        p = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(("ollama", p))
        time.sleep(3)
    else:
        log("Ollama already running")

    # 2. Start Telegram bridge (standalone or with-gatekeeper mode)
    if telegram or standalone:
        log("Starting Telegram Bridge...")
        bridge_path = BASE_DIR / "telegram_bridge.py"
        if bridge_path.exists():
            env = os.environ.copy()
            p = subprocess.Popen(
                [sys.executable, str(bridge_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            processes.append(("telegram-bridge", p))
            time.sleep(2)
        else:
            log("WARNING: telegram_bridge.py not found - Telegram unavailable")

    # 3. Start gatekeeper if requested
    if with_gatekeeper and not standalone:
        log("Starting Gatekeeper...")
        gatekeeper_path = BASE_DIR / "gatekeeper.py"
        p = subprocess.Popen(
            [sys.executable, str(gatekeeper_path), "--background"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(("gatekeeper", p))
        time.sleep(2)

    log("")
    log("Pipeline started. %d services running." % len(processes))
    log("Press Ctrl+C to stop all services.")

    try:
        while True:
            time.sleep(1)
            for name, p in processes:
                if p.poll() is not None:
                    log("WARNING: %s died (exit code %d)" % (name, p.returncode))
    except KeyboardInterrupt:
        log("")
        log("Shutting down...")
        for name, p in processes:
            p.terminate()
            log("  Stopped %s" % name)


def main():
    parser = argparse.ArgumentParser(description="Hermes Bridge Manager")
    parser.add_argument("--validate", action="store_true", help="Run pre-flight checks only")
    parser.add_argument("--with-gatekeeper", action="store_true", help="Run full pipeline with gatekeeper + telegram bridge")
    parser.add_argument("--standalone", action="store_true", help="Standalone mode: telegram bridge + ollama (linux fallback)")
    parser.add_argument("--gateway-only", action="store_true", help="Run gateway + Ollama only (no gatekeeper)")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, start nothing")
    args = parser.parse_args()

    if args.validate or args.dry_run:
        ok = validate()
        if not ok:
            sys.exit(1)
        if args.dry_run:
            log("")
            log("Dry run complete. Pipeline not started.")
            sys.exit(0)

    if args.standalone:
        start_pipeline(standalone=True)
    elif args.with_gatekeeper:
        start_pipeline(with_gatekeeper=True, telegram=True)
    elif args.gateway_only:
        start_pipeline(with_gatekeeper=False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
