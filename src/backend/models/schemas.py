"""
VerifAI — Pydantic Schemas
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


class ACStatus(str, Enum):
    implemented = "implemented"
    partial = "partial"
    missing = "missing"
    wrong = "wrong"
    error = "error"


class ACFragment(BaseModel):
    """A single Acceptance Criteria fragment."""
    text: str
    status: ACStatus
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = ""
    source_line: int | None = None


class AnalysisRequest(BaseModel):
    """Incoming analysis request from a webhook."""
    repo_url: str
    pr_number: int
    pr_title: str
    pr_description: str
    diff: str
    ac_text: str


class AnalysisResult(BaseModel):
    """Result of analyzing one PR against its ACs."""
    repo_url: str
    pr_number: int
    overall_score: float = Field(ge=0.0, le=1.0)
    fragments: list[ACFragment] = []
    summary: str = ""
    llm_cost_estimate: float = 0.0
