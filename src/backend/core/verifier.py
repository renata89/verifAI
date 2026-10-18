"""
VerifAI — Requirements Verifier Engine

Core logic: matches Acceptance Criteria against code diffs using an LLM.
With caching to avoid redundant API calls.
"""

from __future__ import annotations
import hashlib
from typing import List

from src.backend.models.schemas import (
    ACFragment,
    ACStatus,
    AnalysisResult,
)


# ─── In-memory cache ──────────────────────────────────────────────
_cache: dict[str, AnalysisResult] = {}
_cache_hits = 0
_cache_misses = 0


def _cache_key(diff: str, ac_text: str) -> str:
    """Return a deterministic key for a (diff, ac) pair."""
    raw = (diff + ac_text).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Rough LLM cost estimate in USD (GPT-4o rates)."""
    return (input_tokens / 1_000_000) * 2.50 + (output_tokens / 1_000_000) * 10.00


def _split_ac(ac_text: str) -> List[str]:
    """Split multi-line AC into individual fragments."""
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


# ─── LLM Prompt Template ──────────────────────────────────────────
PROMPT_TEMPLATE = """You are VerifAI, a traceability analyzer. Your job is to check if the provided code diff satisfies the given Acceptance Criteria (AC).

## Acceptance Criteria:
{ac_text}

## Code Diff:
```diff
{diff}
```

## Instructions:
For each AC fragment, determine:
- **implemented**: The code clearly implements this AC.
- **partial**: Some aspects are implemented but not all.
- **missing**: The AC is not addressed in the code at all.
- **wrong**: The code does something different than the AC specifies.

Return your analysis as a JSON object with:
- "fragments": list of {{"text": "...", "status": "...", "confidence": 0.0-1.0, "explanation": "..."}}
- "summary": "one sentence overall verdict"
- "input_tokens": integer estimate

Be strict. It's better to flag a partial as missing than to give a false positive.
"""


def analyze(repo_url: str, pr_number: int, pr_title: str, diff: str, ac_text: str) -> AnalysisResult:
    """
    Analyze a PR diff against Acceptance Criteria.
    Uses LLM to determine implementation status of each AC.
    """
    global _cache_hits, _cache_misses

    key = _cache_key(diff, ac_text)
    if key in _cache:
        _cache_hits += 1
        return _cache[key]

    _cache_misses += 1

    # ── Parse AC into fragments ──
    fragments = _split_ac(ac_text)

    # ── Build the prompt ──
    prompt = PROMPT_TEMPLATE.format(ac_text=ac_text, diff=diff)

    # ── Call LLM (stub for now — replace with real API call) ──
    result = _call_llm(prompt, fragments, diff, ac_text)

    result.repo_url = repo_url
    result.pr_number = pr_number

    # Cache the result
    _cache[key] = result
    return result


def _call_llm(prompt: str, fragments: list[str], diff: str, ac_text: str) -> AnalysisResult:
    """
    Stub LLM call.
    TODO: Replace with actual OpenAI/Anthropic API call.
    Returns dummy analysis for development.
    """
    # Estimate tokens (very rough: 4 chars ≈ 1 token)
    input_tokens = len(prompt) // 4
    output_tokens = len(fragments) * 60

    return AnalysisResult(
        repo_url="",
        pr_number=0,
        overall_score=0.75,
        fragments=[
            ACFragment(
                text=fragments[0] if fragments else ac_text,
                status=ACStatus.partial,
                confidence=0.7,
                explanation="[STUB] Needs real LLM call. Based on placeholder analysis.",
            )
        ],
        summary="[STUB] Analysis pending. Replace with actual LLM response.",
        llm_cost_estimate=_estimate_cost(input_tokens, output_tokens),
    )
