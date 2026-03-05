const SPECIALIST_META = {
    scan_analyzer: { icon: '🧠', label: 'Medical Imaging', model: 'google/medgemma-4b-it', color: '#06b6d4' },
    symptom_analyzer: { icon: '🩺', label: 'Symptoms & Clinical Notes', model: 'UFNLP/gatortron-medium', color: '#818cf8' },
    lab_analyzer: { icon: '🔬', label: 'Lab Results', model: 'google/medgemma-4b-it', color: '#a855f7' },
    literature_analyzer: { icon: '📚', label: 'Biomedical Literature', model: 'microsoft/BioGPT-Large', color: '#10b981' },
    risk_analyzer: { icon: '⚠️', label: 'Patient Risk Scoring', model: 'LightGBM + OpenMed-SuperClinical-434M', color: '#f59e0b' },
    notes_analyzer: { icon: '📋', label: 'Clinical Notes (GatorTron)', model: 'UFNLP/gatortron-medium', color: '#818cf8' },
}


function hexToRgba(hex, alpha = 1) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    if (!result) return `rgba(6,182,212,${alpha})`
    return `rgba(${parseInt(result[1], 16)},${parseInt(result[2], 16)},${parseInt(result[3], 16)},${alpha})`
}

function SpecialistCard({ opinion, index }) {
    const meta = SPECIALIST_META[opinion.model_name] || { icon: '🤖', label: opinion.model_name, color: '#06b6d4' }
    const conf = opinion.confidence || 0
    const confPct = Math.round(conf * 100)
    const confClass = conf >= 0.7 ? 'high-conf' : conf >= 0.45 ? 'mid-conf' : 'low-conf'
    const confLabel = conf >= 0.7 ? 'High' : conf >= 0.45 ? 'Moderate' : 'Low'
    const confTextColor = conf >= 0.7 ? '#10b981' : conf >= 0.45 ? '#f59e0b' : '#ef4444'

    const r = 20, circ = 2 * Math.PI * r
    const offset = circ - circ * conf

    return (
        <div className={`specialist-card ${confClass}`} style={{ '--accent-color': meta.color }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.6rem' }}>{meta.icon}</span>
                    <div>
                        <p style={{ color: meta.color, fontWeight: 700, fontSize: '0.82rem', letterSpacing: '0.04em' }}>Specialist {index + 1}</p>
                        <p style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '0.88rem' }}>{meta.label}</p>
                    </div>
                </div>
                {/* Mini arc confidence */}
                <div style={{ position: 'relative', width: '56px', height: '56px' }}>
                    <svg width="56" height="56" viewBox="0 0 56 56">
                        <circle cx="28" cy="28" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
                        <circle
                            cx="28" cy="28" r={r} fill="none"
                            stroke={confTextColor} strokeWidth="5" strokeLinecap="round"
                            strokeDasharray={circ} strokeDashoffset={offset}
                            style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%', transition: 'stroke-dashoffset 1s ease' }}
                        />
                    </svg>
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ fontSize: '0.72rem', fontWeight: 800, color: confTextColor }}>{confPct}%</span>
                    </div>
                </div>
            </div>

            {/* Diagnosis */}
            <div style={{
                padding: '10px 14px', borderRadius: '10px',
                background: hexToRgba(meta.color, 0.07),
                border: `1px solid ${hexToRgba(meta.color, 0.15)}`,
                marginBottom: '12px'
            }}>
                <p style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>Diagnosis</p>
                <p style={{ color: '#e2e8f0', fontWeight: 700, fontSize: '0.92rem' }}>{opinion.diagnosis || '—'}</p>
            </div>

            {/* Confidence badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <div className="confidence-bar-track" style={{ flex: 1 }}>
                    <div className="confidence-bar-fill" style={{ width: `${confPct}%`, background: confTextColor }} />
                </div>
                <span style={{ color: confTextColor, fontWeight: 700, fontSize: '0.78rem', flexShrink: 0 }}>{confLabel}</span>
            </div>

            {/* Reasoning */}
            {opinion.reasoning && (
                <p style={{ color: '#475569', fontSize: '0.78rem', lineHeight: 1.6, fontStyle: 'italic', marginBottom: '12px' }}>
                    "{opinion.reasoning.slice(0, 160)}{opinion.reasoning.length > 160 ? '...' : ''}"
                </p>
            )}

            {/* Detected Conditions */}
            {opinion.detected_conditions && opinion.detected_conditions.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                    {opinion.detected_conditions.slice(0, 5).map((c, i) => (
                        <span key={i} style={{
                            padding: '2px 8px', borderRadius: '99px', fontSize: '0.68rem', fontWeight: 600,
                            background: hexToRgba(meta.color, 0.1), color: meta.color,
                            border: `1px solid ${hexToRgba(meta.color, 0.2)}`
                        }}>{c}</span>
                    ))}
                </div>
            )}
        </div>
    )
}

export default function AIDebugView({ diagnosisResult }) {
    if (!diagnosisResult) return null

    const { layer1_opinions, layer2_validation, layer3_xai } = diagnosisResult

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>

            {/* ── Layer 1: Specialists ──────────────────── */}
            <div className="glass-card fade-in">
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
                    <div className="layer-badge layer-1"><span className="dot">1</span>Layer 1</div>
                    <h2 style={{ color: '#e2e8f0', fontWeight: 800, fontSize: '1.15rem' }}>
                        Specialist Analysis — {layer1_opinions?.length ?? 5} Independent Models
                    </h2>
                </div>

                {layer1_opinions && layer1_opinions.length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' }}>
                        {layer1_opinions.map((op, i) => (
                            <SpecialistCard key={i} opinion={op} index={i} />
                        ))}
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', padding: '32px', color: '#475569' }}>
                        <p>Specialist opinions not available in response.</p>
                        <p style={{ fontSize: '0.8rem', marginTop: '8px', color: '#334155' }}>This data is returned when the backend is connected.</p>
                    </div>
                )}
            </div>

            {/* ── Layer 2: Cross-Validation ─────────────── */}
            <div className="glass-card fade-in">
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
                    <div className="layer-badge layer-2"><span className="dot">2</span>Layer 2</div>
                    <h2 style={{ color: '#e2e8f0', fontWeight: 800, fontSize: '1.15rem' }}>
                        LLM Cross-Validation
                    </h2>
                </div>

                {layer2_validation ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
                        {/* Primary Diagnosis */}
                        <div style={{
                            gridColumn: '1 / -1', padding: '16px 20px',
                            background: 'rgba(168,85,247,0.07)', border: '1px solid rgba(168,85,247,0.2)',
                            borderRadius: '14px'
                        }}>
                            <p style={{ color: '#d8b4fe', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
                                Confirmed Diagnosis
                            </p>
                            <p style={{ color: '#e2e8f0', fontWeight: 900, fontSize: '1.5rem', marginBottom: '12px' }}>
                                {layer2_validation.primary_diagnosis}
                            </p>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                                <div style={{ flex: 1, minWidth: '200px' }}>
                                    <div className="confidence-bar-track" style={{ height: '8px' }}>
                                        <div className="confidence-bar-fill" style={{ width: `${Math.round(layer2_validation.confidence * 100)}%` }} />
                                    </div>
                                </div>
                                <span style={{ color: '#06b6d4', fontWeight: 800, fontSize: '1rem', flexShrink: 0 }}>
                                    {Math.round(layer2_validation.confidence * 100)}%
                                </span>
                            </div>
                        </div>

                        {/* Cross-val score */}
                        <div style={{ padding: '16px', background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.12)', borderRadius: '14px' }}>
                            <p style={{ color: '#64748b', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>Cross-Validation Score</p>
                            <p style={{ color: '#67e8f9', fontWeight: 900, fontSize: '2rem', marginBottom: '4px' }}>
                                {Math.round(layer2_validation.cross_validation_score * 100)}%
                            </p>
                            <p style={{ color: '#475569', fontSize: '0.78rem' }}>
                                Agreement across {layer2_validation.num_specialists_used || 'multiple'} specialists
                            </p>
                        </div>

                        {/* Reasoning */}
                        <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px' }}>
                            <p style={{ color: '#64748b', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>Validation Reasoning</p>
                            <p style={{ color: '#94a3b8', fontSize: '0.84rem', lineHeight: 1.6 }}>{layer2_validation.reasoning}</p>
                        </div>

                        {/* Anomaly alert */}
                        {layer2_validation.anomaly_detected && (
                            <div style={{ padding: '14px 16px', background: 'rgba(245,158,11,0.1)', border: '2px solid rgba(245,158,11,0.3)', borderRadius: '14px', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>⚠️</span>
                                <div>
                                    <p style={{ color: '#fcd34d', fontWeight: 700, marginBottom: '4px' }}>Anomaly Detected</p>
                                    <p style={{ color: '#92400e', fontSize: '0.82rem' }}>{layer2_validation.anomaly_message}</p>
                                </div>
                            </div>
                        )}

                        {/* Conflicts */}
                        {layer2_validation.conflicts && layer2_validation.conflicts !== '' && (
                            <div style={{ padding: '14px 16px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '14px' }}>
                                <p style={{ color: '#fca5a5', fontWeight: 700, marginBottom: '4px', fontSize: '0.84rem' }}>Conflicts Resolved</p>
                                <p style={{ color: '#7f1d1d', fontSize: '0.8rem', lineHeight: 1.5 }}>{layer2_validation.conflicts}</p>
                            </div>
                        )}
                    </div>
                ) : (
                    <p style={{ color: '#475569', fontStyle: 'italic' }}>Layer 2 cross-validation data not available.</p>
                )}
            </div>

            {/* ── Layer 3: XAI ─────────────────────────── */}
            {layer3_xai && (
                <div className="glass-card fade-in">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
                        <div className="layer-badge layer-3"><span className="dot">3</span>Layer 3</div>
                        <h2 style={{ color: '#e2e8f0', fontWeight: 800, fontSize: '1.15rem' }}>
                            XAI Explainer Output
                        </h2>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                        <div style={{ padding: '12px 20px', borderRadius: '12px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
                            <p style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 700, marginBottom: '4px' }}>EVIDENCE ITEMS</p>
                            <p style={{ color: '#6ee7b7', fontWeight: 900, fontSize: '1.5rem' }}>{layer3_xai.evidence_count}</p>
                        </div>
                        <div style={{ padding: '12px 20px', borderRadius: '12px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.12)', flex: 1 }}>
                            <p style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 700, marginBottom: '4px' }}>ANNOTATED PDF</p>
                            <p style={{ color: layer3_xai.annotated_pdf_path ? '#6ee7b7' : '#ef4444', fontWeight: 600, fontSize: '0.88rem' }}>
                                {layer3_xai.annotated_pdf_path ? '✅ Report Generated' : '❌ Generation failed'}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Raw JSON Accordion ────────────────────── */}
            <details style={{ borderRadius: '14px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)' }}>
                <summary style={{
                    padding: '14px 20px', cursor: 'pointer', fontWeight: 700,
                    background: 'rgba(255,255,255,0.03)', color: '#475569', fontSize: '0.85rem',
                    userSelect: 'none', listStyle: 'none', display: 'flex', alignItems: 'center', gap: '8px'
                }}>
                    🔍 Raw API Response (Developer View)
                </summary>
                <pre style={{
                    padding: '20px', background: 'rgba(5,11,24,0.9)', color: '#64748b',
                    fontSize: '0.72rem', overflowX: 'auto', lineHeight: 1.6,
                    borderTop: '1px solid rgba(255,255,255,0.04)', maxHeight: '400px', overflowY: 'auto'
                }}>
                    {JSON.stringify(diagnosisResult, null, 2)}
                </pre>
            </details>
        </div>
    )
}
