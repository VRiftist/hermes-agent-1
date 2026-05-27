#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES SELF-IMPROVEMENT ENGINE
Captures feedback, tracks prompt performance, and proposes improvements.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

FEEDBACK_FILE = os.path.expanduser("~/.hermes/self-improvement/feedback.jsonl")
PROMPT_REGISTRY = os.path.expanduser("~/.hermes/self-improvement/prompt_registry.json")
PERF_LOG = os.path.expanduser("~/.hermes/self-improvement/performance.jsonl")


def record_feedback(session_id: str, model: str, prompt: str,
                    response: str, rating: int, comment: str = "",
                   ):
    """
    Record operator feedback on a model response.
    rating: 1-5 (1=terrible, 5=perfect)
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "model": model,
        "prompt_preview": prompt[:200],
        "response_preview": response[:200],
        "rating": max(1, min(5, rating)),
        "comment": comment,
    }
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def get_model_stats(model: str, days: int = 7) -> dict:
    """Get aggregate performance stats for a model."""
    if not os.path.exists(FEEDBACK_FILE):
        return {"ratings": [], "avg": 0, "count": 0}

    cutoff = time.time() - (days * 86400)
    ratings = []
    with open(FEEDBACK_FILE, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                if ts.timestamp() >= cutoff:
                    if entry["model"] == model:
                        ratings.append(entry["rating"])
            except (json.JSONDecodeError, KeyError):
                continue

    if not ratings:
        return {"ratings": [], "avg": 0, "count": 0}

    return {
        "ratings": ratings,
        "avg": round(sum(ratings) / len(ratings), 2),
        "count": len(ratings),
        "distribution": {i: ratings.count(i) for i in range(1, 6)},
    }


def track_prompt_performance(prompt_hash: str, model: str,
                              latency_ms: int, cost_usd: float,
                              rating: Optional[int] = None):
    """Track how specific prompt patterns perform over time."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_hash": prompt_hash,
        "model": model,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "rating": rating,
    }
    os.makedirs(os.path.dirname(PERF_LOG), exist_ok=True)
    with open(PERF_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def suggest_improvements() -> list:
    """Analyze feedback and suggest model/routing improvements."""
    suggestions = []

    if not os.path.exists(FEEDBACK_FILE):
        return ["No feedback data yet — collect ratings to enable suggestions"]

    # Check all model stats
    from pathlib import Path
    models_dir = Path(__file__).parent.parent / "scripts" / "model_routing.py"

    # Analyze low-rated responses
    low_ratings = []
    recent_ratings = []
    with open(FEEDBACK_FILE, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                rating = entry.get("rating", 3)
                model = entry.get("model", "unknown")
                comment = entry.get("comment", "")
                recent_ratings.append(entry)
                if rating <= 2:
                    low_ratings.append({"model": model, "comment": comment})
            except (json.JSONDecodeError, KeyError):
                continue

    if low_ratings:
        by_model = {}
        for r in low_ratings:
            m = r["model"]
            if m not in by_model:
                by_model[m] = []
            by_model[m].append(r["comment"])

        for model, comments in by_model.items():
            if len(comments) >= 3:
                suggestions.append(
                    f"⚠️ Model '{model}' has {len(comments)} low ratings. "
                    f"Consider switching to alternative model. Comments: {comments[:3]}"
                )

    # Check if cost is trending up
    if os.path.exists(PERF_LOG):
        recent_costs = []
        with open(PERF_LOG, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    recent_costs.append(entry["cost_usd"])
                except (json.JSONDecodeError, KeyError):
                    continue

        if len(recent_costs) >= 10:
            avg_recent = sum(recent_costs[-10:]) / 10
            avg_older = sum(recent_costs[:10]) / min(10, len(recent_costs) - 10)
            if avg_recent > avg_older * 1.5:
                suggestions.append(
                    f"💰 Costs trending up: recent avg ${avg_recent:.4f} vs older avg ${avg_older:.4f}. "
                    f"Consider shifting more work to local models."
                )

    return suggestions


def weekly_review():
    """Generate a weekly performance review."""
    models_to_check = [
        "mac-ollama:qwen3:14b",
        "deepseek:deepseek-v4-flash",
        "x-ai:grok-4.20-reasoning",
        "openrouter:ring-2.6-1t",
    ]

    review = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "period": "weekly",
    }

    model_performance = {}
    for model in models_to_check:
        stats = get_model_stats(model, days=7)
        model_performance[model] = stats

    review["model_performance"] = model_performance
    review["suggestions"] = suggest_improvements()

    return review


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "weekly":
        review = weekly_review()
        print(json.dumps(review, indent=2))
    else:
        print("Self-improvement engine self-test...")
        record_feedback("test-001", "mac-ollama:qwen3:14b",
                        "Write a hello world",
                        "print('hello world')", 5, "Perfect")
        record_feedback("test-002", "deepseek:deepseek-v4-pro",
                        "Analyze this code",
                        "The code has issues:...", 2, "Missed edge cases")

        stats = get_model_stats("mac-ollama:qwen3:14b")
        print(f"  Model stats: avg rating={stats['avg']}, count={stats['count']}")

        suggestions = suggest_improvements()
        print(f"  Suggestions: {suggestions}")
        print("Self-improvement engine ready. ✅")