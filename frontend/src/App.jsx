import { Suspense, lazy, useEffect, useRef, useState } from 'react'

const MriTumorView = lazy(() => import('./components/MriTumorView'))

const PIPELINE = [
  { id: '0', label: 'L0', title: 'Intake', detail: 'PDF parse & provenance map' },
  { id: '1', label: 'L1', title: 'Specialists', detail: '7 AI agents, 5 models' },
  { id: '2', label: 'L2', title: 'Validator', detail: 'PubMed + FDA evidence check' },
  { id: '3', label: 'L3', title: 'XAI Report', detail: 'Annotated PDF with sources' },
]

const THINK_STAGES = [
  { key: 'l0_1', layer: 'Layer 0', title: 'Opening PDF and indexing pages', ms: 1800 },
  { key: 'l0_2', layer: 'Layer 0', title: 'Extracting demographics, labs, vitals', ms: 2200 },
  { key: 'l0_3', layer: 'Layer 0', title: 'Building provenance map (page + span)', ms: 1800 },
  { key: 'l1_1', layer: 'Layer 1', title: 'Notes specialist — LLaMA 3.3 70B', ms: 1800 },
  { key: 'l1_2', layer: 'Layer 1', title: 'Lab specialist — Mixtral 8×7B MoE', ms: 1800 },
  { key: 'l1_3', layer: 'Layer 1', title: 'History/genetics — Gemma 2 9B', ms: 2000 },
  { key: 'l1_4', layer: 'Layer 1', title: 'Risk stratification — LLaMA 3 70B', ms: 1600 },
  { key: 'l1_5', layer: 'Layer 1', title: 'Merging 7-specialist candidate diagnoses', ms: 1400 },
  { key: 'l2_1', layer: 'Layer 2', title: 'Fetching real PubMed abstracts (NIH eUtils)', ms: 2200 },
  { key: 'l2_2', layer: 'Layer 2', title: 'Checking FDA drug safety database', ms: 1800 },
  { key: 'l2_3', layer: 'Layer 2', title: 'Validating supported / contradicted claims', ms: 2600 },
  { key: 'l3_1', layer: 'Layer 3', title: 'Generating XAI narrative with source links', ms: 2200 },
  { key: 'l3_2', layer: 'Layer 3', title: 'Annotating critical highlights in PDF', ms: 2000 },
  { key: 'l3_3', layer: 'Layer 3', title: 'Assembling final doctor report', ms: 1400 },
]

const TOTAL_STAGE_MS = THINK_STAGES.reduce((acc, s) => acc + s.ms, 0)

const AGENT_COLORS = {
  notes: '#00d4ff',
  labs: '#7c3aed',
  medication: '#f59e0b',
  history_genetics: '#00d4a0',
  exposure: '#ff4d6a',
  risk: '#a78bfa',
  imaging: '#5ee8ff',
}

export default function App() {
  const [viewMode, setViewMode] = useState('clinical')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [pdfPages, setPdfPages] = useState(1)
  const [activePage, setActivePage] = useState(1)
  const [stageIndex, setStageIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const [thinkingLog, setThinkingLog] = useState([])

  const pdfRef = useRef(null)

  const animationTickRef = useRef(null)
  const pageTickRef = useRef(null)
  const animationStartRef = useRef(0)

  useEffect(() => {
    if (!file) {
      setPreviewUrl('')
      setPdfPages(1)
      setActivePage(1)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    let cancelled = false
    estimatePdfPages(file).then((count) => {
      if (!cancelled) { setPdfPages(count); setActivePage(1) }
    })
    return () => { cancelled = true; URL.revokeObjectURL(url) }
  }, [file])

  useEffect(() => { return () => stopProcessingAnimation() }, [])

  const stopProcessingAnimation = () => {
    if (animationTickRef.current) { clearInterval(animationTickRef.current); animationTickRef.current = null }
    if (pageTickRef.current) { clearInterval(pageTickRef.current); pageTickRef.current = null }
  }

  const startProcessingAnimation = () => {
    stopProcessingAnimation()
    setProgress(2)
    setStageIndex(0)
    setThinkingLog([`[INIT] ${THINK_STAGES[0].layer}: ${THINK_STAGES[0].title}`])
    animationStartRef.current = Date.now()

    animationTickRef.current = setInterval(() => {
      const elapsed = Date.now() - animationStartRef.current
      const ratio = Math.min(elapsed / TOTAL_STAGE_MS, 0.97)
      const pct = Math.min(97, 3 + Math.floor(ratio * 94))
      setProgress(pct)

      let cumulative = 0
      let idx = THINK_STAGES.length - 1
      for (let i = 0; i < THINK_STAGES.length; i++) {
        cumulative += THINK_STAGES[i].ms
        if (elapsed <= cumulative) { idx = i; break }
      }

      setStageIndex((prev) => {
        if (idx !== prev) {
          const stage = THINK_STAGES[idx]
          setThinkingLog((logs) => [...logs.slice(-9), `[${stage.layer.replace('Layer ', 'L')}] ${stage.title}`])
        }
        return idx
      })
    }, 650)

    pageTickRef.current = setInterval(() => {
      setActivePage((prev) => (pdfPages <= 1 ? 1 : prev >= pdfPages ? 1 : prev + 1))
    }, 1700)
  }

  const upload = async () => {
    if (!file) return
    const form = new FormData()
    form.append('file', file)


    setLoading(true); setError(''); setResult(null)
    startProcessingAnimation()

    try {
      const res = await fetch('/api/diagnose', { method: 'POST', body: form })
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()
      setResult(data)
      setProgress(100)
      setStageIndex(THINK_STAGES.length - 1)
      setThinkingLog((logs) => [...logs.slice(-9), '[DONE] Report complete — ready to download'])
    } catch (e) {
      setError(e.message || 'Upload failed')
    } finally {
      setLoading(false)
      stopProcessingAnimation()
    }
  }

  const resetAll = () => {
    stopProcessingAnimation()
    setFile(null); setResult(null); setError('')
    setLoading(false); setProgress(0); setStageIndex(0); setThinkingLog([])
  }

  const reportDownloadUrl = result?.case_id ? `/api/report/${result.case_id}` : (result?.artifacts?.report_pdf || '')
  const confidence = Math.round((result?.confidence || 0) * 100)

  if (viewMode === 'mri') {
    return (
      <Suspense fallback={
        <div style={{ minHeight: '100vh', background: 'var(--bg-base)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'monospace', gap: 12 }}>
          <div className="pulse-dot" />Initializing MRI workspace...
        </div>
      }>
        <MriTumorView onBack={() => setViewMode('clinical')} />
      </Suspense>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg-base)' }}>
      {/* Sidebar */}
      <aside className="sidebar" style={{ width: 248 }}>
        <div className="sidebar-logo">
          <LogoIcon size={34} />
          <div>
            <div className="sidebar-title">MediCascade AI</div>
            <div className="sidebar-subtitle">v2.0 · Clinical Intelligence</div>
          </div>
        </div>

        <div className="sidebar-section">4-Layer Pipeline</div>
        {PIPELINE.map((p, i) => (
          <div
            key={p.id}
            style={{
              marginBottom: 6,
              border: '1px solid var(--border)',
              borderRadius: 10,
              padding: '9px 12px',
              background: 'rgba(0,212,255,0.02)',
              transition: 'border-color 0.2s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                fontFamily: 'monospace',
                fontSize: 10,
                fontWeight: 800,
                color: i === 0 ? '#8bafc9' : i === 1 ? 'var(--accent)' : i === 2 ? 'var(--purple-light)' : 'var(--success)',
                background: 'rgba(255,255,255,0.05)',
                padding: '2px 6px',
                borderRadius: 4,
                letterSpacing: '0.05em',
              }}>{p.label}</span>
              <span style={{ color: 'var(--text-primary)', fontSize: 12, fontWeight: 700 }}>{p.title}</span>
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 3, paddingLeft: 4 }}>{p.detail}</div>
          </div>
        ))}

        <div style={{ borderTop: '1px solid var(--border)', marginTop: 14, paddingTop: 14 }}>
          <div className="sidebar-section">Viewers</div>
          <div className="sidebar-item" onClick={() => setViewMode('mri')} style={{ cursor: 'pointer' }}>
            <span style={{ color: 'var(--accent)' }}>&#9672;</span>
            <span>3D Brain MRI Viewer</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '28px 34px', display: 'flex', flexDirection: 'column', gap: 18 }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
          <div>
            <h1 className="page-title" style={{ fontSize: 24, marginBottom: 4 }}>Clinical Decision Intelligence</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              Multi-model cascade · Real-time XAI · Evidence-validated diagnostics
            </p>
          </div>
          {result && (
            <div style={{ display: 'flex', gap: 8 }}>
              <span style={{ padding: '4px 12px', borderRadius: 99, background: 'var(--success-bg)', color: 'var(--success)', fontSize: 11, fontWeight: 700, border: '1px solid rgba(0,212,160,0.25)', fontFamily: 'monospace' }}>
                ● ANALYSIS COMPLETE
              </span>
            </div>
          )}
          {loading && (
            <span style={{ padding: '4px 12px', borderRadius: 99, background: 'var(--accent-dim)', color: 'var(--accent)', fontSize: 11, fontWeight: 700, border: '1px solid var(--border-strong)', fontFamily: 'monospace' }}>
              ◉ PROCESSING {progress}%
            </span>
          )}
        </div>

        {/* Upload Card */}
        <div className="glass-card" style={{ padding: 20 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 14, fontFamily: 'monospace' }}>
            ▸ Input Data
          </div>
          <div>
            {/* PDF Drop Zone */}
            <div
              onClick={() => pdfRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const f = e.dataTransfer.files?.[0]
                if (f?.type === 'application/pdf') setFile(f)
              }}
              style={{
                border: `1.5px dashed ${file ? 'var(--accent)' : 'var(--border-strong)'}`,
                borderRadius: 12,
                padding: '20px 22px',
                cursor: 'pointer',
                background: file ? 'rgba(0,212,255,0.05)' : 'rgba(0,212,255,0.02)',
                transition: 'all 0.2s',
                boxShadow: file ? '0 0 20px rgba(0,212,255,0.08)' : 'none',
              }}
            >
              <input ref={pdfRef} type="file" accept="application/pdf" style={{ display: 'none' }} onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <div style={{ fontSize: 24, marginBottom: 8 }}>{file ? '📄' : '⬆'}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', fontFamily: 'monospace' }}>Patient Document (PDF)</div>
              <div style={{ color: file ? 'var(--accent)' : 'var(--text-primary)', marginTop: 6, fontWeight: 700, fontSize: 15 }}>
                {file ? file.name : 'Click or drag & drop hospital record'}
              </div>
              {file && (
                <div style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 11, fontFamily: 'monospace' }}>
                  {pdfPages} page{pdfPages !== 1 ? 's' : ''} detected · {(file.size / 1024).toFixed(0)} KB
                </div>
              )}
            </div>

          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {loading ? (
                <>
                  <div className="pulse-dot" />
                  <span style={{ color: 'var(--accent)', fontSize: 13, fontFamily: 'monospace' }}>Running cascade... {progress}%</span>
                </>
              ) : (
                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {file ? '● Ready to analyze' : '○ Awaiting input'}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-secondary" onClick={resetAll}>Reset</button>
              <button className="btn-primary" disabled={!file || loading} onClick={upload}>
                {loading ? '◉ Running...' : '▶ Generate Report'}
              </button>
            </div>
          </div>
        </div>

        {/* Loading / Live AI Transparency */}
        {loading && (
          <div className="glass-card fade-in" style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div className="pulse-dot" />
              <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 14 }}>Live AI Transparency</span>
              <span style={{ color: 'var(--text-muted)', fontSize: 12, fontFamily: 'monospace', marginLeft: 'auto' }}>{progress}% complete</span>
            </div>

            {/* Progress bar */}
            <div className="progress-track" style={{ marginBottom: 16 }}>
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 14 }}>
              {/* Stage list */}
              <div style={{ border: '1px solid var(--border)', borderRadius: 10, padding: 12, maxHeight: 380, overflowY: 'auto' }}>
                {THINK_STAGES.map((stage, idx) => {
                  const done = idx < stageIndex
                  const active = idx === stageIndex
                  return (
                    <div key={stage.key} style={{ display: 'flex', gap: 10, marginBottom: 8, opacity: done || active ? 1 : 0.35, transition: 'opacity 0.3s' }}>
                      <div style={{
                        width: 10, height: 10, marginTop: 4, borderRadius: '50%', flexShrink: 0,
                        background: done ? 'var(--success)' : active ? 'var(--accent)' : 'var(--text-muted)',
                        boxShadow: active ? '0 0 10px rgba(0,212,255,0.7)' : done ? '0 0 6px rgba(0,212,160,0.5)' : 'none',
                      }} />
                      <div>
                        <span style={{
                          fontSize: 10, fontWeight: 700, fontFamily: 'monospace',
                          color: done ? 'var(--success)' : active ? 'var(--accent)' : 'var(--text-muted)',
                          marginRight: 6,
                        }}>{stage.layer.replace('Layer ', 'L')}</span>
                        <span style={{ color: done || active ? 'var(--text-primary)' : 'var(--text-muted)', fontSize: 12 }}>{stage.title}</span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* PDF preview */}
              <div style={{ border: '1px solid var(--border)', borderRadius: 10, padding: 12 }}>
                <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8, fontFamily: 'monospace' }}>
                  AI Focus Window — Page {activePage}/{pdfPages}
                </div>
                {previewUrl ? (
                  <embed
                    key={`${previewUrl}-${activePage}`}
                    src={`${previewUrl}#page=${activePage}&toolbar=0&navpanes=0&scrollbar=0`}
                    type="application/pdf"
                    style={{ width: '100%', height: 270, borderRadius: 8, border: '1px solid var(--border)' }}
                  />
                ) : (
                  <div className="warning-box">PDF preview appears after file upload.</div>
                )}
                <div style={{ marginTop: 10, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6, fontFamily: 'monospace' }}>Live Log</div>
                  {thinkingLog.slice(-5).map((line, i) => (
                    <div key={i} style={{ color: i === thinkingLog.slice(-5).length - 1 ? 'var(--accent)' : 'var(--text-muted)', fontSize: 11, marginBottom: 3, fontFamily: 'monospace' }}>
                      {line}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {error && <div className="error-box">{error}</div>}

        {/* Results */}
        {result && !loading && (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Key metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: 12 }}>
              {[
                { label: 'Case ID', value: result.case_id, mono: true },
                { label: 'Primary Diagnosis', value: result.primary_diagnosis || 'Undetermined', accent: true },
                { label: 'Confidence', value: `${confidence}%`, color: confidence >= 75 ? 'var(--success)' : confidence >= 50 ? 'var(--warning)' : 'var(--danger)' },
                { label: 'Processing Time', value: `${(result.processing_time || result.total_processing_time || 0).toFixed(1)}s`, mono: true },
                { label: 'Evidence Items', value: result.evidence_items_count || result.evidence_count || 0 },
                { label: 'Specialist Views', value: result.specialist_views_count || (result.layer1_views || []).length },
              ].map((m) => (
                <div key={m.label} className="stat-card" style={{ padding: '14px 16px', textAlign: 'left' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', fontFamily: 'monospace', marginBottom: 6 }}>{m.label}</div>
                  <div style={{
                    color: m.color || (m.accent ? 'var(--accent)' : 'var(--text-primary)'),
                    fontWeight: 800,
                    fontSize: m.mono ? 14 : 18,
                    fontFamily: m.mono ? 'monospace' : 'inherit',
                    wordBreak: 'break-word',
                  }}>
                    {String(m.value)}
                  </div>
                  {m.label === 'Confidence' && (
                    <div style={{ marginTop: 8 }}>
                      <div className="confidence-bar-track">
                        <div className="confidence-bar-fill" style={{
                          width: `${confidence}%`,
                          background: confidence >= 75 ? 'linear-gradient(90deg, var(--success), #00f5c0)' : confidence >= 50 ? 'linear-gradient(90deg, var(--warning), #fcd34d)' : 'linear-gradient(90deg, var(--danger), #ff8096)',
                        }} />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* ICD-10 + drug safety row */}
            {(result.icd10_code || result.drug_safety?.warnings?.length) && (
              <div style={{ display: 'grid', gridTemplateColumns: result.icd10_code && result.drug_safety?.warnings?.length ? '1fr 1fr' : '1fr', gap: 12 }}>
                {result.icd10_code && (
                  <div style={{ border: '1px solid rgba(0,212,255,0.2)', borderRadius: 12, padding: '12px 16px', background: 'rgba(0,212,255,0.04)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', fontFamily: 'monospace', marginBottom: 6 }}>ICD-10-CM Code</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 18, fontFamily: 'monospace' }}>{result.icd10_code}</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{result.icd10_description}</span>
                    </div>
                  </div>
                )}
                {result.drug_safety?.warnings?.length > 0 && (
                  <div style={{ border: '1px solid rgba(255,77,106,0.2)', borderRadius: 12, padding: '12px 16px', background: 'rgba(255,77,106,0.04)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', fontFamily: 'monospace', marginBottom: 6 }}>FDA Drug Warnings</div>
                    {result.drug_safety.warnings.slice(0, 2).map((w, i) => (
                      <div key={i} style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 3 }}>⚠ {typeof w === 'string' ? w : `${w.drug}: ${w.detail}`}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Specialist views */}
            <div className="glass-card" style={{ padding: 16 }}>
              <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'monospace', marginBottom: 12 }}>▸ Layer 1 — Specialist AI Views</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 10 }}>
                {(result.layer1_views || []).map((v) => {
                  const conf = Math.round((v.confidence || 0) * 100)
                  const accentColor = AGENT_COLORS[v.agent] || 'var(--accent)'
                  return (
                    <div
                      key={v.agent}
                      style={{
                        border: `1px solid ${accentColor}25`,
                        borderLeft: `3px solid ${accentColor}`,
                        borderRadius: 10,
                        padding: 12,
                        background: `${accentColor}08`,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 12 }}>{v.role || v.agent}</div>
                        <div style={{ color: accentColor, fontSize: 12, fontWeight: 800, fontFamily: 'monospace' }}>{conf}%</div>
                      </div>
                      <div style={{ height: 3, borderRadius: 99, background: 'rgba(255,255,255,0.06)', marginBottom: 8, overflow: 'hidden' }}>
                        <div style={{ width: `${conf}%`, height: '100%', background: accentColor, borderRadius: 99, transition: 'width 0.8s ease', boxShadow: `0 0 6px ${accentColor}80` }} />
                      </div>
                      {summarizeFindings(v.findings).map((line, idx) => (
                        <div key={idx} style={{ color: 'var(--text-secondary)', fontSize: 11, marginBottom: 3, lineHeight: 1.4 }}>{line}</div>
                      ))}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Data flow trace */}
            {(result.data_flow_trace || []).length > 0 && (
              <div className="glass-card" style={{ padding: 16 }}>
                <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'monospace', marginBottom: 12 }}>▸ Data Flow Trace</div>
                {(result.data_flow_trace || []).map((step, idx) => (
                  <div key={idx} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 10, marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{
                        fontFamily: 'monospace', fontSize: 10, fontWeight: 800, padding: '2px 7px', borderRadius: 4,
                        background: step.layer?.includes('0') ? 'rgba(139,175,201,0.1)' : step.layer?.includes('1') ? 'var(--accent-dim)' : step.layer?.includes('2') ? 'var(--purple-dim)' : 'var(--success-bg)',
                        color: step.layer?.includes('0') ? 'var(--text-secondary)' : step.layer?.includes('1') ? 'var(--accent)' : step.layer?.includes('2') ? 'var(--purple-light)' : 'var(--success)',
                      }}>{step.layer}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: 11, fontFamily: 'monospace' }}>{step.status}</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}><span style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: 10 }}>IN → </span>{step.input}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}><span style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: 10 }}>OUT → </span>{step.output}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Download report */}
            <div className="glass-card" style={{ padding: 20, border: '1px solid var(--border-strong)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'monospace', marginBottom: 6 }}>▸ Final Report</div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 16 }}>Annotated Doctor Report — PDF</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
                    XAI explanations · Evidence links · ICD-10 coding · Critical highlights
                  </div>
                </div>
                {reportDownloadUrl ? (
                  <a className="btn-primary" href={reportDownloadUrl} target="_blank" rel="noreferrer" style={{ fontSize: 14 }}>
                    ↓ Download PDF Report
                  </a>
                ) : (
                  <div className="warning-box" style={{ margin: 0 }}>PDF not yet available.</div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

/* ── Sub-components ──────────────────────────────────────── */

function LogoIcon({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="lg1" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#00d4ff" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      <rect width="36" height="36" rx="10" fill="url(#lg1)" />
      <path d="M8 18 L14 10 L18 14 L22 8 L28 18" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx="18" cy="24" r="4" stroke="white" strokeWidth="1.8" fill="none" />
      <circle cx="18" cy="24" r="1.5" fill="white" opacity="0.9" />
    </svg>
  )
}

function stringify(v) {
  if (typeof v === 'string') return v
  if (v && typeof v === 'object') return v.detail || v.name || v.drug || JSON.stringify(v)
  return String(v)
}

function summarizeFindings(findings) {
  if (!findings || typeof findings !== 'object') return ['No specialist detail available']
  const items = []
  if (findings.primary_suspect) items.push(`Suspect: ${stringify(findings.primary_suspect)}`)
  if (Array.isArray(findings.patterns) && findings.patterns.length) items.push(`Patterns: ${findings.patterns.slice(0, 2).map(stringify).join('; ')}`)
  if (Array.isArray(findings.red_flags) && findings.red_flags.length) items.push(`Flags: ${findings.red_flags.slice(0, 2).map(stringify).join('; ')}`)
  if (Array.isArray(findings.risk_flags) && findings.risk_flags.length) items.push(`Risk: ${findings.risk_flags.slice(0, 2).map(stringify).join('; ')}`)
  if (Array.isArray(findings.interactions) && findings.interactions.length) items.push(`Interactions: ${findings.interactions.slice(0, 2).map(stringify).join('; ')}`)
  if (Array.isArray(findings.comorbidities) && findings.comorbidities.length) items.push(`Comorbidities: ${findings.comorbidities.slice(0, 2).map(stringify).join('; ')}`)
  if (findings.diagnosis) items.push(`Imaging: ${stringify(findings.diagnosis)}`)
  return items.length ? items.slice(0, 4) : ['Detail in final report']
}

async function estimatePdfPages(file) {
  try {
    const buffer = await file.arrayBuffer()
    const slice = buffer.byteLength > 8_000_000 ? buffer.slice(0, 8_000_000) : buffer
    const text = new TextDecoder('latin1').decode(slice)
    const matches = text.match(/\/Type\s*\/Page\b/g)
    return Math.max(1, Math.min(400, matches ? matches.length : 1))
  } catch {
    return 1
  }
}
