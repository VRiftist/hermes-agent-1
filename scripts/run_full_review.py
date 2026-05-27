#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""Full Blueprint Multi-Model Review — LOCAL-FIRST with cloud fallback.

Tries cloud API first, falls back to local Ollama if keys are missing/broken.
Kimi patience mode preserved for when keys activate.
"""
import sys, os, json, urllib.request, time, signal, logging
sys.path.insert(0, "/Users/lumenhubai/.hermes/scripts")
os.chdir("/Users/lumenhubai/.hermes")

from memory_palace import store_episode, store_fact, get_stats

# TTY-safe: ignore SIGINT/SIGTERM gracefully for non-interactive runs
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("blueprint_review")

# ─── CONFIG ──────────────────────────────────────────────────────────
MAX_KIMI_RETRIES = 50
KIMI_BASE_DELAY = 30.0
KIMI_MAX_DELAY = 300.0

# ─── LOAD KEYS ───────────────────────────────────────────────────────
def _load_env():
    """Load keys from .env, but live environment variables always win.

    This lets Hermes inject real keys via its config (os.environ) while
    preserving .env as a local backup / template.  The merge order is:
      1. .env file on disk (baseline)
      2. os.environ (runtime — set by Hermes gateway, higher priority)
    """
    env = {}
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    # Live env vars override file values (e.g. keys injected by Hermes)
    for key in list(env.keys()):
        live = os.environ.get(key)
        if live:
            env[key] = live
    return env

_env = _load_env()

def _key_ok(key):
    return key and key not in ("***", "") and len(key) > 10

# ─── LOCAL OLLAMA (always works if Ollama is running) ────────────────

def call_ollama(model: str, prompt: str, max_tokens: int = 8192) -> str:
    """Call local Ollama model."""
    url = "http://localhost:11434/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    })
    start = time.time()
    req = urllib.request.Request(url, data=body.encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
        elapsed = time.time() - start
        content = result["choices"][0]["message"]["content"]
        logger.info(f"Ollama/{model}: {len(content):,} chars in {elapsed:.1f}s")
        return content

def _check_ollama_models():
    """List available local models."""
    url = "http://localhost:11434/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        logger.warning(f"Ollama not reachable: {e}")
        return []

# ─── CLOUD API CALLS ────────────────────────────────────────────────

def _call_deepseek(model: str, prompt: str) -> str:
    key = _env.get("DEEPSEEK_API_KEY", "")
    if not _key_ok(key):
        raise RuntimeError("DEEPSEEK_API_KEY missing/placeholder in .env")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.7, "max_tokens": 8192})
    req = urllib.request.Request(url, data=body.encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def _call_xai(prompt: str) -> str:
    key = _env.get("XAI_API_KEY", "")
    if not _key_ok(key):
        raise RuntimeError("XAI_API_KEY missing/placeholder in .env")
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = json.dumps({"model": "grok-4.20-reasoning", "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.7, "max_tokens": 8192})
    req = urllib.request.Request(url, data=body.encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def _call_openrouter(model: str, prompt: str) -> str:
    key = _env.get("OPENROUTER_KEY_1", "")
    if not _key_ok(key):
        raise RuntimeError("OPENROUTER_KEY_1 missing/invalid in .env")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "HTTP-Referer": "https://lumenhub.ai", "X-Title": "LumenHub Blueprint Review"}
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.7, "max_tokens": 8192})
    req = urllib.request.Request(url, data=body.encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def _call_kimi(prompt: str) -> str:
    from kimi_client import chat_completion
    last_error = None
    for attempt in range(1, MAX_KIMI_RETRIES + 1):
        try:
            result = chat_completion(messages=[{"role": "user", "content": prompt}],
                                     max_tokens=4096, temperature=0.7)
            if "error" in result:
                last_error = result["error"]
                if "NO_KIMI_KEY" in str(result):
                    raise RuntimeError(f"Kimi key not configured: {last_error}")
                delay = min(KIMI_BASE_DELAY * (2 ** (attempt - 1)), KIMI_MAX_DELAY)
                time.sleep(delay)
                continue
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = str(e)
            delay = min(KIMI_BASE_DELAY * (2 ** (attempt - 1)), KIMI_MAX_DELAY)
            time.sleep(delay)
    raise RuntimeError(f"Kimi failed after {MAX_KIMI_RETRIES} attempts: {last_error}")

# ─── REVIEW TASKS ────────────────────────────────────────────────────

def make_review(rid, label, cloud_fn, local_model, purpose, prompt, persona="analyst"):
    """Create a review task with cloud-first, local-fallback strategy."""
    def execute():
        # Try cloud first
        cloud_error = None
        try:
            result = cloud_fn(prompt)
            return {"source": "cloud", "content": result}
        except Exception as e:
            cloud_error = str(e)[:200]

        # Fall back to local
        local_prompt = f"You are {persona}. {prompt}"
        result = call_ollama(local_model, local_prompt)
        return {"source": f"local (cloud failed: {cloud_error})", "content": result}

    return {"id": rid, "label": label, "purpose": purpose, "execute": execute}

REVIEWS = [
    make_review(
        "grok-pain-points",
        "Grok-4.20-reasoning: User Pain Points & Wish List",
        lambda p: _call_xai(p),
        "qwen3:14b",
        "Leverage X/Twitter discourse for PKM pain points",
        persona="a technology analyst who reads X/Twitter and Reddit daily",
        prompt=(
            "You are analyzing what users ACTUALLY want from PKM (Personal Knowledge Management) tools. "
            "Using your knowledge of X/Twitter, Reddit communities (r/ObsidianMD, r/logseq, r/Notion, r/productivity), "
            "and productivity discourse, deliver a detailed report covering:\n\n"
            "1. Top 10 pain points users report about current PKM apps (Obsidian, Notion, Logseq, Roam, Bear)\n"
            "2. Most-requested features that don't exist well anywhere\n"
            "3. Enterprise vs consumer gap — teams vs individuals\n"
            "4. AI-integration complaints — gimmicky vs genuinely useful\n"
            "5. Onboarding friction and dropoff points\n"
            "6. Sync/reliability nightmares\n"
            "7. Mobile vs desktop feature gaps\n"
            "8. What users actually want from AI in note-taking\n"
            "9. Power user workflows mainstream apps fail to support\n"
            "10. Pricing model frustrations\n\n"
            "Be specific with patterns from real discussions. This is for LumenHub — a local-first AI-augmented PKM in Flutter."
        )
    ),
    make_review(
        "deepseek-architecture",
        "DeepSeek v4-pro: Architecture Audit",
        lambda p: _call_deepseek("deepseek-v4-pro", p),
        "qwen3-coder",
        "Ruthless adversarial audit of Hermes + LumenHub architecture",
        persona="a senior systems architect known for finding critical flaws",
        prompt=(
            "Perform a ruthless adversarial architecture review of the Hermes Agent + LumenHub system. "
            "Find every weakness, edge case, and failure mode.\n\n"
            "ARCHITECTURE:\n"
            "- Flutter 3.44 + Riverpod (BLoC state management)\n"
            "- SQLite + drift (no FTS5 yet)\n"
            "- 6-tier context trimming: T0(identity never trim) T1(task) T2(recent) T3(semantic) T4(background/compressed) T5(tool/compressed) T6(conversation/deleted)\n"
            "- 12K token budget, warn@9K, hard_trim@6K\n"
            "- Consult/merge: classify->route->consult(Athena)->quality_gate(Ring)\n"
            "- Models: qwen3:14b, qwen3-coder:30b-a3b, qwen3:8b, deepseek-v4-flash, grok-4.20, ring-2.6-1t, kimi-v1-8k\n"
            "- Hybrid compression: T4/T5 rephrase+tag, T6 delete\n"
            "- SQLite memory palace, Night Council cron, Key guardian, FSRS spaced repetition\n\n"
            "CHALLENGES TO ADDRESS:\n"
            "1. Can context trimming silently corrupt multi-step tasks?\n"
            "2. Ring disagrees with Athena - what happens?\n"
            "3. Are token budgets realistic per model?\n"
            "4. Primary model fails mid-task - cascade?\n"
            "5. Where does this silently degrade vs fail loudly?\n"
            "6. SQLite at 10K+ entries - performance?\n"
            "7. Compression vs deletion - optimal?\n"
            "8. Race conditions in concurrent access?\n"
            "9. Security vulnerabilities?\n"
            "10. Single highest-ROI change?\n"
            "11. Multi-session continuity gaps?\n"
            "12. Non-linear importance (T6 joke key to T1 decision)?"
        )
    ),
    make_review(
        "ring-design",
        "Ring-2.6-1t (OpenRouter): Comprehensive Design Review",
        lambda p: _call_openrouter("inclusionai/ring-2.6-1t", p),
        "qwen3-coder",
        "Final quality gate — principal architect review",
        persona="a principal systems architect with 15 years experience",
        prompt=(
            "You are a principal systems architect. Perform comprehensive design review of Hermes Agent + LumenHub.\n\n"
            "1. SYSTEM DESIGN - Rate 1-10 with reasoning:\n"
            "   Multi-model deliberate routing, 6-tier context lifecycle, Memory palace, Consult/merge/quality-gate, Circuit breaker, Night Council\n\n"
            "2. SCALABILITY:\n"
            "   SQLite at 10K/100K/1M entries, context window growth, multi-device sync, routing table expansion. What breaks first?\n\n"
            "3. SECURITY:\n"
            "   .env vault, redact_pii, sandboxed execution, planned E2E encryption. Biggest attack surface?\n\n"
            "4. MAINTAINABILITY:\n"
            "   Script organization, YAML config, 10/10 self-test coverage, documentation. Hardest to maintain in 12 months?\n\n"
            "5. PRODUCT (Flutter):\n"
            "   Architecture decisions, Riverpod fit, Hermes as AI backend, SQLite+drift, roadmap priorities. Changes?\n\n"
            "6. MISSING/DANGEROUS ASSUMPTIONS:\n"
            "   What critical assumptions could fail catastrophically?"
        )
    ),
    make_review(
        "kimi-creative",
        "Kimi v1-8k (Moonshot DIRECT): Creative/Design/UX Review",
        lambda p: _call_kimi(p),
        "qwen3:14b",
        "Creative/aesthetic/UX judgment — the 'artist' lens",
        persona="a creative design consultant specializing in UX and product aesthetics",
        prompt=(
            "You are a creative design consultant specializing in UX and product aesthetics. "
            "Review the LumenHub + Hermes Agent system from a design and user experience perspective:\n\n"
            "1. What does 'local-first AI PKM' feel like as a product identity? Is it compelling?\n"
            "2. Evaluate the Flutter UI decisions: dark theme, Material 3, Memory Palette widget — what's working, what feels off?\n"
            "3. Onboarding experience: what would make a new user understand this product in 60 seconds?\n"
            "4. Information architecture: is the 6-tier context trimming concept user-facing or invisible? Should users see it?\n"
            "5. Naming & branding: LumenHub, Hermes, Athena, Memory Palace — cohesive? Confusing?\n"
            "6. Mobile UX: how does this translate to Android/iOS with smaller screens?\n"
            "7. What emotions should using this product evoke? Does the current design achieve that?\n"
            "8. Micro-interactions and delight: what small details would make this feel premium?\n\n"
            "Be honest, specific, and opinionated. This is the creative lens the other models can't provide."
        )
    ),
]

# ─── EXECUTION ───────────────────────────────────────────────────────

def run_review(review):
    rid = review["id"]
    label = review["label"]
    purpose = review["purpose"]

    print(f"\n{'━' * 70}")
    print(f"▶ {label}")
    print(f"  Purpose: {purpose}")
    print(f"{'━' * 70}")

    start = time.time()
    try:
        result = review["execute"]()
        elapsed = time.time() - start
        source = result["source"]
        content = result["content"]
        print(f"  ✅ DONE via {source} — {len(content):,} chars in {elapsed:.1f}s")
        preview = content[:150].replace("\n", " ").strip()
        print(f"  Preview: {preview[:100]}...")
        return {
            "id": rid, "label": label, "source": source,
            "provider": "cloud" if source == "cloud" else "local-ollama",
            "elapsed_s": round(elapsed, 1),
            "result": content, "error": None
        }
    except Exception as e:
        elapsed = time.time() - start
        err_msg = str(e)
        print(f"  ❌ FAILED after {elapsed:.1f}s: {err_msg[:200]}")
        return {
            "id": rid, "label": label, "source": "failed",
            "provider": "none", "elapsed_s": round(elapsed, 1),
            "result": None, "error": err_msg
        }

def compile_results(results, output_path):
    with open(output_path, "w") as f:
        f.write("# Multi-Model Blueprint Review — Full Results\n\n")
        f.write("> **Generated by**: Hermes Agent — Local-first with cloud fallback\n")
        f.write(f"> **Date**: 2026-05-25\n")
        f.write("> **Note**: Cloud keys were placeholders/invalid. Results from local Ollama models with cloud-persona prompts.\n")
        f.write("> **When cloud keys are provided**: re-run `python3 scripts/run_full_review.py` for native model output.\n\n")

        for r in results:
            f.write(f"## {r['label']}\n\n")
            f.write(f"| Field | Value |\n|-------|-------|\n")
            f.write(f"| Source | {r['source']} |\n")
            f.write(f"| Time | {r['elapsed_s']}s |\n")
            if r.get('error'):
                f.write(f"| Status | ❌ FAILED |\n\n```\n{r['error']}\n```\n\n")
            else:
                f.write(f"| Status | ✅ Complete ({len(r.get('result','')):,} chars) |\n\n")
                f.write(f"### Model's Analysis\n\n")
                f.write(f"{r['result']}\n\n")
            f.write("---\n\n")

        # Coverage matrix
        f.write("## Coverage Matrix\n\n")
        f.write("| Review | Source | Status |\n")
        f.write("|--------|--------|--------|\n")
        for r in results:
            s = "✅ Complete" if not r.get('error') else "❌ Failed"
            f.write(f"| {r['label'][:55]} | {r['source'][:15]} | {s} |\n")

        # Summary
        success = sum(1 for r in results if not r.get('error'))
        total = len(results)
        cloud = sum(1 for r in results if r.get('source') == 'cloud')
        local = sum(1 for r in results if 'local' in str(r.get('source', '')))
        f.write(f"\n## Summary\n\n")
        f.write(f"- **Successful**: {success}/{total}\n")
        f.write(f"- **Cloud-sourced**: {cloud}/{total}\n")
        f.write(f"- **Local-sourced**: {local}/{total}\n")
        f.write(f"- **Total chars generated**: {sum(len(r.get('result','')) for r in results if r.get('result')):,}\n")
        f.write(f"- **Total time**: {sum(r['elapsed_s'] for r in results):.1f}s\n")
        f.write(f"\n## Action Items\n\n")
        f.write("- [ ] Provide DeepSeek API key at platform.deepseek.com → re-run for native DeepSeek analysis\n")
        f.write("- [ ] Provide xAI API key at console.x.ai → re-run for native Grok analysis\n")
        f.write("- [ ] Fix OpenRouter key or replace → re-run for native Ring analysis\n")
        f.write("- [ ] Activate Kimi at platform.moonshot.cn → re-run for native Kimi creative review\n")

    print(f"\nResults → {output_path}")

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("  FULL BLUEPRINT REVIEW — LOCAL-FIRST + CLOUD FALLBACK")
    print("=" * 70)

    # Check local Ollama
    models = _check_ollama_models()
    print(f"\n🔧 Local Ollama models: {', '.join(models) if models else 'NOT REACHABLE'}")

    # Check cloud keys
    print("\n🔑 Cloud key status:")
    for name, val in [("DeepSeek", _env.get("DEEPSEEK_API_KEY","")),
                       ("xAI/Grok", _env.get("XAI_API_KEY","")),
                       ("OpenRouter", _env.get("OPENROUTER_KEY_1","")),
                       ("Kimi", _env.get("KIMI_API_KEY",""))]:
        ok = _key_ok(val)
        print(f"  {name}: {'✅ present' if ok else '❌ missing/placeholder'}")
    print()

    results = []
    for review in REVIEWS:
        result = run_review(review)
        results.append(result)

    outpath = "/Users/lumenhubai/.hermes/docs/multi-model-review-results.md"
    compile_results(results, outpath)

    # Log to memory palace
    try:
        stats = get_stats()
        episodic = stats.get('episodes', stats.get('episodic_count', 'n/a'))
        semantic = stats.get('facts', stats.get('semantic_count', 'n/a'))
        store_episode("multi-model-review-20260525-v4", "infrastructure",
            f"4-model local-first review v4: {sum(1 for r in results if not r.get('error'))}/4 complete. "
            f"Cloud keys: placeholder. Palace: {episodic}ep/{semantic}facts",
            importance=10, tags=["review", "blueprint", "multi-model", "local-first", "cloud-keys-broken"])
        store_fact("Multi-model review v4 — local fallback",
            f"{sum(1 for r in results if not r.get('error'))}/4 complete via Ollama. Cloud keys need provisioning.")
        print(f"  Memory palace: {episodic}ep/{semantic}facts")
    except Exception as e:
        print(f"  Palace note: {e}")

    success = sum(1 for r in results if not r.get('error'))
    print(f"\n{'=' * 70}")
    print(f"  DONE — {success}/{len(results)} reviews completed (local fallback)")
    print(f"{'=' * 70}\n")