import { useState, useEffect, useRef } from 'react'

// All sub-steps that appear in the live log, keyed to progress thresholds
const PIPELINE_STEPS = [
    { at: 5, layer: 0, icon: '▸', text: 'Received PDF upload — opening file stream' },
    { at: 10, layer: 0, icon: '▸', text: 'Layer 0 — PyPDF2: reading page structure & metadata' },
    { at: 15, layer: 0, icon: '▸', text: 'Layer 0 — pdfplumber: extracting tables and layout blocks' },
    { at: 22, layer: 0, icon: '▸', text: 'Layer 0 — DataClassifier: tagging sections (labs, symptoms, history, vitals)' },
    { at: 28, layer: 0, icon: '▸', text: 'Layer 0 — PDFExtractor: pulling embedded images & scan references' },
    { at: 33, layer: 0, icon: '✓', text: 'Layer 0 complete — PatientData object built, handing off to Layer 1' },
    { at: 38, layer: 1, icon: '▸', text: 'Layer 1 — Launching 5 specialist models in parallel' },
    { at: 42, layer: 1, icon: '▸', text: 'Specialist 1 — MedGemma-4B-IT: analysing imaging / scan references' },
    { at: 48, layer: 1, icon: '▸', text: 'Specialist 2 — UFNLP/GatorTron: processing clinical notes & symptoms' },
    { at: 55, layer: 1, icon: '▸', text: 'Specialist 3 — MedGemma-4B-IT: interpreting lab results & values' },
    { at: 61, layer: 1, icon: '▸', text: 'Specialist 4 — microsoft/BioGPT-Large: biomedical literature matching' },
    { at: 68, layer: 1, icon: '▸', text: 'Specialist 5 — BiomedNLP-BiomedBERT: risk factor scoring' },
    { at: 74, layer: 1, icon: '▸', text: 'Layer 1 — Collecting 5 SpecialistOpinion reports with confidence scores' },
    { at: 80, layer: 1, icon: '✓', text: 'Layer 1 complete — 5 reports ready, forwarding to Layer 2' },
    { at: 83, layer: 2, icon: '▸', text: 'Layer 2 — MedGemma-4B: reading all 5 specialist reports for cross-validation' },
    { at: 87, layer: 2, icon: '▸', text: 'Layer 2 — Comparing specialists: checking agreement, flagging conflicts' },
    { at: 90, layer: 2, icon: '▸', text: 'Layer 2 — Running anomaly detection on inter-specialist variance' },
    { at: 93, layer: 2, icon: '✓', text: 'Layer 2 complete — FinalDiagnosis object produced, forwarding to Layer 3' },
    { at: 94, layer: 3, icon: '▸', text: 'Layer 3 — MedGemma-4B: generating XAI explanation from diagnosis + evidence' },
    { at: 96, layer: 3, icon: '▸', text: 'Layer 3 — pdf_annotator: building annotated evidence PDF report' },
    { at: 97, layer: 3, icon: '▸', text: 'Layer 3 — image_annotator: marking scan regions with findings' },
    { at: 98, layer: 3, icon: '✓', text: 'Layer 3 complete — AnnotatedReport ready' },
    { at: 99, layer: -1, icon: '✓', text: 'Pipeline complete — returning diagnosis to API' },
]

export default function LoadingProgress({ progress, currentLayer }) {
    const [visibleSteps, setVisibleSteps] = useState([])
    const logRef = useRef(null)

    useEffect(() => {
        const shown = PIPELINE_STEPS.filter(s => progress >= s.at)
        setVisibleSteps(shown)
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
    }, [progress])

    const circumference = 2 * Math.PI * 54

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

            {/* ── Header ───────────────────────────────────────────── */}
            <div className="glass-card" style={{ padding: '24px 28px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '32px', flexWrap: 'wrap' }}>

                    {/* Progress ring */}
                    <div style={{ flexShrink: 0 }}>
                        <svg width="124" height="124" viewBox="0 0 124 124">
                            <circle cx="62" cy="62" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="7" />
                            <circle
                                cx="62" cy="62" r="54" fill="none"
                                stroke="#e05c6a" strokeWidth="7" strokeLinecap="round"
                                strokeDasharray={circumference}
                                strokeDashoffset={circumference - (circumference * progress) / 100}
                                style={{ transition: 'stroke-dashoffset 0.6s ease', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
                            />
                            <text x="62" y="56" textAnchor="middle" fill="#f08090" fontSize="26" fontWeight="800" fontFamily="Inter">{progress}%</text>
                            <text x="62" y="73" textAnchor="middle" fill="#4e5665" fontSize="11" fontFamily="Inter">complete</text>
                        </svg>
                    </div>

                    {/* Status */}
                    <div style={{ flex: 1, minWidth: '220px' }}>
                        <h2 style={{ color: '#edf0f4', fontSize: '17px', fontWeight: 800, marginBottom: '6px' }}>
                            Running Cascade Pipeline
                        </h2>
                        <p style={{ color: '#e05c6a', fontSize: '12px', fontWeight: 600, marginBottom: '18px', fontFamily: 'JetBrains Mono, monospace' }}>
                            ▶ {currentLayer}
                        </p>

                        {/* Layer status pills */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {[
                                { n: 0, label: 'L0: Extraction', startAt: 0, doneAt: 35 },
                                { n: 1, label: 'L1: Specialists', startAt: 35, doneAt: 80 },
                                { n: 2, label: 'L2: Validation', startAt: 80, doneAt: 93 },
                                { n: 3, label: 'L3: XAI Report', startAt: 93, doneAt: 98 },
                            ].map(l => {
                                const isDone = progress > l.doneAt
                                const isActive = progress > l.startAt && !isDone
                                return (
                                    <span key={l.n} style={{
                                        padding: '4px 12px',
                                        borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                                        display: 'inline-flex', alignItems: 'center', gap: '6px',
                                        background: isDone || isActive ? 'rgba(224,92,106,0.1)' : 'rgba(255,255,255,0.03)',
                                        color: isDone || isActive ? '#f08090' : '#4e5665',
                                        border: `1px solid ${isDone || isActive ? 'rgba(224,92,106,0.25)' : '#252a35'}`,
                                        transition: 'all 0.4s'
                                    }}>
                                        {isDone ? '✓' : isActive ? '▶' : '○'} {l.label}
                                    </span>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Terminal log ─────────────────────────────────────── */}
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                {/* Window bar */}
                <div style={{
                    padding: '10px 16px', borderBottom: '1px solid #252a35',
                    display: 'flex', alignItems: 'center', gap: '8px',
                    background: 'rgba(0,0,0,0.3)'
                }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                        {['#e05c6a', '#c4883a', '#4e5665'].map((c, i) => (
                            <div key={i} style={{ width: '10px', height: '10px', borderRadius: '50%', background: c }} />
                        ))}
                    </div>
                    <span style={{
                        fontSize: '11px', color: '#4e5665',
                        fontFamily: 'JetBrains Mono, monospace',
                        flex: 1, textAlign: 'center'
                    }}>
                        medicascade-pipeline — live log
                    </span>
                    <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#e05c6a', animation: 'pulseDot 2s infinite' }} />
                </div>

                {/* Log */}
                <div ref={logRef} style={{
                    height: '340px', overflowY: 'auto', padding: '14px 18px',
                    fontFamily: 'JetBrains Mono, monospace', fontSize: '12px',
                    background: '#080a0d'
                }}>
                    <div style={{ color: '#252a35', marginBottom: '10px', paddingBottom: '8px', borderBottom: '1px solid #14181f' }}>
                        <span style={{ color: '#e05c6a' }}>medicascade</span>
                        <span style={{ color: '#252a35' }}>@engine</span>
                        <span style={{ color: '#343b4a' }}> ~ % python main.py diagnose</span>
                    </div>

                    {visibleSteps.map((step, i) => {
                        const isLast = i === visibleSteps.length - 1 && progress < 99
                        const isDone = step.icon === '✓'
                        return (
                            <div key={i} style={{
                                display: 'flex', alignItems: 'flex-start', gap: '10px',
                                marginBottom: '5px',
                                animation: i === visibleSteps.length - 1 ? 'fadeIn 0.3s ease-out' : 'none'
                            }}>
                                <span style={{ color: '#343b4a', fontSize: '10px', width: '18px', flexShrink: 0, marginTop: '2px', textAlign: 'right' }}>
                                    {step.layer >= 0 ? `L${step.layer}` : 'OK'}
                                </span>
                                <span style={{ color: '#343b4a', flexShrink: 0 }}>│</span>
                                <span style={{
                                    color: isDone ? '#e05c6a' : isLast ? '#edf0f4' : '#4e5665',
                                    lineHeight: 1.5, flex: 1
                                }}>
                                    <span style={{ color: isDone ? '#e05c6a' : isLast ? '#e05c6a' : '#343b4a', marginRight: '6px' }}>
                                        {step.icon}
                                    </span>
                                    {step.text}
                                    {isLast && <span style={{ color: '#e05c6a', marginLeft: '6px', animation: 'pulseDot 0.8s infinite' }}>█</span>}
                                </span>
                            </div>
                        )
                    })}

                    {progress >= 99 && (
                        <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #14181f', color: '#e05c6a', fontWeight: 700 }}>
                            ✓ Pipeline complete — all 4 layers finished successfully
                        </div>
                    )}
                </div>
            </div>

            {/* ── Layer breakdown grid ─────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                {[
                    {
                        n: 0, startAt: 0, doneAt: 35, title: 'Layer 0 — Data Extraction',
                        steps: ['PyPDF2 reads PDF structure', 'pdfplumber extracts tables', 'DataClassifier sections text', 'Embedded images extracted']
                    },
                    {
                        n: 1, startAt: 35, doneAt: 80, title: 'Layer 1 — 5 Specialist Models',
                        steps: ['MedGemma-4B: imaging analysis', 'GatorTron: clinical notes', 'MedGemma-4B: lab interpretation', 'BioGPT-Large: literature match', 'BiomedBERT: risk scoring']
                    },
                    {
                        n: 2, startAt: 80, doneAt: 93, title: 'Layer 2 — Cross-Validation',
                        steps: ['Reads all 5 specialist reports', 'Detects contradictions', 'Runs anomaly detection', 'Unified FinalDiagnosis output']
                    },
                    {
                        n: 3, startAt: 93, doneAt: 98, title: 'Layer 3 — XAI Explanation',
                        steps: ['MedGemma-4B generates explanation', 'pdf_annotator marks evidence', 'image_annotator highlights scans', 'Returns AnnotatedReport']
                    },
                ].map(layer => {
                    const isDone = progress > layer.doneAt
                    const isActive = progress > layer.startAt && !isDone
                    return (
                        <div key={layer.n} style={{
                            background: isActive ? 'rgba(224,92,106,0.06)' : '#1a1e27',
                            border: `1px solid ${isActive ? 'rgba(224,92,106,0.25)' : isDone ? 'rgba(224,92,106,0.15)' : '#252a35'}`,
                            borderRadius: '9px', padding: '14px 16px',
                            transition: 'all 0.4s'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                                <span style={{
                                    width: '20px', height: '20px', borderRadius: '50%', fontSize: '10px',
                                    fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    background: isDone || isActive ? '#e05c6a' : '#252a35',
                                    color: isDone || isActive ? '#fff' : '#4e5665', flexShrink: 0
                                }}>{isDone ? '✓' : layer.n}</span>
                                <span style={{
                                    fontSize: '12px', fontWeight: 700,
                                    color: isActive ? '#f08090' : isDone ? '#e05c6a' : '#4e5665'
                                }}>{layer.title}</span>
                                {isActive && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#e05c6a', animation: 'pulseDot 1s infinite', marginLeft: 'auto' }} />}
                            </div>
                            {layer.steps.map((step, i) => {
                                const stepProgress = layer.startAt + ((layer.doneAt - layer.startAt) / layer.steps.length) * (i + 1)
                                const stepDone = progress >= stepProgress
                                return (
                                    <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', fontSize: '11px', marginBottom: '3px' }}>
                                        <span style={{ color: stepDone ? '#e05c6a' : '#252a35', flexShrink: 0 }}>
                                            {stepDone ? '●' : '○'}
                                        </span>
                                        <span style={{ color: stepDone ? '#9aa3b2' : '#343b4a' }}>{step}</span>
                                    </div>
                                )
                            })}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
