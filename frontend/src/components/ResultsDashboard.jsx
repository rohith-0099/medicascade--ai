import { useState } from 'react'

export default function ResultsDashboard({ results, onReset }) {
    const [openSections, setOpenSections] = useState({
        l0: false, l1: true, l2: true, l3: true, secondary: false
    })
    const toggle = (key) => setOpenSections(p => ({ ...p, [key]: !p[key] }))

    const conf = results.confidence || 0
    const confPct = Math.round(conf * 100)
    const cvScore = Math.round((results.cross_validation_score || 0) * 100)
    const confColor = conf >= 0.75 ? '#39d353' : conf >= 0.5 ? '#f0b429' : '#f85149'
    const confLabel = conf >= 0.75 ? 'High Confidence' : conf >= 0.5 ? 'Moderate' : 'Low Confidence'

    const opinions = results.layer1_opinions || []
    const l2 = results.layer2_validation || {}

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* ── Final Diagnosis Banner ─────────────────────────── */}
            <div className="glass-card slide-up" style={{ borderTop: `3px solid ${confColor}`, position: 'relative', overflow: 'hidden' }}>
                {/* Subtle glow bg */}
                <div style={{
                    position: 'absolute', top: 0, right: 0, width: '300px', height: '100%',
                    background: `radial-gradient(ellipse at right, rgba(${hexToRgb(confColor)},0.06) 0%, transparent 70%)`,
                    pointerEvents: 'none'
                }} />
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '24px', flexWrap: 'wrap', position: 'relative' }}>
                    <div style={{ flex: 1, minWidth: '260px' }}>
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <div className="layer-badge layer-2"><span className="dot">2</span>Layer 2 Output</div>
                            {results.anomaly_detected && <span className="medical-badge badge-warning">⚠️ Anomaly Detected</span>}
                        </div>
                        <p style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '6px' }}>
                            Primary Diagnosis
                        </p>
                        <h2 style={{ fontSize: '26px', fontWeight: 900, color: 'var(--text-primary)', lineHeight: 1.2, marginBottom: '14px' }}>
                            {results.primary_diagnosis || 'No diagnosis'}
                        </h2>
                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                            <span style={{
                                display: 'inline-flex', alignItems: 'center', gap: '6px',
                                padding: '5px 14px', borderRadius: '99px', fontWeight: 700, fontSize: '13px',
                                background: `rgba(${hexToRgb(confColor)},0.12)`,
                                color: confColor, border: `1px solid ${confColor}44`,
                                textShadow: `0 0 10px rgba(${hexToRgb(confColor)},0.4)`
                            }}>
                                <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: confColor, animation: 'pulseDot 2s infinite' }} />
                                {confPct}% — {confLabel}
                            </span>
                            <span className="medical-badge badge-info" style={{ fontSize: '12px', padding: '5px 12px' }}>
                                Cross-Val: {cvScore}%
                            </span>
                            <span className="medical-badge badge-success" style={{ fontSize: '12px', padding: '5px 12px' }}>
                                {opinions.length || 5} Specialists
                            </span>
                        </div>
                        <div className="confidence-bar-track" style={{ height: '6px', marginTop: '16px' }}>
                            <div className="confidence-bar-fill" style={{ width: `${confPct}%`, background: `linear-gradient(90deg, ${confColor}88, ${confColor})` }} />
                        </div>
                    </div>
                    <ConfidenceGauge confidence={conf} color={confColor} />
                </div>

                {/* Reasoning */}
                {results.reasoning && (
                    <div style={{
                        marginTop: '20px', padding: '14px 18px',
                        background: 'rgba(57,211,83,0.05)', border: '1px solid rgba(57,211,83,0.12)',
                        borderRadius: '10px'
                    }}>
                        <p style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
                            Layer 2 — AI Reasoning
                        </p>
                        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '13px' }}>{results.reasoning}</p>
                    </div>
                )}
            </div>

            {/* ── Stats Row ──────────────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                {[
                    { label: 'Confidence', val: `${confPct}%`, color: confColor },
                    { label: 'Cross-Validation', val: `${cvScore}%`, color: '#388bfd' },
                    { label: 'Specialists Used', val: l2.num_specialists_used || opinions.length || 5, color: '#bc8cff' },
                    { label: 'Processing Time', val: `${(results.total_processing_time || 0).toFixed(1)}s`, color: '#39d353' },
                ].map(s => (
                    <div key={s.label} className="metric-card">
                        <div className="metric-label">{s.label}</div>
                        <div className="metric-value" style={{ fontSize: '22px', color: s.color, textShadow: `0 0 14px rgba(${hexToRgb(s.color)},0.4)` }}>{s.val}</div>
                    </div>
                ))}
            </div>

            {/* ─────────────────────────────────────────────────────── */}
            {/* LAYER BY LAYER TRANSPARENCY SECTIONS                   */}
            {/* ─────────────────────────────────────────────────────── */}

            {/* ── Layer 0 ────────────────────────────────────────── */}
            <Section
                id="l0" open={openSections.l0} onToggle={() => toggle('l0')}
                layerN={0} color="#bc8cff"
                title="Layer 0 — Data Extraction"
                subtitle="pdfplumber · PyPDF2 · DataClassifier"
                badge="L0"
            >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    {[
                        { label: 'Text Extraction', detail: 'pdfplumber → PyPDF2 fallback', icon: '📄' },
                        { label: 'Table Extraction', detail: 'pdfplumber page.extract_tables()', icon: '📊' },
                        { label: 'Data Classification', detail: 'Regex → sections: labs, symptoms, vitals, history, meds', icon: '🔤' },
                        { label: 'Image Extraction', detail: 'Embedded JPEG/PNG via PyPDF2 XObject', icon: '🖼️' },
                    ].map(item => (
                        <div key={item.label} style={{
                            background: 'rgba(188,140,255,0.05)', border: '1px solid rgba(188,140,255,0.12)',
                            borderRadius: '8px', padding: '12px 14px'
                        }}>
                            <div style={{ fontSize: '16px', marginBottom: '4px' }}>{item.icon}</div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: '#bc8cff', marginBottom: '3px' }}>{item.label}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>{item.detail}</div>
                        </div>
                    ))}
                </div>
                <div className="info-box" style={{ marginTop: '12px', fontSize: '12px' }}>
                    <strong>Output:</strong> PatientData object with structured fields: text, tables, images, demographics, clinical_notes, lab_results, symptoms, medications
                </div>
            </Section>

            {/* ── Layer 1 ─────────────────────────────────────────── */}
            <Section
                id="l1" open={openSections.l1} onToggle={() => toggle('l1')}
                layerN={1} color="#39d353"
                title="Layer 1 — Specialist Analysis"
                subtitle="5 models run independently in parallel"
                badge="L1"
            >
                {opinions.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {opinions.map((op, i) => {
                            const c = Math.round((op.confidence || 0) * 100)
                            const col = c >= 70 ? '#39d353' : c >= 45 ? '#f0b429' : '#f85149'
                            return (
                                <div key={i} className={`specialist-card ${c >= 70 ? 'high-conf' : c >= 45 ? 'mid-conf' : 'low-conf'}`}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                                                <span style={{
                                                    fontSize: '10px', fontWeight: 700, color: '#0d1117',
                                                    background: '#39d353', padding: '2px 8px', borderRadius: '99px'
                                                }}>S{i + 1}</span>
                                                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                                                    {op.model_name}
                                                </span>
                                            </div>

                                            <p style={{ fontSize: '13px', fontWeight: 700, color: col, marginBottom: '6px' }}>
                                                {op.diagnosis}
                                            </p>

                                            {op.reasoning && (
                                                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '8px' }}>
                                                    {op.reasoning}
                                                </p>
                                            )}

                                            {op.key_findings && op.key_findings.length > 0 && (
                                                <div style={{ marginBottom: '8px' }}>
                                                    <p style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>Key Findings</p>
                                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                                        {op.key_findings.slice(0, 6).map((f, j) => (
                                                            <span key={j} style={{
                                                                fontSize: '11px', padding: '2px 9px', borderRadius: '99px',
                                                                background: 'rgba(57,211,83,0.08)', color: '#39d353',
                                                                border: '1px solid rgba(57,211,83,0.15)'
                                                            }}>{f}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {op.detected_conditions && op.detected_conditions.length > 0 && (
                                                <div>
                                                    <p style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>Detected Conditions</p>
                                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                                        {op.detected_conditions.slice(0, 5).map((cond, j) => (
                                                            <span key={j} style={{
                                                                fontSize: '11px', padding: '2px 9px', borderRadius: '99px',
                                                                background: 'rgba(248,81,73,0.08)', color: '#f85149',
                                                                border: '1px solid rgba(248,81,73,0.15)'
                                                            }}>{cond}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Confidence mini gauge */}
                                        <div style={{ textAlign: 'center', flexShrink: 0 }}>
                                            <div style={{
                                                width: '56px', height: '56px', borderRadius: '50%',
                                                background: `conic-gradient(${col} ${c * 3.6}deg, #30363d ${c * 3.6}deg)`,
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                boxShadow: `0 0 12px rgba(${hexToRgb(col)},0.25)`,
                                                position: 'relative'
                                            }}>
                                                <div style={{
                                                    width: '44px', height: '44px', borderRadius: '50%',
                                                    background: 'var(--bg-card)',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                                }}>
                                                    <span style={{ fontSize: '13px', fontWeight: 900, color: col }}>{c}%</span>
                                                </div>
                                            </div>
                                            <p style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '4px', fontWeight: 600 }}>CONFIDENCE</p>
                                        </div>
                                    </div>

                                    {/* Confidence bar */}
                                    <div className="confidence-bar-track" style={{ marginTop: '12px' }}>
                                        <div className="confidence-bar-fill" style={{
                                            width: `${c}%`,
                                            background: `linear-gradient(90deg, ${col}66, ${col})`
                                        }} />
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                ) : (
                    <div className="warning-box">No specialist opinions returned — check backend connection</div>
                )}
            </Section>

            {/* ── Layer 2 ─────────────────────────────────────────── */}
            <Section
                id="l2" open={openSections.l2} onToggle={() => toggle('l2')}
                layerN={2} color="#f0b429"
                title="Layer 2 — Cross-Validation"
                subtitle="MedGemma-4B reads all 5 reports and produces unified diagnosis"
                badge="L2"
            >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                    {[
                        { label: 'Primary Diagnosis', val: l2.primary_diagnosis || results.primary_diagnosis, color: confColor },
                        { label: 'Overall Confidence', val: `${Math.round((l2.confidence || conf) * 100)}%`, color: confColor },
                        { label: 'Cross-Validation Score', val: `${cvScore}%`, color: '#388bfd' },
                        { label: 'Specialists Consulted', val: l2.num_specialists_used || opinions.length || 5, color: '#bc8cff' },
                    ].map(m => (
                        <div key={m.label} style={{
                            background: 'rgba(240,180,41,0.05)', border: '1px solid rgba(240,180,41,0.12)',
                            borderRadius: '8px', padding: '12px 14px'
                        }}>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
                                {m.label}
                            </div>
                            <div style={{ fontSize: '18px', fontWeight: 800, color: m.color, textShadow: `0 0 10px rgba(${hexToRgb(m.color)},0.35)` }}>
                                {m.val}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Conflicts */}
                {l2.conflicts && (
                    <div className="warning-box" style={{ marginBottom: '12px' }}>
                        <strong>⚖️ Conflicts Detected & Resolved:</strong> {l2.conflicts}
                    </div>
                )}

                {/* Anomaly */}
                {results.anomaly_detected && (
                    <div className="error-box" style={{ marginBottom: '12px' }}>
                        <strong>🚨 Anomaly Detected:</strong> {results.anomaly_description || 'Unusual pattern found in specialist outputs'}
                    </div>
                )}

                {/* Reasoning */}
                {l2.reasoning && (
                    <div style={{
                        background: 'rgba(240,180,41,0.05)', border: '1px solid rgba(240,180,41,0.12)',
                        borderRadius: '10px', padding: '14px 16px'
                    }}>
                        <p style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
                            Validator Reasoning
                        </p>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{l2.reasoning}</p>
                    </div>
                )}

                {/* Secondary diagnoses */}
                {results.secondary_diagnoses && results.secondary_diagnoses.length > 0 && (
                    <div style={{ marginTop: '14px' }}>
                        <p style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
                            Differential Diagnoses Considered
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {results.secondary_diagnoses.map((sec, i) => {
                                const c = Math.round((sec.confidence || 0) * 100)
                                return (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 12px', background: 'var(--bg-hover)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                                        <span style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '11px', width: '20px' }}>#{i + 1}</span>
                                        <span style={{ color: 'var(--text-secondary)', flex: 1, fontSize: '13px' }}>{sec.diagnosis}</span>
                                        <div className="confidence-bar-track" style={{ width: '80px' }}>
                                            <div className="confidence-bar-fill" style={{ width: `${c}%`, background: '#484f58' }} />
                                        </div>
                                        <span style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 600, width: '34px', textAlign: 'right' }}>{c}%</span>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}
            </Section>

            {/* ── Layer 3 ─────────────────────────────────────────── */}
            <Section
                id="l3" open={openSections.l3} onToggle={() => toggle('l3')}
                layerN={3} color="#388bfd"
                title="Layer 3 — XAI Explanation"
                subtitle="MedGemma-4B generates human-readable clinical explanation"
                badge="L3"
            >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '14px' }}>
                    {[
                        { icon: '💡', label: 'MedGemma XAI', detail: 'Clinical explanation in plain language' },
                        { icon: '📌', label: 'PDF Annotator', detail: 'Evidence markers in annotated PDF report' },
                        { icon: '🎨', label: 'Image Annotator', detail: 'Scan regions highlighted with findings' },
                    ].map(item => (
                        <div key={item.label} style={{
                            background: 'rgba(56,139,253,0.05)', border: '1px solid rgba(56,139,253,0.12)',
                            borderRadius: '8px', padding: '12px 14px', textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '20px', marginBottom: '6px' }}>{item.icon}</div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: '#388bfd', marginBottom: '3px' }}>{item.label}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{item.detail}</div>
                        </div>
                    ))}
                </div>

                {results.explanation_text && (
                    <div className="xai-highlight" style={{ whiteSpace: 'pre-wrap', maxHeight: '380px', overflowY: 'auto', fontSize: '13px' }}>
                        {results.explanation_text}
                    </div>
                )}

                {/* Evidence count */}
                {results.layer3_xai?.evidence_count > 0 && (
                    <div className="success-box" style={{ marginTop: '12px' }}>
                        <strong>✅ Evidence Items Extracted:</strong> {results.layer3_xai.evidence_count} clinical evidence points annotated in the report
                    </div>
                )}

                {/* PDF download */}
                {results.annotated_pdf_path && (
                    <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: 'rgba(57,211,83,0.06)', border: '1px solid rgba(57,211,83,0.2)', borderRadius: '10px' }}>
                        <div>
                            <p style={{ fontWeight: 700, color: '#39d353', marginBottom: '3px', fontSize: '13px' }}>📄 Annotated PDF Report Ready</p>
                            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Evidence-annotated clinical report with XAI explanation</p>
                        </div>
                        <a href="/api/report/diagnosis_report.pdf" download style={{
                            padding: '9px 18px', borderRadius: '8px', fontWeight: 700, fontSize: '13px',
                            background: 'linear-gradient(135deg, #1a4d2e, #39d353)', color: '#d5f5db',
                            textDecoration: 'none', border: '1px solid rgba(57,211,83,0.4)',
                            boxShadow: '0 0 14px rgba(57,211,83,0.2)', flexShrink: 0
                        }}>
                            ↓ Download PDF
                        </a>
                    </div>
                )}
            </Section>

            {/* ── Actions ─────────────────────────────────────────── */}
            <div style={{ display: 'flex', gap: '12px' }}>
                <button onClick={onReset} className="btn-primary" style={{ flex: 1 }}>
                    ← Analyse Another Patient
                </button>
            </div>

            {/* ── Disclaimer ──────────────────────────────────────── */}
            <div className="warning-box" style={{ fontSize: '12px' }}>
                <strong>⚠️ Medical Disclaimer:</strong> This AI output is for research and educational purposes only. Always consult a qualified healthcare provider for medical decisions.
            </div>
        </div>
    )
}

/* ── Reusable accordion section ───────────────────────────────── */
function Section({ id, open, onToggle, layerN, color, title, subtitle, badge, children }) {
    return (
        <div style={{
            background: 'var(--bg-card)', border: `1px solid ${open ? color + '33' : 'var(--border)'}`,
            borderRadius: '12px', overflow: 'hidden', transition: 'border-color 0.3s'
        }}>
            {/* Toggle header */}
            <button onClick={onToggle} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
                padding: '14px 18px', background: 'none', border: 'none', cursor: 'pointer',
                textAlign: 'left'
            }}>
                <span className={`layer-badge layer-${layerN}`} style={{ flexShrink: 0 }}>
                    <span className="dot">{layerN}</span>{badge}
                </span>
                <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1px' }}>{title}</p>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>{subtitle}</p>
                </div>
                <span style={{
                    color: open ? color : 'var(--text-muted)', fontSize: '16px',
                    transition: 'transform 0.2s', transform: open ? 'rotate(0deg)' : 'rotate(-90deg)',
                    textShadow: open ? `0 0 8px ${color}88` : 'none'
                }}>▼</span>
            </button>

            {/* Collapsible content */}
            {open && (
                <div style={{ padding: '0 18px 18px', animation: 'fadeIn 0.3s ease-out' }}>
                    <div style={{ borderTop: `1px solid ${color}22`, paddingTop: '16px' }}>
                        {children}
                    </div>
                </div>
            )}
        </div>
    )
}

function ConfidenceGauge({ confidence, color }) {
    const pct = Math.round(confidence * 100)
    const r = 44
    const circ = 2 * Math.PI * r
    const offset = circ - circ * confidence
    return (
        <div style={{ position: 'relative', width: '130px', height: '130px', flexShrink: 0 }}>
            <svg width="130" height="130" viewBox="0 0 110 110">
                <circle cx="55" cy="55" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                <circle cx="55" cy="55" r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
                    strokeDasharray={circ} strokeDashoffset={offset}
                    style={{
                        transition: 'stroke-dashoffset 1.2s ease', transform: 'rotate(-90deg)', transformOrigin: '50% 50%',
                        filter: `drop-shadow(0 0 6px rgba(${hexToRgb(color)},0.6))`
                    }} />
            </svg>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '22px', fontWeight: 900, color, textShadow: `0 0 14px rgba(${hexToRgb(color)},0.5)` }}>{pct}%</span>
                <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.1em' }}>CONFIDENCE</span>
            </div>
        </div>
    )
}

function hexToRgb(hex) {
    const r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    if (!r) return '57,211,83'
    return `${parseInt(r[1], 16)},${parseInt(r[2], 16)},${parseInt(r[3], 16)}`
}
