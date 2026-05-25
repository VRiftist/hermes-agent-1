#!/usr/bin/env python3
"""
Context benchmark for Linux GPU models via SSH.
Run FROM Mac, executes on Linux.
"""
import subprocess, time, json, sys, os

LINUX_HOST = "192.168.1.230"
SSH_CMD = f"ssh {LINUX_HOST}"

def get_linux_vram():
    out = subprocess.run(
        f"{SSH_CMD} 'nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits'",
        shell=True, capture_output=True, text=True
    ).stdout.strip().replace("MiB","")
    if "," in out:
        parts = out.split(",")
        return float(parts[0].strip()), float(parts[1].strip())
    return 0, 0

def bench(model, context_size):
    filler = "The quick brown fox jumps over the lazy dog. "
    repeats = max(1, context_size // 8)
    prompt_text = filler * repeats
    prompt_text = prompt_text[:int(context_size * 4)]

    payload = {
        "model": model,
        "prompt": prompt_text + "\\n\\nWord count:",
        "num_ctx": context_size,
        "num_predict": 5,
        "temperature": 0.1,
        "stream": False
    }

    payload_json = json.dumps(payload)

    start = time.time()
    try:
        result = subprocess.run(
            f'{SSH_CMD} \'curl -s -X POST http://127.0.0.1:11434/api/generate -d "{payload_json}"\'',
            shell=True, capture_output=True, text=True, timeout=300
        )
        elapsed = time.time() - start
        output = result.stdout.strip()

        lines = [l for l in output.strip().split("\\n") if l.strip()]
        try:
            data = json.loads(lines[-1])
        except:
            try:
                data = json.loads(output)
            except:
                data = {"error": output[:200], "response": ""}

        response = data.get("response", "")
        success = bool(response.strip()) and result.returncode == 0

        return {
            "context": context_size,
            "success": success,
            "latency_sec": round(elapsed, 1),
            "eval_count": data.get("eval_count", 0),
            "truncated": "context_length" in str(data).lower(),
            "error": str(data.get("error",""))[:200] if not success else None
        }
    except subprocess.TimeoutExpired:
        return {
            "context": context_size, "success": False, "latency_sec": 300,
            "eval_count": 0, "truncated": False, "error": "TIMEOUT"
        }
    except Exception as e:
        return {
            "context": context_size, "success": False, "latency_sec": 0,
            "eval_count": 0, "truncated": False, "error": str(e)[:200]
        }

def run_benchmark(model, label):
    print(f"\n{'='*70}")
    print(f"  BENCHMARK: {model}")
    print(f"  {label} (Linux GPU)")
    print(f"{'='*70}\n")

    ctx_sizes = [96000, 80000, 64000, 48000, 32000, 24000, 16000, 12000, 8000]
    results = []
    best = None

    for ctx in ctx_sizes:
        r = bench(model, ctx)
        results.append(r)

        if r["success"]:
            if best is None:
                best = ctx
            print(f"  ✓ ctx={ctx:>6,} | {r['latency_sec']:>6.1f}s | eval={r['eval_count']}")
        else:
            err = r["error"] or "NONE"
            print(f"  ✗ ctx={ctx:>6,} | FAIL: {err[:50]}")

    print(f"\n  BEST: {best:,} context" if best else "\n  NO SUCCESSFUL RUNS")
    return results, best

if __name__ == "__main__":
    print("=== Full Context Review Benchmark Suite ===")
    print("Running on Linux GPU (RTX 3060 12GB) via SSH\n")

    # Check GPU status
    print("GPU check:")
    os.system(f'{SSH_CMD} "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits"')

    models = [
        ("qwen-coder-32b-96k:latest", "32B 96K-Native"),
        ("qwen2.5-coder:32b-instruct-q4_K_M", "32B Standard Q4"),
    ]

    all_results = {}
    for i, (model, label) in enumerate(models):
        results, best = run_benchmark(model, label)
        all_results[model] = {"best": best, "results": results}

        if i < len(models) - 1:
            print("\n  Cooling down 60s between models...")
            time.sleep(60)

    # Save
    os.makedirs(os.path.expanduser("~/.hermes"), exist_ok=True)
    with open(os.path.expanduser("~/.hermes/bench_linux_gpu.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nSaved to ~/.hermes/bench_linux_gpu.json")

    print(f"\n{'='*70}")
    print("  COMPARISON")
    print(f"{'='*70}")
    for model, data in all_results.items():
        line = f"  {model}: max ctx = {data['best']:,}" if data['best'] else f"  {model}: FAILED"
        print(line)