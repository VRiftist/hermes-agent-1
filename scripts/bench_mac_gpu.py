#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
Mac M2 Pro GPU benchmark — find the best coder model for Apple Silicon.
Tests via MLX (GPU) and compares quality + speed across coder models.
"""
import sys, os, time, json, gc, tracemalloc, textwrap

# Ensure MLX venv is used
sys.path.insert(0, os.path.expanduser("~/.mlx-venv/lib/python3.14/site-packages"))

import mlx.core as mx
from mlx_lm import load, generate

BENCHMARK_PROMPT = """You are a senior code reviewer. Review the following Python function
for bugs, security issues, performance problems, and style violations.
Give a structured review in JSON format with keys: bugs, security, performance, style.

```python
def process_data(data, config):
    result = []
    for item in data:
        if item.get('active'):
            transformed = {}
            for key, value in item.items():
                if key == 'name':
                    transformed['name'] = value.upper()
                elif key == 'value':
                    transformed['value'] = int(value) * 2
                elif key == 'tags':
                    transformed['tags'] = [t.strip() for t in value.split(',')]
                else:
                    transformed[key] = value
            if transformed.get('value', 0) > 100:
                result.append(transformed)
    return sorted(result, key=lambda x: x['value'], reverse=True)

data = [
    {'name': 'alpha', 'value': '42', 'active': True, 'tags': 'fast, reliable'},
    {'name': 'beta', 'value': '73', 'active': False, 'tags': 'slow'},
    {'name': 'gamma', 'value': '150', 'active': True, 'tags': 'fast, modern'},
    {'name': 'delta', 'value': 'not_a_number', 'active': True, 'tags': 'experimental'},
]
config = {'threshold': 100}
print(process_data(data, config))
```"""

CONTEXT_TEST_PROMPT = """You are a code summarizer. Read the following code and return a
one-sentence summary of what it does. Reply in 10 words or fewer."""

def clear_mlx_cache():
    mx.metal.clear_cache()
    gc.collect()
    tracemalloc.reset_peak()

def test_model_quality(model_name, model, tokenizer):
    """Test coding quality with a benchmark prompt."""
    clear_mlx_cache()
    start = time.time()
    try:
        response, _ = generate(
            model, tokenizer,
            prompt=BENCHMARK_PROMPT,
            max_tokens=200,
            temp=0.2,
            repetition_penalty=1.1,
            verbose=False
        )
        elapsed = time.time() - start
        return {
            "model": model_name,
            "success": True,
            "latency_sec": round(elapsed, 2),
            "response": response.strip()[:500],
            "response_len": len(response)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "model": model_name,
            "success": False,
            "latency_sec": round(elapsed, 2),
            "response": "",
            "error": str(e)[:200]
        }

def test_context_ceiling(model_name, model, tokenizer, ctx_sizes):
    """Test max context window."""
    results = []
    best = None

    for ctx in ctx_sizes:
        clear_mlx_cache()
        filler = "The quick brown fox jumps over the lazy dog. "
        repeats = max(1, ctx // 8)
        prompt_text = filler * repeats
        prompt_text = prompt_text[:int(ctx * 4)]
        full_prompt = CONTEXT_TEST_PROMPT + "\n\n" + prompt_text + "\n\nSummary:"

        start = time.time()
        try:
            response, _ = generate(
                model, tokenizer,
                prompt=full_prompt,
                max_tokens=10,
                temp=0.1,
                verbose=False
            )
            elapsed = time.time() - start
            success = len(response.strip()) > 0

            if success:
                if best is None or ctx > best:
                    best = ctx
                print(f"  ✓ ctx={ctx:>6,} | {elapsed:>6.1f}s | {len(response):>4} chars")
            else:
                print(f"  ? ctx={ctx:>6,} | empty response")

            results.append({
                "context": ctx,
                "success": success,
                "latency_sec": round(elapsed, 1),
                "response_len": len(response)
            })
        except Exception as e:
            print(f"  ✗ ctx={ctx:>6,} | {str(e)[:50]}")
            results.append({
                "context": ctx,
                "success": False,
                "latency_sec": 0,
                "response_len": 0,
                "error": str(e)[:150]
            })

    return results, best

def main():
    models_to_test = [
        ("mlx-community/Qwen2.5-Coder-7B-Instruct-4bit", "Qwen 2.5 Coder 7B Q4"),
        ("mlx-community/Qwen2.5-Coder-14B-Instruct-4bit", "Qwen 2.5 Coder 14B Q4"),
        ("mlx-community/Qwen3-8B-Base", "Qwen 3.0 8B Base Q4"),  # baseline
    ]

    try:
        memory = mx.metal.device_properties()['memory_size']
    except:
        memory = 10 * 1024 * 1024 * 1024  # M2 Pro ~10GB GPU
    print(f"\n{'='*70}")
    print(f"  MAC GPU BENCHMARK — Apple Silicon MLX")
    print(f"  GPU Memory: {memory / 1024 / 1024 / 1024:.1f} GB")
    print(f"  Platform: M2 Pro")
    print(f"{'='*70}\n")

    context_sizes = [2048, 4096, 8192, 12288, 16384, 20000, 24576, 28000, 32000]

    all_results = {}
    for i, (hf_name, label) in enumerate(models_to_test):
        print(f"\n--- Loading: {label} ({hf_name}) ---")
        try:
            model, tokenizer = load(hf_name)
            print(f"  ✓ Model loaded successfully")

            # Quality test
            print(f"  Running quality benchmark...")
            quality = test_model_quality(label, model, tokenizer)
            print(f"    Time: {quality['latency_sec']}s")
            if quality['success']:
                print(f"    Response preview: {quality['response'][:150]}...")

            # Context ceiling test
            print(f"  testing context ceiling...")
            ctx_results, best = test_context_ceiling(label, model, tokenizer, context_sizes)

            all_results[hf_name] = {
                "label": label,
                "quality": quality,
                "context_results": ctx_results,
                "best_context": best
            }

            if quality['success']:
                print(f"\n  >>> {label}")
                print(f"      Quality: {quality['latency_sec']}s")
                print(f"      Best context: {best:,}" if best else "      Best context: NONE")

            # Unload to free memory
            del model
            del tokenizer
            clear_mlx_cache()

        except Exception as e:
            err = str(e)
            print(f"  ✗ FAILED: {err[:200]}")
            all_results[hf_name] = {
                "label": label,
                "error": err[:300],
                "quality": None,
                "context_results": [],
                "best_context": None
            }

        if i < len(models_to_test) - 1:
            print(f"\n  Cooling down 15s before next model...")
            clear_mlx_cache()
            time.sleep(15)

    # Save results
    out_path = os.path.expanduser("~/.hermes/mac_gpu_benchmark.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*70}")
    for hf_name, data in all_results.items():
        label = data.get("label", hf_name)
        if data["best_context"]:
            quality_time = data["quality"]["latency_sec"] if data["quality"] else "N/A"
            print(f"  {label:40s} | quality: {quality_time:>6}s | best ctx: {data['best_context']:>6,}")
        elif "error" in data:
            print(f"  {label:40s} | ERROR: {data['error'][:50]}")
        else:
            print(f"  {label:40s} | FAILED")

    print(f"\n  Results saved to {out_path}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()