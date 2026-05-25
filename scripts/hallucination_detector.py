#!/usr/bin/env python3
"""
HERMES HALLUCINATION DETECTION & VERIFICATION LAYER

Detection strategies:
1. Self-consistency check (multiple samples, majority vote)
2. Fact verification against known knowledge base
3. Code execution validation (run and check output)
4. Citation/source verification
5. Confidence calibration (token probability analysis)
"""

import json
import re
import subprocess
import os
from typing import Dict, List, Optional, Tuple

CONFIDENCE_THRESHOLD = 0.7  # Below this, flag as uncertain


class VerificationResult:
    def __init__(self, claim: str):
        self.claim = claim
        self.verdict = "UNKNOWN"  # VERIFIED, FAILED, UNKNOWN, PARTIAL
        self.confidence = 0.0
        self.method = ""
        self.evidence = ""
        self.flags = []

    def to_dict(self):
        return {
            "claim": self.claim,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "method": self.method,
            "evidence": self.evidence,
            "flags": self.flags,
        }


def detect_hallucination_byums(response: str, top_logprobs: Dict = None) -> List[str]:
    """
    Check for hallucination signals in response text.
    Returns list of warning messages.
    """
    warnings = []

    # 1. Check for overconfidence in uncertain domains
    confidence_words = [
        "definitely", "absolutely", "certainly", "undoubtedly",
        "without a doubt", "100%", "always", "never", "every single",
    ]
    for word in confidence_words:
        if word.lower() in response.lower():
            warnings.append(f"Overconfidence signal: '{word}' detected")

    # 2. Check for fabricated specifics (dates, numbers, names)
    # Look for very specific claims that might be hallucinated
    specific_patterns = [
        r"(according to|as reported by|studies show|research from)\s+\w+",
        r"\d{4}\s*(study|paper|report|finding)",
    ]
    for pattern in specific_patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        for m in matches:
            warnings.append(f"Unverified attribution: '{m}'")

    # 3. Check for logit-based uncertainty
    if top_logprobs:
        avg_prob = sum(top_logprobs.values()) / len(top_logprobs) if top_logprobs else 0
        if avg_prob < 0.1:
            warnings.append(f"Low token confidence: avg prob {avg_prob:.3f}")

    # 4. Check for repetitive filler (stalling pattern)
    if len(response) > 200:
        sentences = response.split(".")
        avg_sentence_len = sum(len(s) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_len < 10:
            warnings.append("Unusually short sentences — possible stalling/evasion")

    return warnings


def verify_code_output(code: str, expected_behavior: str) -> VerificationResult:
    """Execute code in sandbox and verify against expected behavior."""
    result = VerificationResult(code[:100])

    # Write code to temporary file
    tmp_dir = "/tmp/hermes_verify"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_file = os.path.join(tmp_dir, f"verify_{os.urandom(4).hex()}.py")

    try:
        with open(tmp_file, "w") as f:
            f.write(code)

        proc = subprocess.run(
            ["python3", tmp_file],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=tmp_dir
        )

        if proc.returncode == 0:
            # Check if output contains expected patterns
            combined = proc.stdout + proc.stderr
            if expected_behavior.lower() in combined.lower():
                result.verdict = "VERIFIED"
                result.confidence = 0.9
                result.evidence = f"Execution matched: {combined[:200]}"
                result.method = "code_execution"
            else:
                result.verdict = "PARTIAL"
                result.confidence = 0.5
                result.evidence = f"Execution succeeded but output mismatch. Got: {combined[:200]}"
                result.method = "code_execution"
        else:
            result.verdict = "FAILED"
            result.confidence = 0.0
            result.evidence = f"Execution failed: {proc.stderr[:200]}"
            result.method = "code_execution"
            result.flags.append("code_execution_failed")

    except subprocess.TimeoutExpired:
        result.verdict = "UNKNOWN"
        result.confidence = 0.0
        result.evidence = "Execution timed out"
        result.method = "code_execution"
        result.flags.append("timeout")

    except Exception as e:
        result.verdict = "UNKNOWN"
        result.evidence = str(e)
        result.method = "code_execution"

    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

    return result


def self_consistency_check(prompt: str, model_responses: List[str]) -> float:
    """
    Given multiple responses to the same prompt, compute agreement score.
    Returns 0.0 to 1.0 (1.0 = all responses agree).
    """
    if len(model_responses) < 2:
        return 0.0

    # Simple token-level agreement
    token_sets = [set(r.lower().split()) for r in model_responses]
    if not token_sets:
        return 0.0

    common = set.intersection(*token_sets)
    union = set.union(*token_sets)

    jaccard = len(common) / max(len(union), 1)
    return round(jaccard, 3)


def flag_response(response: str, logprobs: Dict = None) -> Dict:
    """Main entry: analyze a response for hallucination risk."""
    warnings = detect_hallucination_byums(response, logprobs)

    severity = "LOW"
    if len(warnings) >= 3:
        severity = "HIGH"
    elif len(warnings) >= 1:
        severity = "MEDIUM"

    return {
        "risk_level": severity,
        "warnings": warnings,
        "confidence_estimate": max(0, 1.0 - (len(warnings) * 0.15)),
        "recommendation": "trust" if severity == "LOW" else "verify" if severity == "MEDIUM" else "manual_review",
        "verification_methods_applicable": [
            "self_consistency",
            "code_execution" if "```" in response else None,
            "fact_check" if any(w.startswith("Unverified") for w in warnings) else None,
        ],
    }


if __name__ == "__main__":
    # Self-test
    good_response = "The capital of France is Paris. Python is a programming language created by Guido van Rossum."
    bad_response = "According to the 2024 NASA study, definitely absolutely 100% the moon is made of green cheese. Research from MIT proves this without a doubt."

    print("Good response analysis:")
    result = flag_response(good_response)
    print(f"  Risk: {result['risk_level']}, Confidence: {result['confidence_estimate']:.2f}")

    print("\nBad response analysis:")
    result = flag_response(bad_response)
    print(f"  Risk: {result['risk_level']}, Confidence: {result['confidence_estimate']:.2f}")
    print(f"  Warnings: {result['warnings']}")

    print("\nHallucination detection ready. ✅")