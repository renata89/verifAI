Sample test files for VerifAI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These files are used to manually test the VerifAI analysis engine.

How to use:
  python -m src.cli analyze \
    --ac "$(cat tests/fixtures/samples/ac-login.txt)" \
    --diff "$(cat tests/fixtures/samples/code-login.py)"

Files:
  ac-login.txt    ← Acceptance Criteria for login system
  code-login.py   ← Code implementation (with intentional bugs)
  ac-search.txt   ← Acceptance Criteria for search API
  code-search.py  ← Code implementation (with intentional bugs)

Intentionally included bugs:
  • Login: missing welcome email (AC #3)
  • Search: missing relevance scoring (AC #2, #3)
  • Search: using basic LIKE instead of full-text search

Expected results (with real LLM):
  • Login: AC #1 ✅, AC #2 ✅, AC #3 ❌ (missing)
  • Search: AC #1 ✅, AC #2 ❌ (wrong), AC #3 ❌ (missing), AC #4 ✅
