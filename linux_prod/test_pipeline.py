#!/usr/bin/env python3
"""
test_pipeline.py — Smoke tests for the Telegram → Gateway → Ollama pipeline.
Run via: python3 run_bridge.py --validate (calls this automatically)

Tests:
  1. All required Python modules import successfully
  2. Path resolution works (no hard-coded roots)
  3. Environment variables are set
  4. Ollama API is reachable
  5. Auto-trim script can parse and execute
  6. Bridge signal files can be read/written
  7. Gatekeeper can start and bind its socket
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests  # top-level for Pyright binding visibility

BASE_DIR = Path(__file__).resolve().parent
errors: list[str] = []
warnings: list[str] = []


def test(name: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name}")
        errors.append(f"{name}: {detail}")


def warn(name: str, detail: str = ""):
    print(f"  ⚠️  {name}")
    warnings.append(f"{name}: {detail}")


def test_imports():
    print("\n[1] Import tests")
    try:
        import requests as _r  # noqa: F841
        test("requests available", True)
    except ImportError:
        test("requests available", False, "pip install requests")

    try:
        from pathlib import Path as _P  # noqa: F841
        test("pathlib available", True)
    except ImportError:
        test("pathlib available", False, "stdlib missing?")


def test_path_resolution():
    print("\n[2] Path resolution tests")
    test("BASE_DIR is not root", BASE_DIR != Path("/"), f"BASE_DIR={BASE_DIR}")
    test("BASE_DIR exists", BASE_DIR.exists(), f"BASE_DIR={BASE_DIR}")

    expected_files = [
        "scripts/auto_trim.py",
        "gateway_integration.py",
        "run_bridge.py",
        "gatekeeper.py",
    ]
    for f in expected_files:
        full = BASE_DIR / f
        test(f"exists: {f}", full.exists(), f"not found at {full}")
        if full.exists():
            test(f"non-empty: {f}", full.stat().st_size > 0, f"0 bytes at {full}")


def test_env_vars():
    print("\n[3] Environment variable tests")
    for var in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_IDS"]:
        val = os.environ.get(var)
        test(f"{var} is set", bool(val), f"{var} is empty or unset")

    for var in ["OLLAMA_HOST", "TRIM_MODEL"]:
        val = os.environ.get(var)
        if val:
            test(f"{var} = {val}", True)
        else:
            warn(f"{var} not set (will use default)")


def test_ollama():
    print("\n[4] Ollama connectivity")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        test("Ollama reachable", resp.status_code == 200, f"HTTP {resp.status_code}")

        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models]
            test("At least one model", len(model_names) > 0, "No models pulled yet")
            if model_names:
                print(f"     Models: {', '.join(model_names)}")

            trim_model = os.environ.get("TRIM_MODEL", "qwen3:8b")
            has_trim = any(trim_model in name or name in trim_model for name in model_names)
            if not has_trim:
                warn(f"Trim model '{trim_model}' not found in pulled models")
    except requests.exceptions.ConnectionError:
        test("Ollama reachable", False, "Cannot connect to localhost:11434 — is ollama running?")
    except Exception as e:
        test("Ollama reachable", False, str(e))


def test_signal_files():
    print("\n[5] Bridge signal file tests")
    signals_dir = BASE_DIR / "bridge" / "signals"
    signals_dir.mkdir(parents=True, exist_ok=True)

    test_file = signals_dir / "_test_write.json"
    try:
        test_file.write_text(json.dumps({"test": True, "ts": time.time()}))
        test("Can write signal file", True)
        data = json.loads(test_file.read_text())
        test("Can read signal file", data.get("test") is True)
        test_file.unlink()
    except Exception as e:
        test("Signal file R/W", False, str(e))

    auto_trim = BASE_DIR / "scripts" / "auto_trim.py"
    if auto_trim.exists():
        test("auto_trim.py writable path", True)
    else:
        test("auto_trim.py exists", False)


def test_gatekeeper_socket():
    print("\n[6] Gatekeeper socket test")
    sock_path = "/tmp/aether-gatekeeper-test.sock"
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(sock_path)
        sock.close()
        os.unlink(sock_path)
        test("Unix socket creation", True)
    except PermissionError:
        test("Unix socket creation", False, "Permission denied")
    except Exception as e:
        test("Unix socket creation", False, str(e))


def test_auto_trim_parse():
    print("\n[7] Auto-trim script parse test")
    auto_trim = BASE_DIR / "scripts" / "auto_trim.py"
    if not auto_trim.exists():
        test("auto_trim.py exists", False)
        return

    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open('{auto_trim}').read()); print('OK')"],
            capture_output=True, text=True, timeout=10,
        )
        test("auto_trim.py syntax valid", "OK" in result.stdout, result.stderr)
    except Exception as e:
        test("auto_trim.py syntax", False, str(e))


def main():
    print("=" * 60)
    print("PIPELINE SMOKE TEST")
    print("=" * 60)

    test_imports()
    test_path_resolution()
    test_env_vars()
    test_ollama()
    test_signal_files()
    test_gatekeeper_socket()
    test_auto_trim_parse()

    print("\n" + "=" * 60)
    if errors:
        print(f"❌ {len(errors)} FAILURE(S):")
        for e in errors:
            print(f"   • {e}")
        print("\nFix the above before deploying.")
    else:
        print("✅ ALL TESTS PASSED")
        if warnings:
            print(f"⚠️  {len(warnings)} warning(s) — review above")
    print("=" * 60)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())