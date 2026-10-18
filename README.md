# VerifAI — AI Traceability Engine

**Verify. Trace. Trust.**

VerifAI is an AI-powered traceability engine for software development teams. It bridges the gap between requirements, code, tests, and documentation.

## Core Capabilities

- **Requirements Verifier** — Does the implementation actually satisfy the Acceptance Criteria?
- **Test Gap Analyzer** — Which ACs have no test coverage? Generate suggested test cases.
- **Documentation Drift Detector** — Does the code do what the docs say?

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  GitHub/Git │◄──►│  Trace Engine│◄──►│   LLM Core  │
│  Lab / API  │    │  (FastAPI)   │    │  (RAG+Code) │
└─────────────┘    └──────┬───────┘    └─────────────┘
                         │
                   ┌─────▼──────┐
                   │ PostgreSQL │
                   │  (Storage) │
                   └────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / FastAPI |
| Frontend | React + TypeScript |
| Database | PostgreSQL |
| LLM | OpenAI / Anthropic API |
| Auth | GitHub OAuth |
| CI/CD | GitHub Actions |

## Project Status

🚧 **MVP Phase** — Requirements Verifier (focus)

## Getting Started

```bash
# Clone
git clone git@github.com:renata89/verifAI.git
cd verifAI

# Backend setup
cd src/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn main:app --reload
```
