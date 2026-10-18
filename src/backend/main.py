"""
VerifAI — Backend Application
Minimal MVP: Requirements Verifier
"""

from fastapi import FastAPI
from src.backend.routes.webhooks import router as webhook_router
from src.backend.routes.health import router as health_router

app = FastAPI(
    title="VerifAI",
    description="AI Traceability Engine — Requirements Verifier",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(webhook_router)
