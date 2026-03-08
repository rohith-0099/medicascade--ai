import { Suspense, lazy, useEffect, useRef, useState } from 'react'

const MriTumorView = lazy(() => import('./components/MriTumorView'))
const Brain3DViewer = lazy(() => import('./components/Brain3DViewer'))

const PIPELINE = [
  { id: '0', title: 'Layer 0', detail: 'Intake and structure facts with provenance' },
  { id: '1', title: 'Layer 1', detail: 'Specialists produce candidate findings' },
  { id: '2', title: 'Layer 2', detail: 'Validator confirms against trusted evidence' },
  { id: '3', title: 'Layer 3', detail: 'Doctor report PDF with XAI and highlights' },
]

const THINK_STAGES = [
  { key: 'l0_1', layer: 'Layer 0', title: 'Opening PDF and indexing pages', ms: 1800 },
  { key: 'l0_2', layer: 'Layer 0', title: 'Extracting demographics, labs, vitals', ms: 2200 },
  { key: 'l0_3', layer: 'Layer 0', title: 'Building provenance map (page + span)', ms: 1800 },
  { key: 'l1_1', layer: 'Layer 1', title: 'Notes specialist reasoning', ms: 1800 },
  { key: 'l1_2', layer: 'Layer 1', title: 'Lab specialist pattern detection', ms: 1800 },
  { key: 'l1_3', layer: 'Layer 1', title: 'Medication/history/exposure specialists', ms: 2200 },
  { key: 'l1_4', layer: 'Layer 1', title: 'Merging specialist candidate diagnoses', ms: 1600 },
  { key: 'l2_1', layer: 'Layer 2', title: 'Retrieving PubMed / NICE / WHO evidence', ms: 2200 },
  { key: 'l2_2', layer: 'Layer 2', title: 'Validating supported/uncertain/contradicted claims', ms: 2600 },
  { key: 'l3_1', layer: 'Layer 3', title: 'Generating Groq-powered XAI narrative', ms: 2200 },
  { key: 'l3_2', layer: 'Layer 3', title: 'Annotating critical highlights in PDF', ms: 2000 },
  { key: 'l3_3', layer: 'Layer 3', title: 'Assembling final doctor report', ms: 1400 },
]

const TOTAL_STAGE_MS = THINK_STAGES.reduce((acc, s) => acc + s.ms, 0)

export default function App() {
  const [viewMode, setViewMode] = useState('clinical')
  const [file, setFile] = useState(null)
  const [scan, setScan] = useState(null)
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
  const scanRef = useRef(null)
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
      if (!cancelled) {
        setPdfPages(count)
        setActivePage(1)
      }
    })

    return () => {
      cancelled = true
      URL.revokeObjectURL(url)
    }
  }, [file])

  useEffect(() => {
    return () => {
      stopProcessingAnimation()
    }
  }, [])

  const stopProcessingAnimation = () => {
    if (animationTickRef.current) {
      clearInterval(animationTickRef.current)
      animationTickRef.current = null
    }
    if (pageTickRef.current) {
      clearInterval(pageTickRef.current)
      pageTickRef.current = null
    }
  }

  const startProcessingAnimation = () => {
    stopProcessingAnimation()
    setProgress(2)
    setStageIndex(0)
    setThinkingLog([`Started: ${THINK_STAGES[0].layer} - ${THINK_STAGES[0].title}`])
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
        if (elapsed <= cumulative) {
          idx = i
          break
        }
      }

      setStageIndex((prev) => {
        if (idx !== prev) {
          const stage = THINK_STAGES[idx]
          setThinkingLog((logs) => [...logs.slice(-9), `${stage.layer}: ${stage.title}`])
        }
        return idx
      })
    }, 650)

    pageTickRef.current = setInterval(() => {
      setActivePage((prev) => {
        if (pdfPages <= 1) return 1
        return prev >= pdfPages ? 1 : prev + 1
      })
    }, 1700)
  }

  const upload = async () => {
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    if (scan) form.append('scan', scan)

    setLoading(true)
    setError('')
    setResult(null)
    startProcessingAnimation()

    try {
      const res = await fetch('/api/diagnose', { method: 'POST', body: form })
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()
      setResult(data)
      setProgress(100)
      setStageIndex(THINK_STAGES.length - 1)
      setThinkingLog((logs) => [...logs.slice(-9), 'Layer 3: Report complete and ready to download'])
    } catch (e) {
      setError(e.message || 'Upload failed')
    } finally {
      setLoading(false)
      stopProcessingAnimation()
    }
  }

  const resetAll = () => {
    stopProcessingAnimation()
    setFile(null)
    setScan(null)
    setResult(null)
    setError('')
    setLoading(false)
    setProgress(0)
    setStageIndex(0)
    setThinkingLog([])
  }

  const ResultValue = ({ label, value }) => (
    <div className="glass-card" style={{ padding: 14, border: '1px solid var(--border)' }}>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
      <div style={{ color: 'var(--text-primary)', marginTop: 4, fontWeight: 700, fontSize: 20 }}>{value}</div>
    </div>
  )

  const summarizeFindings = (findings) => {
    if (!findings || typeof findings !== 'object') return ['No specialist detail available']
    const items = []
    if (findings.primary_suspect) items.push(`Primary suspect: ${findings.primary_suspect}`)
    if (Array.isArray(findings.patterns) && findings.patterns.length) items.push(`Patterns: ${findings.patterns.slice(0, 2).join('; ')}`)
    if (Array.isArray(findings.red_flags) && findings.red_flags.length) items.push(`Red flags: ${findings.red_flags.slice(0, 2).join('; ')}`)
    if (Array.isArray(findings.risk_flags) && findings.risk_flags.length) items.push(`Risk flags: ${findings.risk_flags.slice(0, 2).join('; ')}`)
    if (Array.isArray(findings.interactions) && findings.interactions.length) items.push(`Interactions: ${findings.interactions.slice(0, 2).join('; ')}`)
    if (Array.isArray(findings.comorbidities) && findings.comorbidities.length) items.push(`Comorbidities: ${findings.comorbidities.slice(0, 2).join('; ')}`)
    if (Array.isArray(findings.consider) && findings.consider.length) items.push(`Exposure considerations: ${findings.consider.slice(0, 2).join('; ')}`)
    if (findings.diagnosis) items.push(`Imaging diagnosis: ${findings.diagnosis}`)
    return items.length ? items.slice(0, 4) : ['Summary available in final PDF report']
  }

  const reportDownloadUrl = result?.case_id ? `/api/report/${result.case_id}` : (result?.artifacts?.report_pdf || '')

  if (viewMode === 'mri') {
    return (
      <Suspense fallback={<div style={{ minHeight: '100vh', background: 'var(--bg-base)', color: 'var(--text-secondary)', padding: 24 }}>Loading MRI workspace...</div>}>
        <MriTumorView onBack={() => setViewMode('clinical')} />
      </Suspense>
    )
  }

  if (viewMode === '3d-brain') {
    return (
      <Suspense fallback={<div style={{ minHeight: '100vh', background: '#0a0e27', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading 3D Brain Viewer...</div>}>
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <div style={{ background: 'rgba(15, 20, 45, 0.95)', padding: '12px 20px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ color: 'white', margin: 0, fontSize: '18px' }}>3D Brain Tumor Viewer</h2>
            <button onClick={() => setViewMode('clinical')} style={{ padding: '8px 16px', background: '#4a90e2', border: 'none', borderRadius: '5px', color: 'white', cursor: 'pointer' }}>Back to Clinical</button>
          </div>
          <Brain3DViewer />
        </div>
      </Suspense>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg-base)' }}>
      <aside className="sidebar" style={{ width: 250 }}>
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <span style={{ color: '#041006', fontWeight: 800 }}>MC</span>
          </div>
          <div>
            <div className="sidebar-title">MediCascade</div>
            <div className="sidebar-subtitle">Doctor-first workflow</div>
          </div>
        </div>
        <div className="sidebar-section">Data Flow</div>
        {PIPELINE.map((p) => (
          <div key={p.id} style={{ marginBottom: 8, border: '1px solid var(--border)', borderRadius: 10, padding: 10 }}>
            <div style={{ color: 'var(--accent-light)', fontSize: 13, fontWeight: 700 }}>{p.title}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{p.detail}</div>
          </div>
        ))}
      </aside>

      <main style={{ flex: 1, padding: '28px 34px', display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div className="page-header">
          <h1 className="page-title" style={{ marginBottom: 6 }}>Clinical Decision Report</h1>
          <p className="page-description">
            Watch the live AI processing path from Layer 0 to Layer 3 while your PDF is being analyzed.
          </p>
          <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
            <button className="btn-secondary" onClick={() => setViewMode('mri')} style={{}}>
              Open Brain MRI Modality View
            </button>
            <button className="btn-secondary" onClick={() => setViewMode('3d-brain')} style={{}}>
              Open 3D Brain Tumor Viewer
            </button>
          </div>
        </div>

        <div className="glass-card" style={{ padding: 20, border: '1px solid var(--border-strong)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
            <div
              onClick={() => pdfRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const f = e.dataTransfer.files?.[0]
                if (f?.type === 'application/pdf') setFile(f)
              }}
              style={{
                border: `1.5px dashed ${file ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 12,
                padding: 20,
                cursor: 'pointer',
                background: 'linear-gradient(120deg, var(--accent-dim), transparent)',
              }}
            >
              <input ref={pdfRef} type="file" accept="application/pdf" style={{ display: 'none' }} onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <div style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Patient document</div>
              <div style={{ color: 'var(--text-primary)', marginTop: 8, fontWeight: 700, fontSize: 18 }}>
                {file ? file.name : 'Click or drop hospital PDF'}
              </div>
              {file && <div style={{ color: 'var(--text-secondary)', marginTop: 8, fontSize: 12 }}>Detected pages (estimate): {pdfPages}</div>}
            </div>

            <div style={{ border: '1px solid var(--border)', borderRadius: 12, padding: 14, background: 'var(--bg-hover)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Optional imaging</div>
              <input ref={scanRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={(e) => setScan(e.target.files?.[0] || null)} />
              <button className="btn-secondary" onClick={() => scanRef.current?.click()} style={{ width: '100%', marginTop: 10 }}>
                {scan ? scan.name : 'Attach scan image'}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 14 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{loading ? `Processing... ${progress}%` : 'Ready'}</div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-secondary" onClick={resetAll}>Reset</button>
              <button className="btn-primary" disabled={!file || loading} onClick={upload}>{loading ? 'Running' : 'Generate Report'}</button>
            </div>
          </div>
        </div>

        {loading && (
          <div className="glass-card" style={{ border: '1px solid var(--border)', padding: 16 }}>
            <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: 10 }}>Live AI Transparency View</div>
            <div style={{ height: 8, borderRadius: 999, background: 'rgba(148,163,184,0.18)', overflow: 'hidden', marginBottom: 14 }}>
              <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent), var(--accent-light))', transition: 'width 0.4s ease' }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 14 }}>
              <div style={{ border: '1px solid var(--border)', borderRadius: 10, padding: 12 }}>
                {THINK_STAGES.map((stage, idx) => {
                  const done = idx < stageIndex
                  const active = idx === stageIndex
                  return (
                    <div key={stage.key} style={{ display: 'flex', gap: 10, marginBottom: 9, opacity: done || active ? 1 : 0.45 }}>
                      <div
                        style={{
                          width: 11,
                          height: 11,
                          marginTop: 4,
                          borderRadius: '50%',
                          background: done ? 'var(--success)' : (active ? 'var(--accent)' : 'var(--text-muted)'),
                          boxShadow: active ? '0 0 12px rgba(59,130,246,0.7)' : 'none',
                        }}
                      />
                      <div>
                        <div style={{ color: done || active ? 'var(--text-primary)' : 'var(--text-muted)', fontSize: 12, fontWeight: 700 }}>
                          {stage.layer}
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{stage.title}</div>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div style={{ border: '1px solid var(--border)', borderRadius: 10, padding: 12 }}>
                <div style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>
                  PDF Focus Window
                </div>
                {previewUrl ? (
                  <div>
                    <div style={{ color: 'var(--accent-light)', fontSize: 12, marginBottom: 8 }}>
                      AI focus page: {activePage} / {pdfPages}
                    </div>
                    <embed
                      key={`${previewUrl}-${activePage}`}
                      src={`${previewUrl}#page=${activePage}&toolbar=0&navpanes=0&scrollbar=0`}
                      type="application/pdf"
                      style={{ width: '100%', height: 330, borderRadius: 8, border: '1px solid var(--border)' }}
                    />
                  </div>
                ) : (
                  <div className="warning-box">PDF preview will appear once a file is uploaded.</div>
                )}

                <div style={{ marginTop: 10, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 6 }}>Live reasoning log</div>
                  {thinkingLog.slice(-5).map((line, i) => (
                    <div key={i} style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>
                      {line}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {error && <div className="error-box">{error}</div>}

        {result && !loading && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: 12 }}>
              <ResultValue label="Case ID" value={result.case_id} />
              <ResultValue label="Primary Diagnosis" value={result.primary_diagnosis || 'Undetermined'} />
              <ResultValue label="Confidence" value={`${Math.round((result.confidence || 0) * 100)}%`} />
              <ResultValue label="Processing Time" value={`${(result.processing_time || result.total_processing_time || 0).toFixed(1)}s`} />
              <ResultValue label="Evidence Items" value={result.evidence_items_count || result.evidence_count || 0} />
              <ResultValue label="Specialist Views" value={result.specialist_views_count || (result.layer1_views || []).length} />
            </div>

            <div className="glass-card" style={{ padding: 16, border: '1px solid var(--border)' }}>
              <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: 8 }}>Layer 1 Specialist Views</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(250px,1fr))', gap: 10 }}>
                {(result.layer1_views || []).map((v) => (
                  <div key={v.agent} style={{ border: '1px solid var(--border)', borderRadius: 10, padding: 12, background: 'rgba(57,255,20,0.03)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 13 }}>{v.role || v.agent}</div>
                      <div style={{ color: 'var(--accent-light)', fontSize: 12, fontWeight: 700 }}>{Math.round((v.confidence || 0) * 100)}%</div>
                    </div>
                    {summarizeFindings(v.findings).map((line, idx) => (
                      <div key={idx} style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>{line}</div>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card" style={{ padding: 16, border: '1px solid var(--border)' }}>
              <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: 8 }}>Data Flow Transparency</div>
              {(result.data_flow_trace || []).map((step, idx) => (
                <div key={idx} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 10, marginBottom: 8 }}>
                  <div style={{ color: 'var(--accent-light)', fontWeight: 700, fontSize: 12 }}>{step.layer} ({step.status})</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 3 }}>Input: {step.input}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>Output: {step.output}</div>
                </div>
              ))}
            </div>

            <div className="glass-card" style={{ padding: 16, border: '1px solid var(--border)' }}>
              <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: 8 }}>Doctor Report</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 10 }}>
                Download the complete annotated report with detailed XAI explanation, evidence links, and highlighted critical values.
              </div>
              {reportDownloadUrl ? (
                <a className="btn-primary" href={reportDownloadUrl} target="_blank" rel="noreferrer">
                  Download Annotated PDF
                </a>
              ) : (
                <div className="warning-box">PDF report not available yet.</div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

async function estimatePdfPages(file) {
  try {
    const buffer = await file.arrayBuffer()
    // A lightweight page count estimate based on PDF object markers.
    const slice = buffer.byteLength > 8_000_000 ? buffer.slice(0, 8_000_000) : buffer
    const text = new TextDecoder('latin1').decode(slice)
    const matches = text.match(/\/Type\s*\/Page\b/g)
    const count = matches ? matches.length : 1
    return Math.max(1, Math.min(400, count))
  } catch {
    return 1
  }
}
