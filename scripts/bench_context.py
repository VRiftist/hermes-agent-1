#!/usr/bin/env python3
"""
Context window benchmark — starts at a high context size and steps down.
Measures: success/failure, latency, approximate tokens processed.
Usage: python3 bench_context.py <model> <start_ctx> <step_down> <min_ctx>
"""

import sys, time, json, subprocess, os

def bench_context(model, context_size):
    """Send a prompt of ~context_size tokens and measure response."""
    # Generate filler text to fill the context window
    filler = "The quick brown fox jumps over the lazy dog. " * 50  # ~550 chars per repeat
    repeats = max(1, context_size // 200)  # rough token count (1 token ≈ 4 chars)
    prompt_text = filler * repeats
    # Truncate to approximately the target token count
    prompt_text = prompt_text[:context_size * 4]

    prompt_msg = (
        f"You are benchmarking context window size. "
        f"Process the following text and return the total word count. "
        f"Keep your response short (just the number).\n\n"
        f"{prompt_text}\n\n"
        f"Total word count:"
    )

    payload = {
        "model": model,
        "prompt": prompt_msg,
        "num_ctx": context_size,
        "num_predict": 10,
        "temperature": 0.1,
        "timeout": 300
    }

    start = time.time()
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://127.0.0.1:11434/api/generate",
             "-d", json.dumps(payload)],
            capture_output=True, text=True, timeout=120
        )
        elapsed = time.time() - start
        output = result.stdout.strip()

        # Parse response
        try:
            data = json.loads(output)
            response = data.get("response", "")
        except:
            response = output[-200:] if output else "PARSE_ERROR"

        # Check markers
        truncated = "length" in output.lower() and "context" in output.lower()
        success = result.returncode == 0 and len(response) > 0

        return {
            "context": context_size,
            "success": success,
            "latency_sec": round(elapsed, 2),
            "response_len": len(response),
            "truncated": truncated,
            "error": None if success else (output[:300] if output else "EMPTY_RESPONSE")
        }
    except subprocess.TimeoutExpired:
        return {
            "context": context_size,
            "success": False,
            "latency_sec": 120,
            "response_len": 0,
            "truncated": False,
            "error": "TIMEOUT_120s"
        }
    except Exception as e:
        return {
            "context": context_size,
            "success": False,
            "latency_sec": 0,
            "response_len": 0,
            "truncated": False,
            "error": str(e)[:200]
        }

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <model> <start_ctx> <step_down> [min_ctx]")
        print(f"Example: {sys.argv[0]} qwen3:8b 262144 32768 8192")
        sys.exit(1)

    model = sys.argv[1]
    ctx = int(sys.argv[2])
    step = int(sys.argv[3])
    min_ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 2048

    print(f"\n{'='*60}")
    print(f"  BENCHMARK: {model}")
    print(f"  Starting: {ctx:,} ctx | Step: {step:,} | Min: {min_ctx:,}")
    print(f"{'='*60}\n")

    results = []
    best_working = None

    while ctx >= min_ctx:
        print(f"  Testing ctx={ctx:,} ... ", end="", flush=True)
        r = bench_context(model, ctx)
        results.append(r)

        if r["success"]:
            print(f"OK ({r['latency_sec']}s, {r['response_len']} chars)")
            best_working = ctx
            # If this worked easily, try jumping up
            if r["latency_sec"] < 5 and not r["truncated"]:
                print(f"  -> Fast & clean, jumping UP to {ctx + step:,}")
                ctx += step
                continue
            # Otherwise step down
            ctx -= step
        else:
            print(f"FAIL ({r['error'][:60]})")
            ctx -= step

    print(f"\n{'='*60}")
    print(f"  RESULT: Best working context = {best_working:,}")
    print(f"{'='*60}")

    # Print summary table
    print(f"\n{'Context':>12} | {'Status':>8} | {'Latency':>10} | {'Response':>10} | Notes")
    print(f"{'-'*12}-+-{'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*20}")
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        notes = r["error"][:30] if r["error"] else ""
        if r["truncated"]:
            notes += " [TRUNCATED]"
        print(f"{r['context']:>12,} | {status:>8} | {r['latency_sec']:>8.1f}s | {r['response_len']:>10} | {notes}")

if __name__ == "__main__":
    main()