#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
Ollama API context window benchmark for Mac (Apple Silicon).
Streams responses properly, tracks memory, finds real ceiling.
"""
import subprocess, time, json, sys, os, resource, tracemalloc

OLLAMA_URL = "http://127.0.0.1:11434"

def get_memory_mb():
    """Get current process RSS in MB."""
    try:
        with open(f"/proc/{os.getpid()}/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024  # KB to MB
    except:
        pass
    # Fallback: use tracemalloc
    current, _ = tracemalloc.get_traced_memory()
    return current / 1024 / 1024

def bench(model, context_size, step_name=""):
    """Send prompt at given context size, return result dict."""
    filler = "The quick brown fox jumps over the lazy dog. "
    repeats = max(1, context_size // 8)  # ~8 tokens per repeat
    prompt_text = filler * repeats
    prompt_text = prompt_text[:int(context_size * 4)]  # ~4 chars/token

    payload = {
        "model": model,
        "prompt": prompt_text + "\n\nTotal word count:",
        "num_ctx": context_size,
        "num_predict": 5,
        "temperature": 0.1,
        "stream": False  # Don't stream — wait for full response
    }

    tracemalloc.start()
    start = time.time()
    peak_mem = 0

    try:
        # Use subprocess with timeout to avoid hanging
        proc = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{OLLAMA_URL}/api/generate",
             "-d", json.dumps(payload)],
            capture_output=True, text=True, timeout=180
        )
        elapsed = time.time() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mem = peak / 1024 / 1024

        output = proc.stdout.strip()

        # Parse the final JSON object from potentially streamed responses
        # Try to find the last complete JSON object
        lines = [l for l in output.strip().split("\n") if l.strip()]
        last_line = lines[-1] if lines else ""

        try:
            data = json.loads(last_line)
        except json.JSONDecodeError:
            # Try parsing the whole output
            try:
                data = json.loads(output)
            except:
                data = {"error": output[:200], "response": ""}

        response = data.get("response", "")
        done = data.get("done", False)
        error = data.get("error", "") if not done and not response else None

        if isinstance(error, dict):
            error = str(error)

        success = bool(response.strip()) and proc.returncode == 0
        truncated = "context_length" in str(data).lower() or "truncat" in response.lower()
        eval_count = data.get("eval_count", 0)
        load_time = data.get("load_duration", 0) / 1e9 if isinstance(data.get("load_duration"), (int, float)) else 0

        return {
            "context": context_size,
            "step_name": step_name,
            "success": success,
            "latency_sec": round(elapsed, 2),
            "peak_mem_mb": round(peak_mem, 1),
            "response_len": len(response),
            "eval_count": eval_count,
            "load_time_sec": round(load_time, 2),
            "truncated": truncated,
            "error": str(error)[:200] if error else None
        }

    except subprocess.TimeoutExpired:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "context": context_size,
            "step_name": step_name,
            "success": False,
            "latency_sec": 180,
            "peak_mem_mb": round(peak / 1024 / 1024, 1),
            "response_len": 0,
            "eval_count": 0,
            "load_time_sec": 0,
            "truncated": False,
            "error": "TIMEOUT"
        }
    except Exception as e:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "context": context_size,
            "step_name": step_name,
            "success": False,
            "latency_sec": 0,
            "peak_mem_mb": round(peak / 1024 / 1024, 1),
            "response_len": 0,
            "eval_count": 0,
            "load_time_sec": 0,
            "truncated": False,
            "error": str(e)[:200]
        }

def run_benchmark(model_name, ctx_start, ctx_step, ctx_min, label=""):
    print(f"\n{'='*70}")
    print(f"  BENCHMARK: {model_name}")
    print(f"  {label}")
    print(f"  Starting: {ctx_start:,} ctx | Step: {ctx_step:,} | Min: {ctx_min:,}")
    print(f"{'='*70}\n")

    results = []
    best_working = None
    ctx = ctx_start

    while ctx >= ctx_min:
        step_label = f"{'↑' if best_working and ctx > best_working else '↓'}"
        print(f"  [{step_label}] ctx={ctx:,} ... ", end="", flush=True)

        r = bench(model_name, ctx, step_label)
        results.append(r)

        if r["success"]:
            if not r["truncated"]:
                if best_working is None or ctx > best_working:
                    best_working = ctx
                print(f"✓ OK ({r['latency_sec']}s, peak {r['peak_mem_mb']:.0f}MB, eval_tokens={r['eval_count']})")

                # If fast and clean, jump up
                if r["latency_sec"] < 30 and not r["truncated"]:
                    jump = ctx_step * 2
                    print(f"  -> Fast! Jumping UP to {ctx + jump:,}")
                    ctx += jump
                    continue
                # Otherwise step down
                ctx -= ctx_step
            else:
                print(f"~ OK but TRUNCATED ({r['latency_sec']}s)")
                ctx -= ctx_step
        else:
            err = r["error"] or "UNKNOWN"
            if "out_of_memory" in err.lower() or "OOM" in err.upper():
                print(f"✗ OOM ({err[:60]})")
            elif "context_length" in err.lower():
                print(f"✗ CTX_ERR ({err[:60]})")
            elif r["latency_sec"] >= 180:
                print(f"✗ TIMEOUT")
            else:
                print(f"✗ FAIL ({err[:60]})")
            ctx -= ctx_step

        gc_imported = False
        try:
            import gc
            gc.collect()
            gc_imported = True
        except:
            pass
        if gc_imported:
            gc.collect()

    print(f"\n{'='*70}")
    if best_working:
        best_result = next((r for r in results if r["context"] == best_working and r["success"]), None)
        peak = best_result["peak_mem_mb"] if best_result else "?"
        print(f"  RESULT: Maximum working context = {best_working:,}")
        print(f"          Peak memory at that size: {peak}MB")
    else:
        print("  RESULT: No context size succeeded")
    print(f"{'='*70}\n")

    # Summary table
    print(f"  {'Context':>10} | {'OK/FAIL':>7} | {'Time':>8} | {'PeakMB':>7} | {'Tokens':>8} | {'Notes'}")
    print(f"  {'-'*10}-+-{'-'*7}-+-{'-'*8}-+-{'-'*7}-+-{'-'*8}-+-{'-'*25}")
    for r in results:
        status = "✓" if r["success"] and not r["truncated"] else "~" if r["success"] else "✗"
        err_note = (r["error"] or "")[:25] if not r["success"] else ("TRUNC" if r["truncated"] else "")
        time_s = f"{r['latency_sec']:.0f}s" if r["latency_sec"] < 180 else "TO"
        print(f"  {r['context']:>10,} | {status:>7} | {time_s:>8} | {r['peak_mem_mb']:>6.0f} | {r['eval_count']:>8,} | {err_note}")

    return results, best_working

if __name__ == "__main__":
    import gc

    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:32b-instruct-q4_K_M"
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 8192
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    minimum = int(sys.argv[4]) if len(sys.argv) > 4 else 2048

    results, best = run_benchmark(model, start, step, minimum)

    # Save
    out = {
        "model": model,
        "platform": "mac_m2_metal_ollama",
        "best_context": best,
        "results": results
    }
    os.makedirs(os.path.expanduser("~/.hermes"), exist_ok=True)
    with open(os.path.expanduser("~/.hermes/bench_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved to ~/.hermes/bench_results.json")