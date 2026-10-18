"""
VerifAI — LLM Client

Handles communication with OpenAI-compatible LLM APIs.
Supports OpenAI, Anthropic, and custom endpoints.
"""

from __future__ import annotations
import json
import os
from typing import Any

import httpx

# Default to OpenAI, override via env
LLM_API_KEY = os.environ.get("VERIFAI_LLM_API_KEY", "")
LLM_API_URL = os.environ.get("VERIFAI_LLM_API_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("VERIFAI_LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are VerifAI, a traceability analyzer for code diffs.
Your job is to check if the provided code diff satisfies the given Acceptance Criteria (AC).

For each AC fragment, determine one of:
- **implemented**: The code clearly implements this AC. All requirements are met.
- **partial**: Some aspects are implemented but not all. Missing edge cases or details.
- **missing**: The AC is not addressed in the code at all.
- **wrong**: The code does something different than the AC specifies.

Be strict. False positives (saying implemented when it's not) are worse than false negatives.

Respond ONLY with a JSON object matching this schema:
{
  "fragments": [
    {
      "text": "the exact AC text",
      "status": "implemented|partial|missing|wrong",
      "confidence": 0.0-1.0,
      "explanation": "brief justification citing specific code evidence"
    }
  ],
  "summary": "one sentence overall verdict"
}
"""


async def analyze_with_llm(ac_text: str, diff: str) -> dict[str, Any]:
    """
    Send AC + diff to LLM for analysis.
    Returns parsed JSON response.
    """
    if not LLM_API_KEY:
        return _stub_response(ac_text)

    prompt = f"""## Acceptance Criteria:
{ac_text}

## Code Diff:
```diff
{diff}
```"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{LLM_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def _stub_response(ac_text: str) -> dict[str, Any]:
    """Fallback when no API key is configured."""
    fragments = _split_fragments(ac_text)
    return {
        "fragments": [
            {
                "text": f,
                "status": "partial",
                "confidence": 0.7,
                "explanation": "⏳ No LLM API key set. Set VERIFAI_LLM_API_KEY env var for real analysis.",
            }
            for f in fragments
        ],
        "summary": "Stub analysis — set VERIFAI_LLM_API_KEY for real results.",
    }


def _split_fragments(ac_text: str) -> list[str]:
    """Split AC text into individual fragments."""
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
