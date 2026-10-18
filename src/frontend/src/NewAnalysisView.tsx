import { useState } from 'react'

interface NewAnalysisProps {
  onCreated: () => void
  onBack: () => void
}

export default function NewAnalysisView({ onCreated, onBack }: NewAnalysisProps) {
  const [acText, setAcText] = useState('')
  const [codeDiff, setCodeDiff] = useState('')
  const [prTitle, setPrTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)

  async function handleSubmit() {
    if (!acText.trim()) {
      setError('Acceptance Criteria is required')
      return
    }
    if (!codeDiff.trim()) {
      setError('Code diff is required')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const resp = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: 'github.com/renata89/verifAI',
          pr_number: Date.now(),
          pr_title: prTitle || 'Manual Analysis',
          diff: codeDiff,
          ac_text: acText,
        }),
      })

      if (!resp.ok) {
        throw new Error(`API error: ${resp.status}`)
      }

      const data = await resp.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  function scoreColor(score: number) {
    if (score >= 0.7) return 'green'
    if (score >= 0.4) return 'yellow'
    return 'red'
  }

  const STATUS_EMOJI: Record<string, string> = {
    implemented: '✓',
    partial: '~',
    missing: '✗',
    wrong: '!',
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo" style={{ cursor: 'pointer' }} onClick={onBack}>
          <div className="logo-icon">←</div>
          <span>VerifAI / New Analysis</span>
        </div>
      </header>

      <div className="new-analysis-layout">
        {/* Input Form */}
        <div className="new-analysis-form">
          <div className="form-group">
            <label className="form-label">PR Title (optional)</label>
            <input
              className="form-input"
              placeholder="e.g. Add login feature"
              value={prTitle}
              onChange={e => setPrTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Acceptance Criteria *</label>
            <textarea
              className="form-textarea"
              placeholder={`Paste Acceptance Criteria here...

Examples:
1. User can login with email and password
2. Password must be at least 8 characters
3. Welcome email sent after registration

Or use ## AC format from GitHub PRs`}
              rows={8}
              value={acText}
              onChange={e => setAcText(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Code Diff *</label>
            <textarea
              className="form-textarea form-textarea--mono"
              placeholder={`Paste the code diff here...

@router.post("/login")
async def login(email, password):
    if len(password) < 8:
        return {"error": "too short"}
    return {"token": create_token(email)}`}
              rows={12}
              value={codeDiff}
              onChange={e => setCodeDiff(e.target.value)}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <button
            className="verifai-btn verifai-btn--primary"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : '▶ Run Analysis'}
          </button>
        </div>

        {/* Results Panel */}
        <div className="new-analysis-results">
          {loading && (
            <div className="empty-state">
              <p style={{ fontFamily: 'var(--verifai-font-mono)', fontSize: '0.875rem' }}>
                Analyzing...
              </p>
              <div className="loading-bar">
                <div className="loading-bar__fill" />
              </div>
            </div>
          )}

          {result && (
            <div className="detail-card">
              <div className="detail-header" style={{ marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1rem' }}>{result.pr_title || 'Analysis Result'}</h3>
                  <p className="detail-meta">{result.repo_url} · PR #{result.pr_number}</p>
                </div>
                <div className="detail-score">
                  <div className={`stat-value ${scoreColor(result.overall_score)}`} style={{ fontSize: '2rem' }}>
                    {(result.overall_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="verifai-score" style={{ marginBottom: '1rem' }}>
                <div className="verifai-score__fill" style={{
                  width: `${result.overall_score * 100}%`,
                  background: result.overall_score >= 0.7 ? 'var(--verifai-status-implemented)' :
                             result.overall_score >= 0.4 ? 'var(--verifai-status-partial)' :
                             'var(--verifai-status-missing)'
                }} />
              </div>

              {result.fragments?.map((frag: any, i: number) => (
                <div key={i} className="ac-item">
                  <div className={`ac-status ${frag.status}`}>{STATUS_EMOJI[frag.status]}</div>
                  <div className="ac-text">{frag.text}</div>
                  <div className="ac-conf">{(frag.confidence * 100).toFixed(0)}%</div>
                </div>
              ))}

              <p style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--verifai-text-muted)' }}>
                {result.summary}
                {result.llm_cost_estimate && (
                  <> · Cost: ${result.llm_cost_estimate.toFixed(5)}</>
                )}
              </p>
            </div>
          )}

          {!loading && !result && (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <h3>Enter AC + Code</h3>
              <p style={{ fontSize: '0.75rem' }}>
                Paste Acceptance Criteria and code diff on the left, then click "Run Analysis"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
