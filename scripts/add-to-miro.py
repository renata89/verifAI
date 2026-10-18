# VerifAI — Add Designs to Miro Board
# Uses Miro REST API v2 with developer token

import requests
import base64
import os

# Miro board ID
BOARD_ID = "uXjVEY0cdvw="
# Get token from env or prompt
MIRO_TOKEN = os.environ.get("MIRO_TOKEN", "")

if not MIRO_TOKEN:
    print("Need Miro API token.")
    print("1. Go to: https://miro.com/app/settings/user-profile/developer-tokens")
    print("2. Copy your token")
    print("3. Run: MIRO_TOKEN=xxx python scripts/add-to-miro.py")
    exit(1)

headers = {
    "Authorization": f"Bearer {MIRO_TOKEN}",
    "Content-Type": "application/json",
}

# Upload logo
logo_path = "docs/verifai-logo.png"
with open(logo_path, "rb") as f:
    logo_data = base64.b64encode(f.read()).decode()

print("Uploading logo...")

# Miro API: create image item from a URL (data URL works)
resp = requests.post(
    f"https://api.miro.com/v2/boards/{BOARD_ID}/images",
    headers=headers,
    json={
        "data": {"url": f"data:image/png;base64,{logo_data}"},
        "position": {"x": -300, "y": -200, "origin": "center"},
    },
)
print(f"Logo: {resp.status_code} — {resp.text[:100]}")

# Upload UI mockup
mockup_path = "docs/verifai-ui-mockup.png"
with open(mockup_path, "rb") as f:
    mockup_data = base64.b64encode(f.read()).decode()

print("Uploading UI mockup...")
resp = requests.post(
    f"https://api.miro.com/v2/boards/{BOARD_ID}/images",
    headers=headers,
    json={
        "data": {"url": f"data:image/png;base64,${mockup_data}"},
        "position": {"x": 300, "y": -200, "origin": "center"},
    },
)
print(f"Mockup: {resp.status_code} — {resp.text[:100]}")

# Add a sticky note with description
print("Adding description...")
resp = requests.post(
    f"https://api.miro.com/v2/boards/{BOARD_ID}/sticky_notes",
    headers=headers,
    json={
        "data": {
            "content": "VerifAI — AI Traceability Engine\n\n"
                       "MVP: Requirements Verifier\n"
                       "Phase 2: Test Gap Analyzer\n"
                       "Phase 3: Documentation Drift\n\n"
                       "Tech: FastAPI + React + LLM\n"
                       "GitHub: renata89/verifAI"
        },
        "position": {"x": 0, "y": 300, "origin": "center"},
    },
)
print(f"Note: {resp.status_code} — {resp.text[:100]}")
