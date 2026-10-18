# Sample 2: Search API
# Acceptance Criteria:
# - Search returns paginated results
# - Results ordered by relevance score
# - Each result includes id, title, and score
# - Empty query returns empty results

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()

class SearchResult(BaseModel):
    id: int
    title: str
    score: float

class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    page: int
    query: str

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(default="", min_length=0),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    # Empty query returns empty results (AC #4)
    if not q:
        return {"results": [], "total": 0, "page": page, "query": q}
    
    # Search in database (AC #1)
    offset = (page - 1) * per_page
    rows = await database.fetch_all(
        "SELECT id, title, content FROM documents WHERE content LIKE :q ORDER BY id LIMIT :lim OFFSET :off",
        {"q": f"%{q}%", "lim": per_page, "off": offset}
    )
    
    # BUG: Missing relevance score (AC #2, #3 not implemented!)
    # Should use full-text search with ts_rank to get scores
    
    results = [{"id": r["id"], "title": r["title"], "score": 0.0} for r in rows]
    
    return {"results": results, "total": len(rows), "page": page, "query": q}
