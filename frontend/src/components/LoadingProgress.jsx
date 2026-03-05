import { useState, useEffect, useRef } from 'react'

// All sub-steps that appear in the live log, keyed to progress thresholds
const PIPELINE_STEPS = [
    { at: 5, layer: 0, icon: '📂', text: 'Received PDF upload — opening file stream' },
    { at: 10, layer: 0, icon: '📄', text: 'Layer 0 ▸ PyPDF2: reading page structure & metadata' },
    { at: 15, layer: 0, icon: '📊', text: 'Layer 0 ▸ pdfplumber: extracting tables and layout blocks' },
    { at: 22, layer: 0, icon: '🔤', text: 'Layer 0 ▸ DataClassifier: regex-tagging sections (labs, symptoms, history, vitals…)' },
    { at: 28, layer: 0, icon: '🖼️', text: 'Layer 0 ▸ PDFExtractor: pulling embedded images & scan references' },
    { at: 33, layer: 0, icon: '✅', text: 'Layer 0 complete — PatientData object built, handing off to Layer 1' },
    { at: 38, layer: 1, icon: '🚀', text: 'Layer 1 ▸ Launching 5 specialist models in parallel' },
    { at: 42, layer: 1, icon: '🧠', text: 'Specialist 1 ▸ MedGemma-4B-IT: analysing medical imaging / scan references' },
    { at: 48, layer: 1, icon: '🩺', text: 'Specialist 2 ▸ UFNLP/GatorTron-medium: processing clinical notes & symptoms' },
    { at: 55, layer: 1, icon: '🔬', text: 'Specialist 3 ▸ MedGemma-4B-IT: interpreting lab results & CBC values' },
    { at: 61, layer: 1, icon: '📚', text: 'Specialist 4 ▸ microsoft/BioGPT-Large: biomedical literature matching' },
    { at: 68, layer: 1, icon: '⚠️', text: 'Specialist 5 ▸ microsoft/BiomedNLP-BiomedBERT: risk factor scoring' },
    { at: 74, layer: 1, icon: '📋', text: 'Layer 1 ▸ Collecting 5 SpecialistOpinion reports with confidence scores' },
    { at: 80, layer: 1, icon: '✅', text: 'Layer 1 complete — 5 reports ready, forwarding to Layer 2' },
    { at: 83, layer: 2, icon: '🔄', text: 'Layer 2 ▸ MedGemma-4B: loading all 5 specialist reports for cross-validation' },
    { at: 87, layer: 2, icon: '⚖️', text: 'Layer 2 ▸ Comparing specialists: checking agreement, flagging conflicts' },
    { at: 90, layer: 2, icon: '🚨', text: 'Layer 2 ▸ Running anomaly detection on inter-specialist variance' },
    { at: 93, layer: 2, icon: '✅', text: 'Layer 2 complete — FinalDiagnosis object produced, forwarding to Layer 3' },
    { at: 94, layer: 3, icon: '💡', text: 'Layer 3 ▸ MedGemma-4B: generating XAI explanation from diagnosis + evidence' },
    { at: 96, layer: 3, icon: '📌', text: 'Layer 3 ▸ pdf_annotator: building annotated evidence PDF report' },
    { at: 97, layer: 3, icon: '🎨', text: 'Layer 3 ▸ image_annotator: marking scan regions with findings' },
    { at: 98, layer: 3, icon: '✅', text: 'Layer 3 complete — AnnotatedReport ready' },
    { at: 99, layer: -1, icon: '🎯', text: 'Pipeline complete — returning diagnosis to API' },
]

const LAYER_COLORS = {
    0: '#bc8cff', // purple
    1: '#39d353', // green
    2: '#f0b429', // amber
    3: '#388bfd', // blue
    '-1': '#e6edf3',
}

const LAYER_LABELS = {
    0: 'L0: Data Extraction',
    1: 'L1: Specialists',
    2: 'L2: Cross-Validation',
    3: 'L3: XAI Explainer',
    '-1': 'Complete',
}

export default function LoadingProgress({ progress, currentLayer }) {
    const [visibleSteps, setVisibleSteps] = useState([])
    const logRef = useRef(null)

    useEffect(() => {
        const shown = PIPELINE_STEPS.filter(s => progress >= s.at)
        setVisibleSteps(shown)
        // auto-scroll log to bottom
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight
        }
    }, [progress])

    const circumference = 2 * Math.PI * 54

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

            {/* ── Header card ──────────────────────────────────────── */}
            <div className="glass-card" style={{ padding: '24px 28px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '28px', flexWrap: 'wrap' }}>

                    {/* Ring */}
                    <div style={{ position: 'relative', flexShrink: 0 }}>
                        <svg width="130" height="130" viewBox="0 0 130 130">
                            <circle cx="65" cy="65" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                            <circle
                                cx="65" cy="65" r="54" fill="none"
                                stroke="#39d353" strokeWidth="8" strokeLinecap="round"
                                strokeDasharray={circumference}
                                strokeDashoffset={circumference - (circumference * progress) / 100}
                                style={{
                                    transition: 'stroke-dashoffset 0.6s ease',
                                    transform: 'rotate(-90deg)', transformOrigin: '50% 50%',
                                    filter: 'drop-shadow(0 0 8px rgba(57,211,83,0.6))'
                                }}
                            />
                            <text x="65" y="58" textAnchor="middle" fill="#39d353" fontSize="28" fontWeight="800"
                                style={{ textShadow: '0 0 12px rgba(57,211,83,0.8)', fontFamily: 'Inter' }}>
                                {progress}%
                            </text>
                            <text x="65" y="76" textAnchor="middle" fill="#484f58" fontSize="11" fontFamily="Inter">
                                complete
                            </text>
                        </svg>
                    </div>

                    {/* Status */}
                    <div style={{ flex: 1, minWidth: '220px' }}>
                        <h2 style={{ color: 'var(--text-primary)', fontSize: '18px', fontWeight: 800, marginBottom: '6px' }}>
                            Running Cascade Pipeline
                        </h2>
                        <p style={{ color: '#39d353', fontSize: '13px', fontWeight: 600, marginBottom: '16px', fontFamily: 'JetBrains Mono, monospace' }}>
                            ▶ {currentLayer}
                        </p>

                        {/* Layer progress pills */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {[0, 1, 2, 3].map(l => {
                                const doneAt = [35, 80, 93, 98][l]
                                const startAt = [0, 35, 80, 93][l]
                                const isDone = progress > doneAt
                                const isActive = progress > startAt && !isDone
                                const col = LAYER_COLORS[l]
                                return (
                                    <span key={l} style={{
                                        padding: '4px 12px 4px 8px',
                                        borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                                        display: 'inline-flex', alignItems: 'center', gap: '6px',
                                        background: isDone ? 'rgba(57,211,83,0.1)' : isActive ? `rgba(${hexToRgb(col)},0.15)` : 'rgba(255,255,255,0.04)',
                                        color: isDone ? '#39d353' : isActive ? col : '#484f58',
                                        border: `1px solid ${isDone ? 'rgba(57,211,83,0.3)' : isActive ? `${col}44` : 'rgba(255,255,255,0.06)'}`,
                                        boxShadow: isActive ? `0 0 10px rgba(${hexToRgb(col)},0.2)` : 'none',
                                        transition: 'all 0.4s'
                                    }}>
                                        <span style={{
                                            width: '16px', height: '16px', borderRadius: '50%',
                                            background: isDone ? '#39d353' : isActive ? col : '#30363d',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '9px', fontWeight: 900, color: '#0d1117'
                                        }}>
                                            {isDone ? '✓' : l}
                                        </span>
                                        L{l}
                                        {isActive && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: col, animation: 'pulseDot 1s infinite' }} />}
                                    </span>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Live terminal log ────────────────────────────────── */}
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                {/* Terminal header */}
                <div style={{
                    padding: '10px 16px', borderBottom: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', gap: '8px',
                    background: 'rgba(0,0,0,0.2)'
                }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f85149' }} />
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f0b429' }} />
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#39d353' }} />
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', flex: 1, textAlign: 'center' }}>
                        medicascade-pipeline — live log
                    </span>
                    <div className="pulse-dot" />
                </div>

                {/* Log body */}
                <div ref={logRef} style={{
                    height: '360px', overflowY: 'auto', padding: '14px 18px',
                    fontFamily: 'JetBrains Mono, monospace', fontSize: '12px',
                    background: '#0a0e14'
                }}>
                    {/* static header */}
                    <div style={{ color: '#484f58', marginBottom: '10px', borderBottom: '1px solid #1c2128', paddingBottom: '8px' }}>
                        <span style={{ color: '#39d353' }}>medicascade</span>
                        <span style={{ color: '#484f58' }}>@</span>
                        <span style={{ color: '#388bfd' }}>cascade-engine</span>
                        <span style={{ color: '#484f58' }}> ~ % python main.py diagnose --cascade-all</span>
                    </div>

                    {visibleSteps.map((step, i) => {
                        const col = LAYER_COLORS[step.layer]
                        const isLast = i === visibleSteps.length - 1 && progress < 99
                        return (
                            <div key={i} style={{
                                display: 'flex', alignItems: 'flex-start', gap: '10px',
                                marginBottom: '6px', opacity: isLast ? 1 : 0.8,
                                animation: i === visibleSteps.length - 1 ? 'fadeIn 0.3s ease-out' : 'none'
                            }}>
                                {/* Layer tag */}
                                <span style={{
                                    fontSize: '9px', fontWeight: 700,
                                    color: col, flexShrink: 0,
                                    width: '24px', textAlign: 'right',
                                    marginTop: '1px', letterSpacing: '-0.02em'
                                }}>
                                    {step.layer >= 0 ? `L${step.layer}` : 'OK'}
                                </span>
                                <span style={{ color: '#484f58', flexShrink: 0 }}>│</span>
                                {/* Icon */}
                                <span style={{ flexShrink: 0, fontSize: '13px' }}>{step.icon}</span>
                                {/* Text */}
                                <span style={{
                                    color: isLast ? '#e6edf3' : '#8b949e',
                                    lineHeight: 1.5,
                                    textShadow: isLast ? `0 0 8px ${col}66` : 'none'
                                }}>
                                    {step.text}
                                    {isLast && <span style={{ color: '#39d353', animation: 'pulseDot 0.8s infinite', marginLeft: '6px' }}>█</span>}
                                </span>
                            </div>
                        )
                    })}

                    {progress >= 99 && (
                        <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #1c2128', color: '#39d353', fontWeight: 700 }}>
                            ✅ Pipeline complete — all layers finished in {progress}% time
                        </div>
                    )}
                </div>
            </div>

            {/* ── What each layer does now ─────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                {[
                    {
                        n: 0, col: '#bc8cff', title: 'Layer 0 — Data Extraction',
                        steps: ['PyPDF2 reads PDF structure', 'pdfplumber extracts tables', 'DataClassifier sections text', 'Embedded images extracted']
                    },
                    {
                        n: 1, col: '#39d353', title: 'Layer 1 — 5 Specialist Models',
                        steps: ['MedGemma: imaging analysis', 'GatorTron: clinical notes', 'MedGemma: lab interpretation', 'BioGPT: literature matching', 'BiomedBERT: risk scoring']
                    },
                    {
                        n: 2, col: '#f0b429', title: 'Layer 2 — Cross-Validation',
                        steps: ['Reads all 5 specialist reports', 'Detects contradictions', 'Runs anomaly detection', 'Produces unified FinalDiagnosis']
                    },
                    {
                        n: 3, col: '#388bfd', title: 'Layer 3 — XAI Explanation',
                        steps: ['MedGemma generates explanation', 'pdf_annotator marks evidence', 'image_annotator marks scans', 'Returns AnnotatedReport']
                    },
                ].map(layer => {
                    const doneAt = [35, 80, 93, 98][layer.n]
                    const startAt = [0, 35, 80, 93][layer.n]
                    const isDone = progress > doneAt
                    const isActive = progress > startAt && !isDone
                    return (
                        <div key={layer.n} style={{
                            background: isActive ? `rgba(${hexToRgb(layer.col)},0.06)` : 'var(--bg-card)',
                            border: `1px solid ${isActive ? layer.col + '44' : isDone ? 'rgba(57,211,83,0.2)' : 'var(--border)'}`,
                            borderRadius: '10px', padding: '14px 16px',
                            boxShadow: isActive ? `0 0 16px rgba(${hexToRgb(layer.col)},0.1)` : 'none',
                            transition: 'all 0.4s'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                                <span style={{
                                    width: '20px', height: '20px', borderRadius: '50%', fontSize: '10px',
                                    fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    background: isDone ? '#39d353' : isActive ? layer.col : '#30363d',
                                    color: '#0d1117', flexShrink: 0
                                }}>{isDone ? '✓' : layer.n}</span>
                                <span style={{ fontSize: '12px', fontWeight: 700, color: isActive ? layer.col : isDone ? '#39d353' : 'var(--text-secondary)' }}>
                                    {layer.title}
                                </span>
                                {isActive && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: layer.col, animation: 'pulseDot 1s infinite', marginLeft: 'auto' }} />}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                {layer.steps.map((step, i) => {
                                    const stepProgress = startAt + ((doneAt - startAt) / layer.steps.length) * (i + 1)
                                    const stepDone = progress >= stepProgress
                                    return (
                                        <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', fontSize: '11px' }}>
                                            <span style={{ color: stepDone ? '#39d353' : '#30363d', flexShrink: 0, marginTop: '1px' }}>
                                                {stepDone ? '●' : '○'}
                                            </span>
                                            <span style={{ color: stepDone ? 'var(--text-secondary)' : '#484f58' }}>{step}</span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

function hexToRgb(hex) {
    const r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    if (!r) return '57,211,83'
    return `${parseInt(r[1], 16)},${parseInt(r[2], 16)},${parseInt(r[3], 16)}`
}
