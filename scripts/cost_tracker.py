#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES COST TRACKING
Monitors spend across all cloud providers in real-time.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict

COST_FILE = os.path.expanduser("~/.hermes/cost-tracking/costs.json")
DAILY_BUDGET_USD = 5.0
MONTHLY_BUDGET_USD = 100.0
ALERT_THRESHOLD = 0.8  # Alert at 80% of budget


# Actual pricing (per 1M tokens)
PRICING = {
    "deepseek:deepseek-v4-flash":   {"input": 0.14, "output": 0.28},
    "deepseek:deepseek-v4-pro":     {"input": 0.28, "output": 0.56},
    "x-ai:grok-4.20-reasoning":     {"input": 1.25, "output": 10.0},
    "openrouter:ring-2.6-1t":       {"input": 0.88, "output": 0.88},
    "openrouter:qwen3-14b":         {"input": 0.0, "output": 0.0},
    # Ollama models are free (local)
    "mac-ollama:qwen3:8b":          {"input": 0.0, "output": 0.0},
    "mac-ollama:qwen3:14b":         {"input": 0.0, "output": 0.0},
    "linux-ollama:qwen3-14b-128k":  {"input": 0.0, "output": 0.0},
}


def load_costs() -> Dict:
    if os.path.exists(COST_FILE):
        try:
            with open(COST_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"sessions": [], "daily_totals": {}, "monthly_totals": {}}


def save_costs(data: Dict):
    os.makedirs(os.path.dirname(COST_FILE), exist_ok=True)
    with open(COST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_call(model_key: str, tokens_input: int, tokens_output: int):
    """Record a single API call's cost."""
    costs = load_costs()
    pricing = PRICING.get(model_key, {"input": 0.0, "output": 0.0})

    input_cost = (tokens_input / 1_000_000) * pricing["input"]
    output_cost = (tokens_output / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model_key,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
    }
    costs["sessions"].append(entry)

    # Update daily total
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today not in costs["daily_totals"]:
        costs["daily_totals"][today] = 0.0
    costs["daily_totals"][today] += total_cost

    # Update monthly total
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    if month not in costs["monthly_totals"]:
        costs["monthly_totals"][month] = 0.0
    costs["monthly_totals"][month] += total_cost

    save_costs(costs)
    return total_cost


def get_daily_spend() -> float:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    costs = load_costs()
    return costs["daily_totals"].get(today, 0.0)


def get_monthly_spend() -> float:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    costs = load_costs()
    return costs["monthly_totals"].get(month, 0.0)


def check_budget_alerts() -> list:
    """Check if any budget thresholds are exceeded."""
    alerts = []
    daily = get_daily_spend()
    monthly = get_monthly_spend()

    if daily >= DAILY_BUDGET_USD:
        alerts.append(f"🔴 DAILY BUDGET EXCEEDED: ${daily:.2f} / ${DAILY_BUDGET_USD}")
    elif daily >= DAILY_BUDGET_USD * ALERT_THRESHOLD:
        alerts.append(f"🟡 Daily budget warning: ${daily:.2f} / ${DAILY_BUDGET_USD}")

    if monthly >= MONTHLY_BUDGET_USD:
        alerts.append(f"🔴 MONTHLY BUDGET EXCEEDED: ${monthly:.2f} / ${MONTHLY_BUDGET_USD}")
    elif monthly >= MONTHLY_BUDGET_USD * ALERT_THRESHOLD:
        alerts.append(f"🟡 Monthly budget warning: ${monthly:.2f} / ${MONTHLY_BUDGET_USD}")

    return alerts


def get_cost_summary() -> Dict:
    """Get comprehensive cost summary."""
    costs = load_costs()
    by_model = {}
    for entry in costs["sessions"]:
        model = entry["model"]
        if model not in by_model:
            by_model[model] = {"calls": 0, "total_cost": 0, "total_input_tokens": 0, "total_output_tokens": 0}
        by_model[model]["calls"] += 1
        by_model[model]["total_cost"] += entry["total_cost_usd"]
        by_model[model]["total_input_tokens"] += entry["tokens_input"]
        by_model[model]["total_output_tokens"] += entry["tokens_output"]

    for model in by_model:
        by_model[model]["total_cost"] = round(by_model[model]["total_cost"], 4)

    return {
        "by_model": by_model,
        "daily": get_daily_spend(),
        "monthly": get_monthly_spend(),
        "daily_budget": DAILY_BUDGET_USD,
        "monthly_budget": MONTHLY_BUDGET_USD,
        "total_calls": sum(m["calls"] for m in by_model.values()),
    }


if __name__ == "__main__":
    # Self-test
    print("Cost tracking self-test...")
    cost = record_call("deepseek:deepseek-v4-flash", 500, 300)
    print(f"  Recorded call: ${cost:.4f}")
    summary = get_cost_summary()
    print(f"  Total calls: {summary['total_calls']}")
    print(f"  Daily spend: ${summary['daily']:.4f}")
    print(f"  Budget alerts: {check_budget_alerts()}")
    print("Cost tracking ready. ✅")