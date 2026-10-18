import { useState, useEffect } from 'react'
import './App.css'

interface ACFragment {
  text: string
  status: 'implemented' | 'partial' | 'missing' | 'wrong'
  confidence: number
  explanation: string
}

interface Analysis {
  id: string
  repo_url: string
  pr_number: number
  pr_title: string
  overall_score: number
  fragments: ACFragment[]
  summary: string
  timestamp: string
}

const STATUS_EMOJI: Record<string, string> = {
  implemented: '✓',
  partial: '~',
  missing: '✗',
  wrong: '!',
}

function App() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch from backend or use demo data
    fetchAnalyses()
  }, [])

  async function fetchAnalyses() {
    try {
      const resp = await fetch('/api/analyses')
      if (resp.ok) {
        const data = await resp.json()
        setAnalyses(data)
      } else {
        // Demo data when backend isn't running
        setAnalyses(getDemoData())
      }
    } catch {
      setAnalyses(getDemoData())
    } finally {
      setLoading(false)
    }
  }

  function getDemoData(): Analysis[] {
    return [
      {
        id: '1',
        repo_url: 'github.com/renata89/verifAI',
        pr_number: 42,
        pr_title: 'Add user authentication module',
        overall_score: 0.75,
        timestamp: new Date().toISOString(),
        summary: '2 of 3 ACs partially implemented.',
        fragments: [
          { text: 'User can register with email and password', status: 'implemented', confidence: 0.92, explanation: 'Registration endpoint exists with email/password validation.' },
          { text: 'Password must be at least 8 characters', status: 'partial', confidence: 0.65, explanation: 'Length check exists but no special character requirement.' },
          { text: 'Welcome email sent after registration', status: 'missing', confidence: 0.88, explanation: 'No email service call found after user creation.' },
        ],
      },
      {
        id: '2',
        repo_url: 'github.com/renata89/verifAI',
        pr_number: 43,
        pr_title: 'Add API rate limiting',
        overall_score: 0.33,
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        summary: 'Rate limiting partially implemented, missing headers and configuration.',
        fragments: [
          { text: '100 requests per minute per API key', status: 'implemented', confidence: 0.95, explanation: 'Rate limit counter implemented with Redis.' },
          { text: 'Return X-RateLimit-* headers', status: 'missing', confidence: 0.90, explanation: 'No rate limit headers in response.' },
          { text: 'Configurable rate limit via env vars', status: 'missing', confidence: 0.85, explanation: 'Hardcoded limit of 100, no env var support.' },
        ],
      },
    ]
  }

  function scoreColor(score: number): string {
    if (score >= 0.7) return 'green'
    if (score >= 0.4) return 'yellow'
    return 'red'
  }

  const totalAnalyzed = analyses.length
  const passingPRs = analyses.filter(a => a.overall_score >= 0.7).length
  const totalACs = analyses.reduce((sum, a) => sum + a.fragments.length, 0)
  const implementedACs = analyses.reduce((sum, a) => sum + a.fragments.filter(f => f.status === 'implemented').length, 0)

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">V</div>
          <span>VerifAI</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="verifai-btn verifai-btn--primary">New Analysis</button>
        </div>
      </header>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-label">PRs Analyzed</div>
          <div className="stat-value">{totalAnalyzed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Passing</div>
          <div className={`stat-value ${scoreColor(passingPRs / Math.max(totalAnalyzed, 1))}`}>{passingPRs}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">ACs Implemented</div>
          <div className={`stat-value ${scoreColor(implementedACs / Math.max(totalACs, 1))}`}>{implementedACs}/{totalACs}</div>
        </div>
      </div>

      <h2 className="section-title">Recent Analyses</h2>

      {loading ? (
        <div className="empty-state"><p>Loading...</p></div>
      ) : analyses.length === 0 ? (
        <div className="empty-state">
          <h3>No analyses yet</h3>
          <p>Submit a PR or use the CLI to analyze your first Acceptance Criteria.</p>
          <code style={{ background: 'var(--verifai-bg-elevated)', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.8125rem', display: 'inline-block' }}>
            python -m src.cli analyze --ac "User can login" --diff "def login(): pass"
          </code>
        </div>
      ) : (
        analyses.map(analysis => (
          <div key={analysis.id} className="analysis-card">
            <div className="analysis-header">
              <div className="pr-info">
                <h3>{analysis.pr_title}</h3>
                <p>{analysis.repo_url} · PR #{analysis.pr_number} · {new Date(analysis.timestamp).toLocaleDateString()}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className={`stat-value ${scoreColor(analysis.overall_score)}`} style={{ fontSize: '1.5rem' }}>
                  {(analysis.overall_score * 100).toFixed(0)}%
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--verifai-text-muted)' }}>score</div>
              </div>
            </div>

            <div className="verifai-score" style={{ marginBottom: '1rem' }}>
              <div className="verifai-score__fill" style={{
                width: `${analysis.overall_score * 100}%`,
                background: analysis.overall_score >= 0.7 ? 'var(--verifai-status-implemented)' :
                           analysis.overall_score >= 0.4 ? 'var(--verifai-status-partial)' :
                           'var(--verifai-status-missing)'
              }} />
            </div>

            <ul className="ac-list">
              {analysis.fragments.map((frag, i) => (
                <li key={i} className="ac-item">
                  <div className={`ac-status ${frag.status}`}>
                    {STATUS_EMOJI[frag.status]}
                  </div>
                  <div className="ac-text">{frag.text}</div>
                  <div className="ac-conf">{(frag.confidence * 100).toFixed(0)}%</div>
                </li>
              ))}
            </ul>

            <p style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--verifai-text-muted)' }}>
              {analysis.summary}
            </p>
          </div>
        ))
      )}
    </div>
  )
}

export default App
