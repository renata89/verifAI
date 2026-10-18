#!/usr/bin/env python3
"""
VerifAI — CLI Tool

Analyze code diffs against Acceptance Criteria from the command line.

Usage:
    # Analyze a diff file against AC text
    python -m src.cli analyze --ac "User can login" --diff "def login(): pass"

    # Analyze a GitHub PR (fetches diff + description)
    python -m src.cli pr --repo renata89/verifAI --pr 1
    
    # Run benchmark
    python -m src.cli benchmark
    
    # Set your LLM API key
    export VERIFAI_LLM_API_KEY="sk-..."
"""

import sys
import argparse
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.core.verifier import analyze
from src.backend.models.schemas import ACStatus


def cmd_analyze(args):
    """Analyze a diff against AC text."""
    result = analyze(
        repo_url=args.repo or "local",
        pr_number=args.pr or 0,
        pr_title=args.title or "CLI Analysis",
        diff=args.diff,
        ac_text=args.ac,
    )

    if args.json:
        print(json.dumps(result.model_dump(), indent=2, default=str))
        return

    print(f"\n{'='*60}")
    print(f"  VerifAI Analysis — PR #{result.pr_number}")
    print(f"{'='*60}")
    print(f"  Overall Score: {result.overall_score:.0%}")
    print(f"  Summary: {result.summary}")
    print(f"  Cost: ${result.llm_cost_estimate:.5f}")
    print(f"{'='*60}")

    for frag in result.fragments:
        emoji = {
            ACStatus.implemented: "✅",
            ACStatus.partial: "🔶",
            ACStatus.missing: "❌",
            ACStatus.wrong: "⚠️",
            ACStatus.error: "💥",
        }.get(frag.status, "❓")

        print(f"\n  {emoji} [{frag.status.value.upper()}] {frag.text[:80]}")
        print(f"     confidence: {frag.confidence:.0%}")
        if frag.explanation:
            print(f"     reason: {frag.explanation[:120]}")

    # Exit codes
    if result.overall_score < 0.5:
        sys.exit(1)


def cmd_benchmark(args):
    """Run the ground truth benchmark."""
    from tests.benchmark import load_dataset, run_benchmark, print_summary

    dataset = load_dataset(args.dataset)
    benchmark = run_benchmark(dataset)

    if args.json:
        print(json.dumps(benchmark, indent=2, default=str))
    else:
        print_summary(benchmark)

    if benchmark["summary"]["accuracy_pct"] < 50:
        sys.exit(1)


def cmd_pr(args):
    """Fetch a GitHub PR and analyze it."""
    import httpx

    repo = args.repo
    pr_num = args.pr
    github_token = os.environ.get("GITHUB_TOKEN", "")

    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    # Fetch PR details
    with httpx.Client() as client:
        pr_resp = client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_num}",
            headers=headers,
        )
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()

        # Fetch diff
        diff_resp = client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_num}",
            headers={**headers, "Accept": "application/vnd.github.v3.diff"},
        )

    pr_title = pr_data.get("title", "")
    pr_body = pr_data.get("body", "")
    diff = diff_resp.text if diff_resp.status_code == 200 else ""

    # Extract AC from PR body
    ac_text = _extract_ac_from_body(pr_body)

    if not ac_text:
        print("❌ No Acceptance Criteria found in PR description.")
        print("   Add ## AC or ## Acceptance Criteria section to the PR.")
        sys.exit(1)

    result = analyze(
        repo_url=f"https://github.com/{repo}",
        pr_number=pr_num,
        pr_title=pr_title,
        diff=diff,
        ac_text=ac_text,
    )

    print(json.dumps(result.model_dump(), indent=2, default=str))


def _extract_ac_from_body(body: str) -> str:
    """Extract AC section from PR body."""
    if not body:
        return ""
    lines = body.split("\n")
    in_ac = False
    ac_lines = []
    markers = [
        "acceptance criteria", "ac:", "kryteria akceptacji",
        "## acceptance criteria", "## ac", "### acceptance criteria",
    ]
    for line in lines:
        if any(m in line.strip().lower() for m in markers):
            in_ac = True
            continue
        if in_ac:
            if line.strip().startswith("##") and "acceptance" not in line.lower():
                break
            ac_lines.append(line)
    return "\n".join(ac_lines).strip()


def main():
    parser = argparse.ArgumentParser(description="VerifAI — AI Traceability Engine")
    subparsers = parser.add_subparsers(dest="command")

    # analyze
    ap = subparsers.add_parser("analyze", help="Analyze diff against AC")
    ap.add_argument("--ac", required=True, help="Acceptance Criteria text")
    ap.add_argument("--diff", required=True, help="Code diff text or @file.txt")
    ap.add_argument("--repo", help="Repository URL")
    ap.add_argument("--pr", type=int, help="PR number")
    ap.add_argument("--title", help="PR title")
    ap.add_argument("--json", action="store_true", help="JSON output")

    # benchmark
    bp = subparsers.add_parser("benchmark", help="Run accuracy benchmark")
    bp.add_argument("--dataset", default="tests/fixtures/ground_truth.yaml")
    bp.add_argument("--json", action="store_true")

    # pr
    pp = subparsers.add_parser("pr", help="Analyze a GitHub PR")
    pp.add_argument("--repo", required=True, help="owner/repo")
    pp.add_argument("--pr", type=int, required=True, help="PR number")

    args = parser.parse_args()

    if args.command == "analyze":
        if args.diff.startswith("@"):
            with open(args.diff[1:]) as f:
                args.diff = f.read()
        cmd_analyze(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "pr":
        cmd_pr(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
