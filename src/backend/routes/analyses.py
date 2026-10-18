"""Analyses endpoints — serves analysis results to the frontend."""
from fastapi import APIRouter
from pydantic import BaseModel

from src.backend.core.verifier import analyze as run_analysis

router = APIRouter(prefix="/api", tags=["api"])


class AnalyzeRequest(BaseModel):
    repo_url: str = "github.com/renata89/verifAI"
    pr_number: int = 1
    pr_title: str = "PR Analysis"
    diff: str = ""
    ac_text: str = ""


# In-memory store for analyses
analyses_store: list[dict] = []

# Seed demo data so the dashboard isn't empty
_seed_demo: bool = True
if _seed_demo:
    from src.backend.core.verifier import analyze as _run
    _demo = _run(
        repo_url="github.com/renata89/verifAI",
        pr_number=42,
        pr_title="Add user authentication module",
        diff="def login(): pass",
        ac_text="1. User can register with email and password\n2. Password must be at least 8 characters\n3. Welcome email sent after registration",
    )
    analyses_store.append(_demo.model_dump())

    _demo2 = _run(
        repo_url="github.com/renata89/verifAI",
        pr_number=43,
        pr_title="Add API rate limiting",
        diff="from redis import Redis",
        ac_text="1. 100 requests per minute per API key\n2. Return X-RateLimit-* headers\n3. Configurable rate limit via env vars",
    )
    analyses_store.append(_demo2.model_dump())


@router.get("/analyses")
async def list_analyses():
    """Return all analyses performed so far."""
    return analyses_store


@router.post("/analyze")
async def analyze_pr(req: AnalyzeRequest):
    """Run analysis and store the result."""
    result = run_analysis(
        repo_url=req.repo_url,
        pr_number=req.pr_number,
        pr_title=req.pr_title,
        diff=req.diff,
        ac_text=req.ac_text,
    )
    data = result.model_dump()
    analyses_store.insert(0, data)  # newest first
    return data


@router.get("/stats")
async def get_stats():
    """Return aggregate statistics."""
    if not analyses_store:
        return {"total_analyzed": 0, "passing": 0, "total_acs": 0, "implemented_acs": 0}

    total = len(analyses_store)
    passing = sum(1 for a in analyses_store if a["overall_score"] >= 0.7)
    acs = sum(len(a.get("fragments", [])) for a in analyses_store)
    implemented = sum(
        1 for a in analyses_store for f in a.get("fragments", [])
        if f["status"] == "implemented"
    )
    return {
        "total_analyzed": total,
        "passing": passing,
        "total_acs": acs,
        "implemented_acs": implemented,
    }
