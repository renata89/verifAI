"""
VerifAI — Requirements Verifier Engine

Core logic: matches Acceptance Criteria against code diffs using an LLM.
With caching to avoid redundant API calls.
"""

from __future__ import annotations
import asyncio
import hashlib
import os
from typing import List

from src.backend.models.schemas import (
    ACFragment,
    ACStatus,
    AnalysisResult,
)
from src.backend.core.llm_client import analyze_with_llm

LLM_API_KEY = os.environ.get("VERIFAI_LLM_API_KEY", "")

# ─── In-memory cache ──────────────────────────────────────────────
_cache: dict[str, AnalysisResult] = {}
_cache_hits = 0
_cache_misses = 0


def _cache_key(diff: str, ac_text: str) -> str:
    raw = (diff + ac_text).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * 2.50 + (output_tokens / 1_000_000) * 10.00


def _split_ac(ac_text: str) -> List[str]:
    lines = [l.strip() for l in ac_text.strip().split("\n") if l.strip()]
    fragments = []
    current = ""
    for line in lines:
        if line[0].isdigit() or line.startswith("-") or line.startswith("*"):
            if current:
                fragments.append(current)
            current = line
        else:
            current = (current + " " + line).strip()
    if current:
        fragments.append(current)
    return fragments if fragments else [ac_text.strip()]


def _calculate_overall(fragments: list[ACFragment]) -> float:
    if not fragments:
        return 0.0
    weights = {
        ACStatus.implemented: 1.0,
        ACStatus.partial: 0.5,
        ACStatus.missing: 0.0,
        ACStatus.wrong: 0.0,
        ACStatus.error: 0.0,
    }
    return sum(weights.get(f.status, 0.0) * f.confidence for f in fragments) / len(fragments)


def _parse_llm_fragments(llm_result: dict, expected_fragments: list[str]) -> list[ACFragment]:
    """Parse LLM response into typed ACFragment objects."""
    raw = llm_result.get("fragments", [])
    parsed = []
    for item in raw:
        try:
            status = ACStatus(item.get("status", "missing"))
        except ValueError:
            status = ACStatus.error
        parsed.append(
            ACFragment(
                text=item.get("text", ""),
                status=status,
                confidence=min(max(item.get("confidence", 0.5), 0.0), 1.0),
                explanation=item.get("explanation", ""),
            )
        )
    return parsed


def _stub_fragments(expected: list[str]) -> list[ACFragment]:
    """Return stub fragments when no LLM is available."""
    return [
        ACFragment(
            text=e,
            status=ACStatus.partial,
            confidence=0.7,
            explanation="⏳ No LLM API key. Set VERIFAI_LLM_API_KEY for real analysis.",
        )
        for e in expected
    ]


def analyze(repo_url: str, pr_number: int, pr_title: str, diff: str, ac_text: str) -> AnalysisResult:
    global _cache_hits, _cache_misses

    key = _cache_key(diff, ac_text)
    if key in _cache:
        _cache_hits += 1
        return _cache[key]

    _cache_misses += 1
    fragments = _split_ac(ac_text)

    # Estimate tokens
    input_tokens = (len(ac_text) + len(diff)) // 4
    output_tokens = len(fragments) * 60

    # Call LLM or fallback to stub
    if LLM_API_KEY:
        try:
            llm_result = asyncio.run(analyze_with_llm(ac_text, diff))
            fragments_parsed = _parse_llm_fragments(llm_result, fragments)
            summary = llm_result.get("summary", "Analysis complete.")
            overall = _calculate_overall(fragments_parsed)
        except Exception as e:
            fragments_parsed = _stub_fragments(fragments)
            summary = f"LLM error: {e}"
            overall = 0.0
    else:
        fragments_parsed = _stub_fragments(fragments)
        summary = "[STUB] Set VERIFAI_LLM_API_KEY for real analysis."
        overall = 0.75

    result = AnalysisResult(
        repo_url=repo_url,
        pr_number=pr_number,
        overall_score=overall,
        fragments=fragments_parsed,
        summary=summary,
        llm_cost_estimate=_estimate_cost(input_tokens, output_tokens),
    )

    _cache[key] = result
    return result
