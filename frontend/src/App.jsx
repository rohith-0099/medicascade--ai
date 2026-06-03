import { useEffect, useRef, useState } from 'react'

const PIPELINE = [
  { id: '0', label: 'L0', title: 'Intake', detail: 'PDF parse & provenance map' },
  { id: '1', label: 'L1', title: 'Specialists', detail: '7 AI agents, 5 models' },
  { id: '2', label: 'L2', title: 'Validator', detail: 'PubMed + FDA evidence check' },
  { id: '3', label: 'L3', title: 'XAI Report', detail: 'Annotated PDF with sources' },
]

const THINK_STAGES = [
  { key: 'l0_1', layer: 'Layer 0', title: 'Reading patient document and indexing pages', ms: 1800 },
  { key: 'l0_2', layer: 'Layer 0', title: 'Extracting demographics, labs, vitals, medications', ms: 2200 },
  { key: 'l0_3', layer: 'Layer 0', title: 'Mapping every value back to its source page', ms: 1800 },
  { key: 'l1_1', layer: 'Layer 1', title: 'Analysing clinical notes and presenting symptoms', ms: 1800 },
  { key: 'l1_2', layer: 'Layer 1', title: 'Interpreting laboratory results', ms: 1800 },
  { key: 'l1_3', layer: 'Layer 1', title: 'Reviewing history and genetic risk factors', ms: 2000 },
  { key: 'l1_4', layer: 'Layer 1', title: 'Screening medications for safety concerns', ms: 1600 },
  { key: 'l1_5', layer: 'Layer 1', title: 'Consolidating candidate diagnoses', ms: 1400 },
  { key: 'l2_1', layer: 'Layer 2', title: 'Retrieving supporting PubMed literature', ms: 2200 },
  { key: 'l2_2', layer: 'Layer 2', title: 'Cross-checking the FDA drug safety database', ms: 1800 },
  { key: 'l2_3', layer: 'Layer 2', title: 'Validating supported vs. contradicted findings', ms: 2600 },
  { key: 'l3_1', layer: 'Layer 3', title: 'Composing the explainable narrative with citations', ms: 2200 },
  { key: 'l3_2', layer: 'Layer 3', title: 'Highlighting critical values for review', ms: 2000 },
  { key: 'l3_3', layer: 'Layer 3', title: 'Finalising the annotated clinician report', ms: 1400 },
]

const TOTAL_STAGE_MS = THINK_STAGES.reduce((acc, s) => acc + s.ms, 0)

// Curated editorial palette — muted, cohesive, no neon
const AGENT_COLORS = {
  notes: '#c8341f',
  labs: '#25624a',
  medication: '#9a6411',
  history_genetics: '#2f4d72',
  exposure: '#7a3b6b',
  risk: '#8c5a2b',
  imaging: '#2b6b6b',
}

export default function App() {
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
      if (!res.ok) {
        let msg = `API error ${res.status}`
        try {
          const errData = await res.json()
          if (errData.detail) msg = errData.detail
        } catch (_) {}
        throw new Error(msg)
      }
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
  const confColor = confidence >= 75 ? 'var(--ok)' : confidence >= 50 ? 'var(--warn)' : 'var(--crit)'

  return (
    <div className="app-shell">
      {/* Instrument rail */}
      <aside className="rail">
        <div className="rail-mark">
          <LogoIcon size={38} />
          <div>
            <div className="rail-word">Medi<em>Cascade</em></div>
            <div className="rail-tag">Clinical Intelligence · v2.0</div>
          </div>
        </div>

        <hr className="rail-rule" />

        <div className="rail-eyebrow"><span>Cascade Pipeline</span><span>04</span></div>

        {PIPELINE.map((p, i) => {
          let isActive = false
          let isPast = false
          if (loading) {
            if (i === 0 && stageIndex < 3) isActive = true
            else if (i === 1 && stageIndex >= 3 && stageIndex < 8) isActive = true
            else if (i === 2 && stageIndex >= 8 && stageIndex < 11) isActive = true
            else if (i === 3 && stageIndex >= 11) isActive = true

            if (i === 0 && stageIndex >= 3) isPast = true
            if (i === 1 && stageIndex >= 8) isPast = true
            if (i === 2 && stageIndex >= 11) isPast = true
          } else if (result) {
            isPast = true
          } else if (i === 0) {
            isActive = true
          }

          const cls = `stage${isActive ? ' is-active' : ''}${isPast ? ' is-past' : ''}`
          return (
            <div key={p.id} className={cls}>
              <div className="stage-num">{isPast && !isActive ? '✓' : i + 1}</div>
              <div className="stage-title">{p.title}</div>
              <div className="stage-detail">{p.detail}</div>
            </div>
          )
        })}

        <hr className="rail-rule thin" />
        <div className="rail-foot">
          XAI · EVIDENCE-LED<br />
          PubMed eUtils · OpenFDA<br />
          ICD-10-CM · FHIR R4
        </div>
      </aside>

      {/* Canvas */}
      <main className="canvas">

        {/* Masthead */}
        <header className="masthead fade-up d1">
          <div>
            <div className="kicker">Decision Support Engine</div>
            <h1 className="display-xl">Clinical <em>Cascade</em></h1>
            <div className="masthead-meta">4-layer pipeline / explainable / evidence-validated</div>
          </div>
          {result && !loading && <span className="pill pill-done">● Analysis Complete</span>}
          {loading && <span className="pill pill-live">◉ Processing {progress}%</span>}
        </header>

        {/* Upload sheet */}
        <section className="sheet fade-up d2" style={{ marginTop: 24 }}>
          <div className="sheet-eyebrow">Input Specimen</div>

          <div
            className={`drop ${file ? 'has-file' : ''}`}
            onClick={() => pdfRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('drag-over') }}
            onDragLeave={(e) => { e.currentTarget.classList.remove('drag-over') }}
            onDrop={(e) => {
              e.preventDefault()
              e.currentTarget.classList.remove('drag-over')
              const f = e.dataTransfer.files?.[0]
              if (f?.type === 'application/pdf') setFile(f)
            }}
          >
            <input ref={pdfRef} type="file" accept="application/pdf" style={{ display: 'none' }} onChange={(e) => setFile(e.target.files?.[0] || null)} />

            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 14 }}>
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke={file ? 'var(--ok)' : 'var(--ink-faint)'} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>

            {!file ? (
              <>
                <div className="drop-lead">Drop the patient PDF here</div>
                <div className="drop-sub">text-based or scanned · OCR-ready</div>
              </>
            ) : (
              <>
                <div className="drop-lead" style={{ color: 'var(--ok)' }}>{file.name}</div>
                <div className="drop-sub">{pdfPages} page{pdfPages !== 1 ? 's' : ''} detected · {(file.size / 1024).toFixed(0)} KB</div>
              </>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 20, gap: 12, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
              {loading ? (
                <>
                  <div className="dot" />
                  <span className="mono" style={{ color: 'var(--accent)', fontSize: 12 }}>Running cascade… {progress}%</span>
                </>
              ) : (
                <span className="mono" style={{ color: 'var(--ink-faint)', fontSize: 12 }}>
                  {file ? '● Ready to analyze' : '○ Awaiting input'}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost" onClick={resetAll}>Reset</button>
              <button className="btn btn-key" disabled={!file || loading} onClick={upload}>
                {loading ? '◉ Running' : '▶ Generate Report'}
              </button>
            </div>
          </div>
        </section>

        {/* Processing transparency */}
        {loading && (
          <section className="sheet fade-up" style={{ marginTop: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <div className="dot" />
              <span style={{ fontFamily: 'var(--display)', fontWeight: 600, fontSize: 18 }}>Live AI Transparency</span>
              <span className="mono" style={{ color: 'var(--ink-faint)', fontSize: 12, marginLeft: 'auto' }}>{progress}% complete</span>
            </div>

            <div className="track" style={{ marginBottom: 18 }}>
              <span style={{ width: `${progress}%` }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 16 }}>
              {/* Stage list */}
              <div style={{ border: '1px solid var(--rule)', borderRadius: 3, padding: 14, maxHeight: 380, overflowY: 'auto' }}>
                {THINK_STAGES.map((stage, idx) => {
                  const done = idx < stageIndex
                  const active = idx === stageIndex
                  return (
                    <div key={stage.key} style={{ display: 'flex', gap: 11, marginBottom: 9, opacity: done || active ? 1 : 0.4, transition: 'opacity .3s' }}>
                      <div style={{
                        width: 9, height: 9, marginTop: 5, borderRadius: '50%', flexShrink: 0,
                        background: done ? 'var(--ok)' : active ? 'var(--accent)' : 'var(--rule-strong)',
                        boxShadow: active ? '0 0 0 3px var(--accent-wash)' : 'none',
                      }} />
                      <div>
                        <span className="mono" style={{ fontSize: 10, fontWeight: 700, marginRight: 7, color: done ? 'var(--ok)' : active ? 'var(--accent)' : 'var(--ink-faint)' }}>
                          {stage.layer.replace('Layer ', 'L')}
                        </span>
                        <span style={{ fontSize: 13.5, color: done || active ? 'var(--ink)' : 'var(--ink-faint)' }}>{stage.title}</span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* PDF focus + tape */}
              <div className="focus-frame" style={{ padding: 14 }}>
                <div className="mono" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.16em', color: 'var(--ink-faint)', marginBottom: 9 }}>
                  AI Focus Window — Page {activePage}/{pdfPages}
                </div>
                {previewUrl ? (
                  <embed
                    key={`${previewUrl}-${activePage}`}
                    src={`${previewUrl}#page=${activePage}&toolbar=0&navpanes=0&scrollbar=0`}
                    type="application/pdf"
                    style={{ width: '100%', height: 270, borderRadius: 3, border: '1px solid var(--rule-strong)' }}
                  />
                ) : (
                  <div className="box box-warn">PDF preview appears after file upload.</div>
                )}
                <div style={{ marginTop: 12 }}>
                  <div className="mono" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.14em', color: 'var(--ink-faint)', marginBottom: 7 }}>Live Log</div>
                  <div className="tape">
                    {thinkingLog.slice(-5).map((line, i, arr) => (
                      <div key={i} className={`tape-line${i === arr.length - 1 ? ' cur' : ''}`}>{line}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {error && <div className="box box-crit fade-up" style={{ marginTop: 18 }}>{error}</div>}

        {/* Results */}
        {result && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18, marginTop: 18 }}>

            {/* Diagnosis hero */}
            <div className="dx-hero fade-up d1">
              <div className="kicker" style={{ marginBottom: 0 }}>Primary Diagnosis</div>
              <div className="dx-name">{result.primary_diagnosis || 'Undetermined'}</div>
            </div>

            {/* Ledger */}
            <div className="ledger fade-up d2">
              {[
                { label: 'Case ID', value: result.case_id, mono: true },
                { label: 'Confidence', value: `${confidence}%`, color: confColor, meter: true },
                { label: 'Processing Time', value: `${(result.processing_time || result.total_processing_time || 0).toFixed(1)}s`, mono: true },
                { label: 'Evidence Items', value: result.evidence_items_count || result.evidence_count || 0 },
                { label: 'Specialist Views', value: result.specialist_views_count || (result.layer1_views || []).length },
                { label: 'ICD-10-CM', value: result.icd10_code || '—', mono: true, accent: true },
              ].map((m) => (
                <div key={m.label} className="cell">
                  <div className="cell-k">{m.label}</div>
                  <div className={`cell-v${m.mono ? ' mono-v' : ''}${m.accent ? ' accent-v' : ''}`} style={m.color ? { color: m.color } : undefined}>
                    {String(m.value)}
                  </div>
                  {m.meter && (
                    <div className="meter">
                      <span style={{ width: `${confidence}%`, background: confColor }} />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {result.fallback_used && (
              <div className="box box-warn fade-up">
                <div className="mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--warn)', marginBottom: 6 }}>
                  Fallback Used
                </div>
                {result.fallback_reason || 'A non-primary provider or deterministic heuristic fallback was used for part of this analysis.'}
              </div>
            )}

            {/* ICD description + drug safety */}
            {(result.icd10_description || result.drug_safety?.warnings?.length) && (
              <div style={{ display: 'grid', gridTemplateColumns: result.icd10_description && result.drug_safety?.warnings?.length ? '1fr 1fr' : '1fr', gap: 14 }} className="fade-up">
                {result.icd10_description && (
                  <div className="chip">
                    <div className="cell-k" style={{ marginBottom: 8 }}>ICD-10-CM Code</div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
                      <span className="chip-code">{result.icd10_code}</span>
                      <span style={{ color: 'var(--ink-soft)', fontSize: 14 }}>{result.icd10_description}</span>
                    </div>
                  </div>
                )}
                {result.drug_safety?.warnings?.length > 0 && (
                  <div className="chip crit">
                    <div className="cell-k" style={{ marginBottom: 8, color: 'var(--crit)' }}>FDA Drug Warnings</div>
                    {result.drug_safety.warnings.slice(0, 2).map((w, i) => (
                      <div key={i} style={{ color: 'var(--crit)', fontSize: 13.5, marginBottom: 4 }}>⚠ {typeof w === 'string' ? w : `${w.drug}: ${w.detail}`}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Specialist views */}
            <section className="sheet fade-up">
              <div className="sheet-eyebrow">Layer 1 — Specialist AI Views</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
                {(result.layer1_views || []).map((v) => {
                  const conf = Math.round((v.confidence || 0) * 100)
                  const accentColor = AGENT_COLORS[v.agent] || 'var(--accent)'
                  return (
                    <div key={v.agent} className="spec" style={{ '--c': accentColor }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                        <div className="spec-role">{v.role || v.agent}</div>
                        <div className="spec-conf">{conf}%</div>
                      </div>
                      <div className="spec-bar"><span style={{ width: `${conf}%` }} /></div>
                      {summarizeFindings(v.findings).map((line, idx) => (
                        <div key={idx} className="spec-line">{line}</div>
                      ))}
                    </div>
                  )
                })}
              </div>
            </section>

            {/* Data flow trace */}
            {(result.data_flow_trace || []).length > 0 && (
              <section className="sheet fade-up">
                <div className="sheet-eyebrow">Data Flow Trace</div>
                {(result.data_flow_trace || []).map((step, idx) => (
                  <div key={idx} className="trace-row">
                    <div>
                      <div className="trace-tag">{step.layer}</div>
                      <div className="mono" style={{ fontSize: 9.5, color: 'var(--ink-faint)', textAlign: 'center', marginTop: 5 }}>{step.status}</div>
                    </div>
                    <div className="trace-io">
                      <div><b>IN →</b> {step.input}</div>
                      <div><b>OUT →</b> {step.output}</div>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {/* Download */}
            <section className="sheet fade-up" style={{ borderColor: 'var(--rule-ink)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
                <div>
                  <div className="sheet-eyebrow" style={{ marginBottom: 8 }}>Final Report</div>
                  <div style={{ fontFamily: 'var(--display)', fontWeight: 600, fontSize: 20 }}>Annotated Doctor Report — PDF</div>
                  <div style={{ color: 'var(--ink-soft)', fontSize: 14, marginTop: 4 }}>
                    XAI explanations · evidence links · ICD-10 coding · critical highlights
                  </div>
                </div>
                {reportDownloadUrl ? (
                  <a className="btn btn-key" href={reportDownloadUrl} target="_blank" rel="noreferrer">↓ Download PDF</a>
                ) : (
                  <div className="box box-warn" style={{ margin: 0 }}>PDF not yet available.</div>
                )}
              </div>
            </section>
          </div>
        )}

        <footer className="disclaimer">
          Research and educational prototype · not a medical device · not for clinical diagnosis or treatment decisions
        </footer>
      </main>
    </div>
  )
}

/* Sub-components */

function LogoIcon({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="0.6" y="0.6" width="34.8" height="34.8" rx="6" fill="#faf8f1" stroke="#18140d" strokeWidth="1.2" />
      <path d="M6 20 L11 20 L13 13 L16 25 L19 9 L22 20 L30 20" stroke="#c8341f" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
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
