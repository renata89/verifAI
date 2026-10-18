"""
VerifAI — Integration Tests

Tests the API endpoints and webhook functionality.
Run with:
    cd ~/Desktop/verifAI && source venv/bin/activate && python -m pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)


def test_health_check():
    """Health endpoint should return 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "verifai"


def test_manual_analysis_stub():
    """POST /webhook/analyze should return analysis result."""
    payload = {
        "repo_url": "test/repo",
        "pr_number": 1,
        "pr_title": "Test PR",
        "pr_description": "## Acceptance Criteria\n- User can login\n- Password is validated",
        "diff": "def login(): pass",
        "ac_text": "User can login with email and password",
    }
    resp = client.post("/webhook/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
    assert "fragments" in data
    assert "summary" in data


def test_github_webhook_opened():
    """Simulate a GitHub PR opened webhook."""
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Add login feature",
            "body": "## Acceptance Criteria\n- User can login with email\n- Password validation works",
        },
        "repository": {"html_url": "https://github.com/test/repo"},
    }
    resp = client.post("/webhook/github", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("analyzed", "no_ac_found")


def test_github_webhook_skipped():
    """Non-PR events should be skipped."""
    payload = {"action": "labeled", "pull_request": {"number": 1}}
    resp = client.post("/webhook/github", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "skipped"


def test_no_ac_in_pr():
    """PR without AC should return no_ac_found."""
    payload = {
        "action": "opened",
        "pull_request": {"number": 1, "title": "Fix typo", "body": "Just a small fix"},
        "repository": {"html_url": "https://github.com/test/repo"},
    }
    resp = client.post("/webhook/github", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_ac_found"
