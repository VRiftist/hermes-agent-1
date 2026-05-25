# Overnight Audit — 2026-05-25

## System State

### Gateway (Mac)
- Hermes gateway running: PID 13770, 3:30 runtime — healthy
- Ollama running on port 11434 — healthy
- Hermes process itself: ~747MB RSS — normal

### SSH Tunnel (Cron)
- Job `ssh-tunnel-linux-ollama` (18c522493e5a): every 5 min, last_status=ok ✅
- Forwards Mac :11435 → Linux :11434

### Disk Space
- 309 GB free out of 460 GB — plenty of headroom

### Memory
- ~118MB free pages (macOS compresses aggressively, this is normal)
- No swap activity — healthy

### Models on Mac (7 models via Ollama)
| Model | Size | Type | Notes |
|-------|------|------|-------|
| `qwen3-coder:30b-a3b-q4_k_M` | 29.6GB | **MoE** | 🔴 NEW — may be key discovery |
| `qwen2.5-coder:32b-instruct-q4_K_M-96k` | 18.9GB | Dense Q4 | 96K context config |
| `qwen2.5-coder:32b-instruct-q4_K_M` | 18.9GB | Dense Q4 | Standard version |
| `qwen3:14b` | 9.3GB | Dense Q4 | Good candidate |
| `qwen2.5-coder:14b` | 9.0GB | Dense Q4 | Good candidate |
| `qwen2.5-coder:7b` | 4.7GB | Dense Q4 | Lightweight |
| `qwen3:8b` | 5.2GB | Dense Q4 | Control baseline |

### SSH to Linux
- ✅ Passwordless key auth working
- ✅ Linux Ollama responding (no models loaded on GPU currently)
- ✅ NOPASSWD sudo active

---

## Issues Found

### 🔴 CRITICAL: bench_mac_gpu.py still uses MLX, not Ollama
The script at `~/.hermes/scripts/bench_mac_gpu.py` still imports `from mlx_lm import load, generate` and tries to download `mlx-community/` models from HF Hub. Those models don't exist there, and no HF token is configured. **This script would never run as-is.**

**Fix:** Rewrite to use Ollama API (`/api/generate`) with Metal backend. Ollama on Mac already uses Metal natively for Apple Silicon.

### 🔴 IMPORTANT: New model discovered — qwen3-coder:30b-a3b-q4_k_M
This is a **Mixture-of-Experts** (MoE) model with 30.5B total parameters but only a fraction active per token. Key implications:
- **Much smaller GPU footprint** than a dense 32B (estimated ~8-12B active params)
- **Could fit on M2 Pro GPU** with room for context
- **30B-level coding quality** at closer to 8B compute cost
- This model may be **the answer** to "best coder on Mac GPU"
- **Must be included in benchmark**

### ⚠️ BUG: linux-ollama base_url in config.yaml
Current: `http://127.0.0.1:11434/v1`
Problem: From the Mac, port 11434 is the **Mac's own** Ollama, not Linux's.
Should be: `http://127.0.0.1:11435/v1` (the SSH tunnel endpoint)
Impact: Any Hermes fallback to `linux-ollama` provider hits local Ollama instead of Linux.

### ⚠️ BUG: API keys in config.yaml plaintext
OpenRouter, DeepSeek, and X.AI keys are in config.yaml in cleartext. User wanted `.env` approach.

### ⚠️ IMPROVEMENT: No timeout/retry on Ollama API calls
Benchmark script has no retry logic. If Ollama hangs or returns partial output, the script hangs.

### ⚠️ IMPROVEMENT: Context sizes in config.yaml may be unrealistic
Mac 32B coder set to 8192 — reasonable for CPU but if running on GPU (via Ollama/Metal), could be higher. Should benchmark to find actual ceiling.

---

## Recommended Actions

1. **Rewrite benchmark script** for Ollama API + Metal backend (include qwen3-coder:30b MoE)
2. **Fix config.yaml** linux-ollama URL
3. **Launch benchmark** overnight, sequential, auto-saving
4. **Move API keys to .env** after benchmark (lower priority)
5. **Validate trimmer protocol** on Linux 8B after we have benchmark results

---

## Proposed Benchmark Models (Updated)

| # | Model | Size on Disk | GPU Fit? | Why |
|---|-------|-------------|----------|-----|
| 1 | `qwen2.5-coder:32b` | 18.9GB | ❌ CPU only | Baseline (already tested ~8K) |
| 2 | `qwen2.5-coder:14b` | 9.0GB | ✅ Tight fit | Candidate 1 |
| 3 | `qwen2.5-coder:7b` | 4.7GB | ✅ Comfortable | Candidate 2 |
| 4 | `qwen3-coder:30b-a3b` | 29.6GB | ⚡ MoE — test it | **Dark horse candidate** |
| 5 | `qwen3:8b` | 5.2GB | ✅ Easy | Control baseline |

Context ceiling test for each: 2K, 4K, 8K, 12K, 16K, 24K, 32K, 48K
Quality test: code review prompt at each model's max context
Total time estimate: 3-4 hours sequential