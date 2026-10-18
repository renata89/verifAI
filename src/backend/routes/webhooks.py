"""GitHub webhook endpoint for PR analysis."""
from fastapi import APIRouter, Request

from src.backend.core.verifier import analyze
from src.backend.models.schemas import AnalysisRequest, AnalysisResult

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/github")
async def github_pr_webhook(request: Request):
    """
    Receive a GitHub PR webhook and run Requirements Verifier analysis.
    """
    payload = await request.json()
    action = payload.get("action")
    
    # Only analyze on PR open or push
    if action not in ("opened", "synchronize"):
        return {"status": "skipped", "action": action}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    repo_url = repo.get("html_url", "")
    pr_number = pr.get("number", 0)
    pr_title = pr.get("title", "")
    pr_body = pr.get("body", "")
    diff = pr.get("diff", "")

    # Extract AC from PR description (or fetch from Jira)
    ac_text = _extract_ac(pr_body)

    if not ac_text:
        return {"status": "no_ac_found", "pr": pr_number}

    result: AnalysisResult = analyze(
        repo_url=repo_url,
        pr_number=pr_number,
        pr_title=pr_title,
        diff=diff,
        ac_text=ac_text,
    )

    return {
        "status": "analyzed",
        "pr": pr_number,
        "result": result.model_dump(),
    }


@router.post("/analyze")
async def manual_analysis(req: AnalysisRequest):
    """Manually submit a diff + AC for analysis (for testing/API use)."""
    result = analyze(
        repo_url=req.repo_url,
        pr_number=req.pr_number,
        pr_title=req.pr_title,
        diff=req.diff,
        ac_text=req.ac_text,
    )
    return result.model_dump()


def _extract_ac(body: str) -> str:
    """
    Extract Acceptance Criteria from a PR description.
    Looks for ## Acceptance Criteria or ## AC or similar headers.
    """
    if not body:
        return ""
    
    lines = body.split("\n")
    in_ac = False
    ac_lines = []
    
    # Common AC markers
    ac_markers = [
        "acceptance criteria", "ac:", "kryteria akceptacji",
        "## acceptance criteria", "## ac", "### acceptance criteria", "### ac",
    ]
    
    for line in lines:
        stripped = line.strip().lower()
        if any(marker in stripped for marker in ac_markers):
            in_ac = True
            continue
        if in_ac:
            # Stop at next section
            if stripped.startswith("##") and "acceptance" not in stripped.lower():
                break
            ac_lines.append(line)
    
    return "\n".join(ac_lines).strip()
