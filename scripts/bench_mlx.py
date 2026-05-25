#!/usr/bin/env python3
"""
MLX-based context window benchmark for Mac.
Tests model at various context sizes, measuring memory and latency.
"""
import sys, os, time, json, gc, tracemalloc
import numpy as np

# Activate venv
venv_site = os.path.expanduser("~/.mlx-venv/lib/python3.14/site-packages")
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

import mlx.core as mx
from mlx_lm import load, generate

def bench_model(model_path, context_sizes, tokenizer, model):
    results = []
    mx.metal.clear_cache()
    gc.collect()
    
    for ctx in context_sizes:
        mx.metal.clear_cache()
        gc.collect()
        
        # Generate filler text
        filler = "The quick brown fox jumps over the lazy dog. "
        repeats = max(1, ctx // 10)
        prompt = filler * repeats
        prompt = prompt[:int(ctx * 4)]  # ~4 chars per token
        
        full_prompt = (
            f"You are benchmarking context window size. "
            f"Process the following text and return the total word count. "
            f"Keep your response short (just the number).\n\n"
            f"{prompt}\n\n"
            f"Total word count:"
        )
        
        print(f"  Testing ctx={ctx:,} ... ", end="", flush=True)
        
        tracemalloc.start()
        start = time.time()
        try:
            response, _ = generate(
                model, tokenizer,
                prompt=full_prompt,
                max_tokens=10,
                temp=0.1,
                repetition_penalty=1.0,
                verbose=False
            )
            elapsed = time.time() - start
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            success = len(response.strip()) > 0
            mem_mb = peak / 1024 / 1024
            
            print(f"OK ({elapsed:.1f}s, ~{mem_mb:.0f}MB peak, {len(response)} chars)")
            results.append({
                "context": ctx,
                "success": success,
                "latency_sec": round(elapsed, 2),
                "peak_mem_mb": round(mem_mb, 1),
                "response_len": len(response),
                "error": None
            })
        except Exception as e:
            elapsed = time.time() - start
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            mem_mb = peak / 1024 / 1024
            
            err = str(e)[:120]
            print(f"FAIL ({err[:60]})")
            results.append({
                "context": ctx,
                "success": False,
                "latency_sec": round(elapsed, 2),
                "peak_mem_mb": round(mem_mb, 1),
                "response_len": 0,
                "error": err
            })
            gc.collect()
            mx.metal.clear_cache()
    
    return results

def main():
    model_name = "qwen2.5-coder:32b-instruct-q4_K_M"
    model_path = None  # Try Ollama path first
    
    print(f"\n{'='*60}")
    print(f"  MLX BENCHMARK: {model_name}")
    print(f"  Platform: Apple Silicon (MLX-Metal)")
    print(f"{'='*60}\n")
    
    # Try to load model
    print("Loading model... ", end="", flush=True)
    try:
        # Try Ollama model path
        ollama_path = os.path.expanduser("~/.ollama/models/manifests/registry.ollama.ai/library/qwen2.5-coder:32b-instruct-q4_K_M")
        
        # Try huggingface cache
        home = os.path.expanduser("~")
        possible_paths = [
            f"{home}/.ollama/models/blobs",
            f"{home}/.cache/huggingface",
            None  # will search
        ]
        
        model, tokenizer = load(model_name, adapter_path=None)
        print("LOADED OK")
    except Exception as e:
        print(f"FAILED: {e}")
        print("Trying to find model files...")
        return
    
    # Test context sizes starting conservative and stepping up
    context_sizes = [2048, 4096, 8192, 12288, 16384, 24576, 32768, 40960, 49152, 57344, 65536]
    
    print(f"\nSystem memory: {mx.metal.device_properties()['memory_size'] / 1024 / 1024 / 1024:.1f} GB")
    print(f"Testing {len(context_sizes)} context sizes...\n")
    
    results = bench_model(model_path, context_sizes, tokenizer, model)
    
    # Summary
    best = None
    for r in results:
        if r["success"]:
            best = r
    
    print(f"\n{'='*60}")
    if best:
        print(f"  RESULT: Best working context = {best['context']:,} ({best['peak_mem_mb']:.0f}MB peak)")
    else:
        print("  RESULT: NO context size worked")
    print(f"{'='*60}\n")
    
    print(f"{'Context':>10} | {'Status':>6} | {'Latency':>10} | {'PeakMem':>10} | Notes")
    print(f"{'-'*10}-+-{'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*30}")
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        notes = r["error"][:30] if r["error"] else ""
        print(f"{r['context']:>10,} | {status:>6} | {r['latency_sec']:>8.1f}s | {r['peak_mem_mb']:>8.0f}MB | {notes}")
    
    # Save results
    with open(os.path.expanduser("~/.hermes/bench_mlx_results.json"), "w") as f:
        json.dump({
            "model": model_name,
            "platform": "mac_m2_metal",
            "results": results,
            "best_context": best["context"] if best else None,
            "best_peak_mem_mb": best["peak_mem_mb"] if best else None
        }, f, indent=2)
    print(f"\nResults saved to ~/.hermes/bench_mlx_results.json")

if __name__ == "__main__":
    main()
