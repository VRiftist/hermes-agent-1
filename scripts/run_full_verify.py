#!/usr/bin/env python3
import os, sys
sys.path.insert(0, "/Users/lumenhubai/.hermes/scripts")
sys.path.insert(0, "/Users/lumenhubai/.hermes/hermes-agent")
os.environ["WIKI_PATH"] = os.path.expanduser("~/.hermes/wiki")

import yaml
config_path = os.path.expanduser("~/.hermes/config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)
assert "providers" in config
print("Config validation OK")

with open(config_path) as f:
    config = yaml.safe_load(f)
assert "providers" in config
print("Config validation OK")

from model_routing import classify_task, select_model
tests = [
    ("Write a Python function to parse JSON", "code_generation"),
    ("Analyze why this algorithm is O(n^2)", "reasoning"),
    ("Research the history of machine learning", "research"),
    ("Write a poem about AI", "creative"),
    ("Review this code for bugs", "review"),
    ("Run ls -la in /tmp", "tool_use"),
    ("What's the weather like?", "general"),
]
for prompt, expected in tests:
    result = classify_task(prompt)
    status = "PASS" if result == expected else "FAIL"
    print(f"  [{status}] '{prompt[:40]}...' -> {result}" + (f" (expected {expected})" if result != expected else ""))

creative = select_model("creative", "design something", budget_usd=5.0)
review = select_model("review", "review this code", budget_usd=5.0)
print(f"Creative routing: {creative['provider']}/{creative['model']}")
print(f"Review routing: {review['provider']}/{review['model']}")

from context_orchestrator import start_session, trim_context, end_session
r = start_session(task="test", phase="testing")
trim = trim_context(11000)
end = end_session(summary="test")
print(f"Orchestrator: blocks={r['total_blocks']}, trim recovered={trim['tokens_recovered']}, end saved={end['blocks_saved']}")

from memory_palace import store_episode, store_fact, get_stats
store_episode("test", "action", "self-test", importance=4)
store_fact("test", "data")
stats = get_stats()
print(f"Memory palace: {stats['episodic_count']} episodes, {stats['semantic_count']} facts")

from kimi_client import status as kimi_status, _primary_key, _secondary_key
st = kimi_status()
print(f"Kimi: {st['keys_loaded']} keys, model={st['model']}, primary={_primary_key[:18] if _primary_key else 'none'}...")

from key_guardian import load_env
env = load_env()
loaded = [k for k, v in env.items() if k.endswith("_KEY") and v and v not in ("***", "")]
print(f"Key guardian: {len(loaded)} keys loaded: {loaded}")

from gateway_integration import gateway_message_start, gateway_message_end
s = gateway_message_start("test", "code_generation")
e = gateway_message_end("done")
print(f"Gateway integration: lifecycle OK")

from circuit_breaker import check_health, report_health
report_health("test-provider", "test-model", True, 100)
h = check_health("test-provider:test-model")
print(f"Circuit breaker: healthy={h}")

from api_error_handler import classify_api_error
# Test Kimi 401 misclassification
err = classify_api_error({"error": "401 rate limit"}, provider="moonshot", model="moonshot-v1-8k", http_status=401)
print(f"Error handler: Kimi 401 rate limit -> category={err.category}, retryable={err.is_retryable}, rotate={err.should_rotate_key}")
assert err.category == "TRANSIENT", f"Expected TRANSIENT got {err.category}"
assert err.should_rotate_key == True
# Test real 401 (non-transient for non-Kimi)
err2 = classify_api_error({"error": "invalid key"}, provider="openrouter", model="ring", http_status=401)
print(f"Error handler: OpenRouter 401 invalid key -> category={err2.category}, retryable={err2.is_retryable}")
# Test 429
err3 = classify_api_error({"error": "rate limit"}, provider="deepseek", model="deepseek-v4-flash", http_status=429)
print(f"Error handler: DeepSeek 429 -> category={err3.category}, retryable={err3.is_retryable}")

from night_council import run as run_nightly
run_nightly()
print("Night council: OK")

print("\n=== ALL TESTS PASSED ===")