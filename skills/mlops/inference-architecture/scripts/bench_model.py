import subprocess
import json
import sys
import os

"""
Quick model benchmark script for the Mac M2 32GB environment.
Run sequentially, one model at a time. Kills Chrome first.

Usage: python3 bench_model.py <model_name> [context_length]
   or: python3 bench_model.py --suite qwen3:14b,qwen2.5-coder:14b 8192
"""

OLLAMA = "http://localhost:11434"

def kill_chrome():
    subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
    print("[+] Chrome killed (if running)")

def get_model_info(model_name):
    """Fetch model details from Ollama."""
    try:
        r = subprocess.run(
            ["curl", "-s", f"{OLLAMA}/api/show", "-d", json.dumps({"name": model_name})],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            info = data.get("model_info", {})
            params = info.get("general.parameter_count", "?")
            arch = info.get("general.architecture", "?")
            print(f"  Params: {params} | Arch: {arch}")
    except Exception:
        pass

def benchmark(model_name, context_len=8192, prompt="Explain recursion in 3 sentences"):
    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": context_len}
    })

    print(f"\n{'='*60}")
    print(f"Benchmarking: {model_name}")
    print(f"Context: {context_len}")
    print(f"{'='*60}")

    get_model_info(model_name)

    r = subprocess.run(
        ["curl", "-s", f"{OLLAMA}/api/generate", "-d", payload],
        capture_output=True, text=True, timeout=120
    )

    if r.returncode != 0:
        print(f"ERROR: {r.stderr[:200]}")
        return None

    try:
        data = json.loads(r.stdout)
        response = data.get("response", "")
        eval_duration = data.get("eval_duration", 0)
        eval_count = data.get("eval_count", 0)
        total_duration = data.get("total_duration", 0)

        tok_sec = eval_count / (eval_duration / 1e9) if eval_duration > 0 else 0
        time_s = total_duration / 1e9

        result = {
            "model": model_name,
            "context": context_len,
            "tokens": eval_count,
            "time_s": round(time_s, 1),
            "tok_per_s": round(tok_sec, 1)
        }
        print(f"\n  Tokens: {eval_count} | Time: {time_s:.1f}s | Speed: {tok_sec:.1f} tok/s")
        print(f"  Preview: {response[:200]}...")
        return result
    except json.JSONDecodeError:
        print(f"  Raw: {r.stdout[:500]}")
        return None

def run_suite(models, context=8192):
    """Benchmark multiple models sequentially."""
    kill_chrome()
    results = []
    for m in models:
        r = benchmark(m, context)
        if r:
            results.append(r)
        subprocess.run(["pkill", "-f", "ollama run"], capture_output=True)
    print("\n\n=== SUMMARY ===")
    for r in results:
        print(f"  {r['model']}: {r['tok_per_s']} tok/s ({r['time_s']}s)")
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 bench_model.py <model_name> [context_length]")
        print("   or: python3 bench_model.py --suite qwen3:14b,qwen2.5-coder:14b 8192")
        sys.exit(1)

    if sys.argv[1] == "--suite":
        models = sys.argv[2].split(",")
        ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 8192
        run_suite(models, ctx)
    else:
        model = sys.argv[1]
        ctx = int(sys.argv[2]) if len(sys.argv) > 2 else 8192
        kill_chrome()
        benchmark(model, ctx)