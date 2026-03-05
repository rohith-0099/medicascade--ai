import { useState, useEffect, useRef } from 'react'
import UploadSection from './components/UploadSection'
import LoadingProgress from './components/LoadingProgress'
import ResultsDashboard from './components/ResultsDashboard'
import AIDebugView from './components/AIDebugView'

/* ── Sidebar nav items ──────────────────────────────────────── */
const NAV = [
    { icon: '🏠', label: 'Dashboard', id: 'home' },
    { icon: '📄', label: 'Upload Report', id: 'upload' },
    { icon: '📊', label: 'Results', id: 'results' },
    { icon: '🔬', label: 'AI Debug View', id: 'debug' },
]

const ARCHITECTURE_LAYERS = [
    { n: '0', label: 'Data Extraction', cls: 'layer-0', detail: 'pdfplumber + PyPDF2' },
    { n: '1', label: '5 Specialists', cls: 'layer-1', detail: 'MedGemma · GatorTron · BioGPT' },
    { n: '2', label: 'Cross-Validation', cls: 'layer-2', detail: 'MedGemma-4B LLM' },
    { n: '3', label: 'XAI Explainer', cls: 'layer-3', detail: 'SHAP + Grad-CAM + MedGemma' },
]

function App() {
    const [state, setState] = useState({
        isProcessing: false,
        progress: 0,
        currentLayer: '',
        results: null,
        error: null
    })
    const [activeNav, setActiveNav] = useState('home')
    const progressInterval = useRef(null)

    const handleFileUpload = async (file, scan) => {
        setState({ isProcessing: true, progress: 0, currentLayer: 'Uploading patient data...', results: null, error: null })
        setActiveNav('upload')

        const formData = new FormData()
        formData.append('file', file)
        if (scan) formData.append('scan', scan)

        startProgressSimulation()

        try {
            const response = await fetch('/api/diagnose', { method: 'POST', body: formData })
            if (!response.ok) throw new Error(`Server error: ${response.status}`)
            const data = await response.json()
            stopProgressSimulation()
            setState({ isProcessing: false, progress: 100, currentLayer: 'Analysis complete!', results: data, error: null })
            setActiveNav('results')
        } catch (error) {
            stopProgressSimulation()
            setState(prev => ({ ...prev, isProcessing: false, error: error.message }))
        }
    }

    const startProgressSimulation = () => {
        if (progressInterval.current) clearInterval(progressInterval.current)
        const layers = [
            { progress: 10, label: 'Layer 0 — Reading patient PDF...' },
            { progress: 20, label: 'Layer 0 — Extracting text & tables...' },
            { progress: 30, label: 'Layer 0 — Classifying data sections...' },
            { progress: 42, label: 'Layer 1 — Launching 5 specialist models...' },
            { progress: 52, label: 'Layer 1 — Symptom analysis (GatorTron)...' },
            { progress: 60, label: 'Layer 1 — Lab interpretation (MedGemma)...' },
            { progress: 66, label: 'Layer 1 — Imaging analysis (MedGemma)...' },
            { progress: 72, label: 'Layer 1 — Literature matching (BioGPT)...' },
            { progress: 78, label: 'Layer 1 — Risk scoring (LightGBM + OpenMed)...' },
            { progress: 84, label: 'Layer 2 — Cross-validating specialist reports...' },
            { progress: 89, label: 'Layer 2 — Resolving conflicts & anomaly detection...' },
            { progress: 93, label: 'Layer 3 — Generating XAI explanation (MedGemma)...' },
            { progress: 97, label: 'Layer 3 — Annotating evidence & building report...' },
            { progress: 98, label: 'Finalising diagnosis...' },
        ]
        let idx = 0
        progressInterval.current = setInterval(() => {
            if (idx < layers.length) {
                const layer = layers[idx]
                setState(prev => ({ ...prev, progress: layer.progress, currentLayer: layer.label }))
                idx++
            }
        }, 1800)
    }

    const stopProgressSimulation = () => {
        if (progressInterval.current) { clearInterval(progressInterval.current); progressInterval.current = null }
    }

    const handleReset = () => {
        stopProgressSimulation()
        setState({ isProcessing: false, progress: 0, currentLayer: '', results: null, error: null })
        setActiveNav('home')
    }

    useEffect(() => () => { if (progressInterval.current) clearInterval(progressInterval.current) }, [])

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-base)' }}>

            {/* ── Sidebar ──────────────────────────────────────────── */}
            <aside className="sidebar" style={{ width: '240px', flexShrink: 0 }}>

                {/* Logo */}
                <div className="sidebar-logo">
                    <div className="sidebar-logo-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <rect x="10" y="2" width="4" height="20" rx="2" fill="white" />
                            <rect x="2" y="10" width="20" height="4" rx="2" fill="white" />
                        </svg>
                    </div>
                    <div>
                        <div className="sidebar-title">MediCascade AI</div>
                        <div className="sidebar-subtitle">Disease Prediction Engine</div>
                    </div>
                </div>

                <hr className="sidebar-divider" />

                {/* Nav */}
                <div className="sidebar-section">Navigation</div>
                {NAV.map(item => (
                    <div
                        key={item.id}
                        className={`sidebar-item ${activeNav === item.id ? 'active' : ''}`}
                        onClick={() => {
                            if (item.id === 'results' && !state.results) return
                            if (item.id === 'debug' && !state.results) return
                            setActiveNav(item.id)
                        }}
                        style={{ opacity: (item.id === 'results' || item.id === 'debug') && !state.results ? 0.4 : 1 }}
                    >
                        <span className="icon">{item.icon}</span>
                        {item.label}
                    </div>
                ))}

                <hr className="sidebar-divider" />

                {/* Architecture info */}
                <div className="sidebar-section">Architecture</div>
                {ARCHITECTURE_LAYERS.map(l => (
                    <div key={l.n} style={{ padding: '6px 12px', marginBottom: '2px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                            <span className={`layer-badge ${l.cls}`} style={{ padding: '2px 8px 2px 4px', fontSize: '10px' }}>
                                <span className="dot" style={{ width: '16px', height: '16px', fontSize: '10px' }}>{l.n}</span>
                                {l.label}
                            </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', paddingLeft: '4px' }}>{l.detail}</div>
                    </div>
                ))}

                <hr className="sidebar-divider" />

                {/* Status indicator */}
                <div style={{ padding: '8px 12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>System</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--accent)' }}>
                        <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--accent)', flexShrink: 0, boxShadow: '0 0 6px var(--accent-glow)' }} />
                        Backend Connected
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>HF Token ✓ · 5 Models Ready</div>
                </div>
            </aside>

            {/* ── Main ─────────────────────────────────────────────── */}
            <main style={{ flex: 1, padding: '32px 40px', maxWidth: '1100px' }}>

                {/* ── Page Header ─────────────────────────────────── */}
                <div className="page-header fade-in">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h1 className="page-title">
                                {activeNav === 'home' && 'Dashboard'}
                                {activeNav === 'upload' && 'Upload Patient Report'}
                                {activeNav === 'results' && 'Diagnosis Results'}
                                {activeNav === 'debug' && 'AI Debug View'}
                            </h1>
                            <p className="page-description">
                                {activeNav === 'home' && 'Upload a patient PDF to run the full cascade diagnosis pipeline.'}
                                {activeNav === 'upload' && 'Provide a medical report PDF and optionally a scan image.'}
                                {activeNav === 'results' && 'Cross-validated diagnosis from 5 specialist models + XAI explanation.'}
                                {activeNav === 'debug' && 'Raw specialist opinions and model confidence scores.'}
                            </p>
                        </div>
                        {state.results && (
                            <button className="btn-secondary" onClick={handleReset}>← New Analysis</button>
                        )}
                    </div>
                </div>

                {/* ── Error ───────────────────────────────────────── */}
                {state.error && (
                    <div className="error-box slide-up" style={{ marginBottom: '24px' }}>
                        <strong>Analysis Error:</strong> {state.error}
                        <button onClick={handleReset} style={{ marginLeft: '12px', fontWeight: 600, color: 'var(--danger)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
                            Try again
                        </button>
                    </div>
                )}

                {/* ── Content ─────────────────────────────────────── */}
                <div className="slide-up">

                    {/* Dashboard home — quick stats + upload CTA */}
                    {activeNav === 'home' && !state.results && !state.isProcessing && (
                        <>
                            {/* Metric row */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '28px' }}>
                                {[
                                    { label: 'Specialist Models', value: '5', delta: 'MedGemma · GatorTron · BioGPT' },
                                    { label: 'Architecture Layers', value: '4', delta: 'L0 → L1 → L2 → L3' },
                                    { label: 'Cross-Validation', value: '100%', delta: 'All specialists checked' },
                                    { label: 'XAI Output', value: '✓', delta: 'SHAP + Grad-CAM' },
                                ].map(m => (
                                    <div key={m.label} className="metric-card">
                                        <div className="metric-label">{m.label}</div>
                                        <div className="metric-value">{m.value}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>{m.delta}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Info box */}
                            <div className="info-box" style={{ marginBottom: '24px' }}>
                                <strong>ℹ️  How it works:</strong> Upload a patient medical report PDF (lab results, clinical notes, imaging reports, history).
                                The system runs 5 specialist AI models in parallel, cross-validates their outputs, and generates an XAI-annotated diagnosis report.
                            </div>

                            {/* Upload section */}
                            <UploadSection onFileUpload={handleFileUpload} />
                        </>
                    )}

                    {/* Upload tab */}
                    {activeNav === 'upload' && !state.isProcessing && !state.results && (
                        <UploadSection onFileUpload={handleFileUpload} />
                    )}

                    {/* Processing */}
                    {state.isProcessing && (
                        <LoadingProgress progress={state.progress} currentLayer={state.currentLayer} />
                    )}

                    {/* Results */}
                    {state.results && !state.isProcessing && activeNav === 'results' && (
                        <ResultsDashboard results={state.results} onReset={handleReset} />
                    )}

                    {/* Debug */}
                    {state.results && !state.isProcessing && activeNav === 'debug' && (
                        <AIDebugView diagnosisResult={state.results} />
                    )}

                    {/* Auto-show results/debug when no explicit tab selected */}
                    {state.results && !state.isProcessing && activeNav === 'home' && (
                        <>
                            <ResultsDashboard results={state.results} onReset={handleReset} />
                            <div style={{ marginTop: '32px' }}>
                                <AIDebugView diagnosisResult={state.results} />
                            </div>
                        </>
                    )}
                </div>

                {/* ── Footer ──────────────────────────────────────── */}
                <footer style={{ marginTop: '60px', paddingTop: '20px', borderTop: '1px solid var(--border)', fontSize: '12px', color: 'var(--text-muted)' }}>
                    MediCascade AI v2.0 · Research & Demonstration Purposes Only · © 2026
                </footer>
            </main>
        </div>
    )
}

export default App
