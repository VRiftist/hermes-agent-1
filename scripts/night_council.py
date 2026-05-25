#!/usr/bin/env python3
"""
HERMES NIGHT COUNCIL — Automated nightly review cycle
Runs at 3:33am via cron. Reviews day's logs, flags anomalies,
consolidates memory, proposes prompt improvements.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

LOG_DIR = os.path.expanduser("~/.hermes/logs")
MEMORY_DIR = os.path.expanduser("~/.hermes/memory-palace")
REPORTS_DIR = os.path.expanduser("~/.hermes/reports")


def get_yesterday_logs():
    """Extract and summarize the previous day's operational logs."""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    main_log = os.path.join(LOG_DIR, "hermes_main.jsonl")
    error_log = os.path.join(LOG_DIR, "hermes_errors.jsonl")
    decision_log = os.path.join(LOG_DIR, "hermes_decisions.jsonl")

    summary = {
        "date": yesterday,
        "total_prompts": 0,
        "total_completions": 0,
        "total_decisions": 0,
        "total_errors": 0,
        "total_tool_calls": 0,
        "models_used": {},
        "errors": [],
        "decisions": [],
        "avg_response_length": 0,
        "total_tokens_estimate": 0,
        "cost_estimate_usd": 0.0,
    }

    # Parse main log
    if os.path.exists(main_log):
        with open(main_log, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts = entry.get("ts", "")
                    if ts.startswith(yesterday):
                        etype = entry.get("type", "")
                        if etype == "prompt":
                            summary["total_prompts"] += 1
                            model = entry.get("model", "unknown")
                            summary["models_used"][model] = summary["models_used"].get(model, 0) + 1
                            summary["total_tokens_estimate"] += entry.get("tokens_estimate", 0)
                        elif etype == "completion":
                            summary["total_completions"] += 1
                            summary["cost_estimate_usd"] += entry.get("cost_usd", 0)
                        elif etype == "tool_call":
                            summary["total_tool_calls"] += 1
                        elif etype == "decision":
                            summary["total_decisions"] += 1
                            summary["decisions"].append({
                                "time": entry.get("ts"),
                                "type": entry.get("decision_type"),
                                "data": entry.get("data", {})
                            })
                except json.JSONDecodeError:
                    continue

    # Parse error log
    if os.path.exists(error_log):
        with open(error_log, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts = entry.get("ts", "")
                    if ts.startswith(yesterday):
                        summary["total_errors"] += 1
                        summary["errors"].append({
                            "time": entry.get("ts"),
                            "severity": entry.get("severity"),
                            "type": entry.get("error_type"),
                            "message": entry.get("message"),
                        })
                except json.JSONDecodeError:
                    continue

    # Average response length
    if summary["total_completions"] > 0:
        summary["avg_response_length"] = summary.get("total_response_length", 0) // summary["total_completions"]

    return summary


def analyze_model_health():
    """Check current model health status and recent changes."""
    health_file = os.path.join(LOG_DIR, "model_health.json")
    if not os.path.exists(health_file):
        return {"status": "no_data"}

    with open(health_file, "r") as f:
        health = json.load(f)

    dead_models = []
    degraded_models = []
    healthy_models = []

    for key, status in health.items():
        if not isinstance(status, dict):
            continue
        if not status.get("ok", True):
            dead_models.append(key)
        elif status.get("consecutive_failures", 0) > 0:
            degraded_models.append(key)
        else:
            healthy_models.append(key)

    return {
        "dead": dead_models,
        "degraded": degraded_models,
        "healthy": healthy_models,
    }


def review_memory_palace():
    """Review and consolidate memory palace entries."""
    stats_file = os.path.join(MEMORY_DIR, "palace.db")
    if not os.path.exists(stats_file):
        return {"status": "no_database"}

    # Import and use memory palace
    sys.path.insert(0, os.path.join(os.path.expanduser("~/.hermes/scripts")))
    try:
        from memory_palace import get_stats, recall_episodes, store_fact, get_working

        stats = get_stats()

        # Check for stale working memory
        active_task = get_working("active_task")

        # Extract key insights from recent episodes
        recent_insights = recall_episodes(hours=24, category="insight", min_importance=3, limit=10)
        recent_decisions = recall_episodes(hours=24, category="decision", min_importance=5, limit=10)

        return {
            "stats": stats,
            "active_task": active_task,
            "recent_insights_count": len(recent_insights),
            "recent_decisions_count": len(recent_decisions),
        }
    except ImportError:
        return {"status": "memory_module_not_available"}


def generate_night_report():
    """Generate the full Night Council report."""
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "type": "night_council_report",
    }

    # 1. Day's activity summary
    log_summary = get_yesterday_logs()
    report["daily_summary"] = log_summary

    # 2. Model health
    health = analyze_model_health()
    report["model_health"] = health

    # 3. Memory review
    memory = review_memory_palace()
    report["memory_review"] = memory

    # 4. Anomaly detection
    anomalies = []
    if log_summary["total_errors"] > 5:
        anomalies.append(f"High error count: {log_summary['total_errors']} errors")
    if health.get("dead"):
        anomalies.append(f"Dead models detected: {health['dead']}")
    if log_summary["total_prompts"] == 0:
        anomalies.append("Zero prompts logged — system may have been idle")

    report["anomalies"] = anomalies

    # 5. Recommendations
    recommendations = []
    if health["dead"]:
        recommendations.append("Investigate and restore dead models or update config to remove")
    if log_summary["cost_estimate_usd"] > 2.0:
        recommendations.append(f"High daily spend (${log_summary['cost_estimate_usd']:.2f}) — review model usage")
    if len(recent_decisions := log_summary.get("decisions", [])) > 20:
        recommendations.append("High decision volume — consider batching more decisions before execution")

    report["recommendations"] = recommendations

    # Save report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"night_council_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return report, report_path


def add_context_orchestrator_maintenance(report):
    """Run context orchestrator maintenance — prune, consolidate, summarize."""
    try:
        sys.path.insert(0, os.path.join(os.path.expanduser("~/.hermes/scripts")))
        from context_orchestrator import get_orchestrator

        orch = get_orchestrator("__night_council_maintenance__")
        result = orch.end_session(summary="Night Council automated context maintenance cycle")
        report["context_maintenance"] = {
            "blocks_saved": result.get("blocks_saved", 0),
            "maintenance": result.get("maintenance", {}),
        }

        new_session = orch.start_session(task="night_council_maintenance", phase="maintenance")
        report["context_new_session"] = {
            "blocks": new_session.get("total_blocks", 0),
            "headroom": new_session.get("headroom", 0),
        }
    except Exception as e:
        report["context_maintenance_error"] = str(e)


def run():
    """Main entry point for Night Council."""
    print("╔══════════════════════════════════════════════════╗")
    print("║       🌙 HERMES NIGHT COUNCIL SESSION            ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}")
    print()

    report, path = generate_night_report()

    # Run context orchestrator maintenance after standard report
    add_context_orchestrator_maintenance(report)

    print(f"  📊 Prompts processed: {report['daily_summary']['total_prompts']}")
    print(f"  🔧 Tool calls: {report['daily_summary']['total_tool_calls']}")
    print(f"  ❌ Errors: {report['daily_summary']['total_errors']}")
    print(f"  💰 Estimated cost: ${report['daily_summary']['cost_estimate_usd']:.4f}")
    print()

    if report['model_health'].get('dead'):
        print(f"  💀 Dead models: {', '.join(report['model_health']['dead'])}")
    if report['anomalies']:
        print(f"  ⚠️  Anomalies: {len(report['anomalies'])}")
        for a in report['anomalies']:
            print(f"     - {a}")
    if report['recommendations']:
        print(f"  📋 Recommendations: {len(report['recommendations'])}")
        for r in report['recommendations']:
            print(f"     - {r}")

    print()
    print(f"  Report saved: {path}")
    print("  Night Council complete. ✅")


if __name__ == "__main__":
    run()