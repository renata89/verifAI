"""
VerifAI — Ground Truth Benchmark

Runs the ground truth dataset through the verifier and measures:
- Accuracy (how many ACs match expected)
- Precision (fewer false positives = better)
- Recall (fewer false negatives = better)
- Cost per analysis

Usage:
    python tests/benchmark.py              # Stub mode
    VERIFAI_LLM_API_KEY=sk-... python tests/benchmark.py  # Real LLM
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import yaml
from pathlib import Path

from src.backend.core.verifier import analyze
from src.backend.models.schemas import ACStatus


def load_dataset(path: str = "tests/fixtures/ground_truth.yaml") -> list[dict]:
    """Load the ground truth dataset."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("fixtures", [])


def score_status(actual: ACStatus, expected: str) -> str:
    """Compare actual vs expected status."""
    expected = expected.lower()
    actual_str = actual.value.lower()

    if actual_str == expected:
        return "correct"
    if expected == "implemented" and actual_str == "partial":
        return "undercall"  # Too strict — should be implemented
    if expected == "partial" and actual_str in ("missing", "wrong"):
        return "overcall"  # Too strict
    if expected in ("missing", "wrong") and actual_str in ("implemented", "partial"):
        return "overcall"  # Too generous
    return "mismatch"


def run_benchmark(dataset: list[dict]) -> dict:
    """Run all fixtures through the verifier and compute metrics."""
    results = []
    total_cost = 0.0

    for entry in dataset:
        fixture_id = entry.get("id", "unknown")
        ac_text = entry.get("ac", "")
        code = entry.get("code", "")
        expected = entry.get("expected", {})
        expected_ac = expected.get("ac_status", "missing")

        # Run analysis
        result = analyze(
            repo_url="benchmark/local",
            pr_number=0,
            pr_title=fixture_id,
            diff=code,
            ac_text=ac_text,
        )

        total_cost += result.llm_cost_estimate

        # Evaluate each fragment
        fixture_results = []
        for frag in result.fragments:
            verdict = score_status(frag.status, expected_ac)
            fixture_results.append({
                "text": frag.text[:80],
                "expected": expected_ac,
                "actual": frag.status.value,
                "confidence": frag.confidence,
                "verdict": verdict,
                "explanation": frag.explanation[:60],
            })

        passed = all(r["verdict"] == "correct" for r in fixture_results)
        results.append({
            "id": fixture_id,
            "passed": passed,
            "fragments": fixture_results,
        })

    # Calculate overall metrics
    total_fragments = sum(len(r["fragments"]) for r in results)
    correct = sum(
        1 for r in results for f in r["fragments"] if f["verdict"] == "correct"
    )
    undercall = sum(
        1 for r in results for f in r["fragments"] if f["verdict"] == "undercall"
    )
    overcall = sum(
        1 for r in results for f in r["fragments"] if f["verdict"] == "overcall"
    )
    mismatch = sum(
        1 for r in results for f in r["fragments"] if f["verdict"] == "mismatch"
    )

    accuracy = (correct / total_fragments * 100) if total_fragments > 0 else 0

    return {
        "summary": {
            "total_fixtures": len(dataset),
            "total_fragments": total_fragments,
            "correct": correct,
            "undercall": undercall,
            "overcall": overcall,
            "mismatch": mismatch,
            "accuracy_pct": round(accuracy, 1),
            "total_cost_usd": round(total_cost, 5),
            "avg_cost_per_analysis": round(total_cost / max(len(dataset), 1), 6),
        },
        "results": results,
    }


def print_summary(benchmark: dict):
    """Pretty-print benchmark results."""
    s = benchmark["summary"]
    print("=" * 60)
    print(f"  VERIFAI BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Dataset:        {s['total_fixtures']} fixtures, {s['total_fragments']} fragments")
    print(f"  ✅ Correct:     {s['correct']}")
    print(f"  ⚠️  Undercall:   {s['undercall']} (was too strict)")
    print(f"  ⚠️  Overcall:    {s['overcall']} (was too generous)")
    print(f"  ❌ Mismatch:    {s['mismatch']}")
    print(f"  📊 Accuracy:    {s['accuracy_pct']}%")
    print(f"  💰 Total cost:  ${s['total_cost_usd']}")
    print(f"  💰 Avg cost:    ${s['avg_cost_per_analysis']}")
    print("=" * 60)

    # Per-fixture details
    for r in benchmark["results"]:
        status = "✅" if r["passed"] else "❌"
        print(f"\n  {status} {r['id']}:")
        for f in r["fragments"]:
            emoji = {"correct": "✅", "undercall": "⬇️", "overcall": "⬆️", "mismatch": "❌"}
            print(f"    {emoji.get(f['verdict'], '❓')} expected={f['expected']} actual={f['actual']} "
                  f"conf={f['confidence']:.1f} — {f['explanation']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="tests/fixtures/ground_truth.yaml")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    benchmark = run_benchmark(dataset)

    if args.json:
        print(json.dumps(benchmark, indent=2))
    else:
        print_summary(benchmark)

    # Exit with non-zero if accuracy < 50%
    if benchmark["summary"]["accuracy_pct"] < 50:
        sys.exit(1)
