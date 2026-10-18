import { useState, useEffect } from 'react'
import './App.css'

interface ACFragment {
  text: string
  status: 'implemented' | 'partial' | 'missing' | 'wrong'
  confidence: number
  explanation: string
}

interface Analysis {
  repo_url: string
  pr_number: number
  pr_title?: string
  overall_score: number
  fragments: ACFragment[]
  summary: string
  llm_cost_estimate?: number
  timestamp?: string
}

import NewAnalysisView from './NewAnalysisView'

const STATUS_EMOJI: Record<string, string> = {
  implemented: '✓',
  partial: '~',
  missing: '✗',
  wrong: '!',
}

const STATUS_LABEL: Record<string, string> = {
  implemented: 'Implemented',
  partial: 'Partial',
  missing: 'Missing',
  wrong: 'Wrong',
}

type View = 'dashboard' | 'detail' | 'new-analysis'

function App() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<View>('dashboard')
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null)

  useEffect(() => {
    fetchAnalyses()
  }, [])

  async function fetchAnalyses() {
    try {
      const resp = await fetch('/api/analyses')
      if (resp.ok) {
        const data = await resp.json()
        setAnalyses(data)
        setLoading(false)
        return
      }
    } catch {
      // Backend not running
    }
    setAnalyses([])
    setLoading(false)
  }

  function viewDetail(a: Analysis) {
    setSelectedAnalysis(a)
    setView('detail')
  }

  function backToDashboard() {
    setView('dashboard')
    setSelectedAnalysis(null)
  }

  function scoreColor(score: number): string {
    if (score >= 0.7) return 'green'
    if (score >= 0.4) return 'yellow'
    return 'red'
  }

  // ── DASHBOARD VIEW ──
  if (view === 'dashboard') {
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
            <button className="verifai-btn verifai-btn--ghost" onClick={fetchAnalyses}>Refresh</button>
            <button className="verifai-btn verifai-btn--primary" onClick={() => setView('new-analysis')}>New Analysis</button>
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
            <code className="cli-hint">
              python -m src.cli analyze --ac "User can login" --diff "def login(): pass"
            </code>
          </div>
        ) : (
          analyses.map((analysis, idx) => (
            <div key={idx} className="analysis-card clickable" onClick={() => viewDetail(analysis)}>
              <div className="analysis-header">
                <div className="pr-info">
                  <h3>{analysis.pr_title || 'Untitled PR'}</h3>
                  <p>{analysis.repo_url} · PR #{analysis.pr_number} · {analysis.timestamp ? new Date(analysis.timestamp).toLocaleDateString() : 'Just now'}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className={`stat-value ${scoreColor(analysis.overall_score)}`} style={{ fontSize: '1.5rem' }}>
                    {(analysis.overall_score * 100).toFixed(0)}%
                  </div>
                  <div className="stat-label" style={{ fontSize: '0.65rem' }}>score · click for details</div>
                </div>
              </div>

              <div className="verifai-score">
                <div className="verifai-score__fill" style={{
                  width: `${analysis.overall_score * 100}%`,
                  background: analysis.overall_score >= 0.7 ? 'var(--verifai-status-implemented)' :
                             analysis.overall_score >= 0.4 ? 'var(--verifai-status-partial)' :
                             'var(--verifai-status-missing)'
                }} />
              </div>

              <ul className="ac-list">
                {analysis.fragments.slice(0, 3).map((frag, i) => (
                  <li key={i} className="ac-item">
                    <div className={`ac-status ${frag.status}`}>{STATUS_EMOJI[frag.status]}</div>
                    <div className="ac-text">{frag.text}</div>
                    <div className="ac-conf">{(frag.confidence * 100).toFixed(0)}%</div>
                  </li>
                ))}
              </ul>

              <p className="analysis-summary">{analysis.summary}</p>
            </div>
          ))
        )}
      </div>
    )
  }

  // ── DETAIL VIEW ──
  if (view === 'detail' && selectedAnalysis) {
    const a = selectedAnalysis
    return (
      <div className="app">
        <header className="header">
          <div className="logo" style={{ cursor: 'pointer' }} onClick={backToDashboard}>
            <div className="logo-icon">←</div>
            <span>VerifAI / PR #{a.pr_number}</span>
          </div>
        </header>

        {/* PR Overview */}
        <div className="detail-card">
          <div className="detail-header">
            <div>
              <h1 className="detail-title">{a.pr_title || 'Untitled PR'}</h1>
              <p className="detail-meta">{a.repo_url} · Pull Request #{a.pr_number}</p>
            </div>
            <div className="detail-score">
              <div className={`stat-value ${scoreColor(a.overall_score)}`} style={{ fontSize: '3rem' }}>
                {(a.overall_score * 100).toFixed(0)}%
              </div>
              <div className="stat-label">Overall Score</div>
            </div>
          </div>

          <div className="verifai-score" style={{ height: '12px', margin: '1.5rem 0' }}>
            <div className="verifai-score__fill" style={{
              width: `${a.overall_score * 100}%`,
              background: a.overall_score >= 0.7 ? 'var(--verifai-status-implemented)' :
                         a.overall_score >= 0.4 ? 'var(--verifai-status-partial)' :
                         'var(--verifai-status-missing)'
            }} />
          </div>
        </div>

        {/* AC Fragments */}
        <h2 className="section-title" style={{ marginTop: '1.5rem' }}>Acceptance Criteria Analysis</h2>
        
        {a.fragments.map((frag, i) => (
          <div key={i} className="detail-fragment">
            <div className="fragment-header">
              <div className={`ac-status ${frag.status}`} style={{ width: '36px', height: '36px', fontSize: '0.875rem' }}>
                {STATUS_EMOJI[frag.status]}
              </div>
              <div className="fragment-info">
                <span className={`verifai-badge verifai-badge--${frag.status}`}>
                  {STATUS_LABEL[frag.status]}
                </span>
                <span className="fragment-conf">{(frag.confidence * 100).toFixed(0)}% confidence</span>
              </div>
            </div>
            <p className="fragment-text">{frag.text}</p>
            {frag.explanation && !frag.explanation.includes('⏳') && (
              <p className="fragment-explanation">{frag.explanation}</p>
            )}
          </div>
        ))}

        {/* Cost Info */}
        {a.llm_cost_estimate && (
          <div className="detail-card" style={{ marginTop: '1.5rem' }}>
            <div className="stat-label">Analysis Cost</div>
            <div className="stat-value" style={{ fontSize: '1rem', fontFamily: 'var(--verifai-font-mono)' }}>
              ${a.llm_cost_estimate.toFixed(5)}
            </div>
          </div>
        )}

        <button className="verifai-btn verifai-btn--primary" style={{ marginTop: '1.5rem' }} onClick={backToDashboard}>
          ← Back to Dashboard
        </button>
      </div>
    )
  }

  // ── NEW ANALYSIS VIEW ──
  if (view === 'new-analysis') {
    return <NewAnalysisView onCreated={fetchAnalyses} onBack={() => setView('dashboard')} />
  }

  return null
}

export default App
