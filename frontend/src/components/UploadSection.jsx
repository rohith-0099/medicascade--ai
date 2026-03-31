import { useState, useRef } from 'react'

const SPECIALIST_ICONS = {
    scan_analyzer: { icon: '🧠', label: 'Medical Imaging (MedGemma)' },
    symptom_analyzer: { icon: '🩺', label: 'Clinical NLP (GatorTron)' },
    lab_analyzer: { icon: '🔬', label: 'Lab Interpretation (MedGemma)' },
    literature_analyzer: { icon: '📚', label: 'Literature Match (BioGPT-Large)' },
    risk_analyzer: { icon: '⚠️', label: 'Risk Scoring (LightGBM + OpenMed)' },
}


export default function UploadSection({ onFileUpload }) {
    const [isDragging, setIsDragging] = useState(false)
    const [selectedFile, setSelectedFile] = useState(null)
    const fileInputRef = useRef(null)

    const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
    const handleDragLeave = () => setIsDragging(false)
    const handleDrop = (e) => {
        e.preventDefault(); setIsDragging(false)
        const file = e.dataTransfer.files[0]; handleFile(file)
    }
    const handleFileSelect = (e) => handleFile(e.target.files[0])

    const handleFile = (file) => {
        if (file && file.type === 'application/pdf') setSelectedFile(file)
        else if (file) alert('Please select a PDF file')
    }
    const handleSubmit = () => { if (selectedFile) onFileUpload(selectedFile) }

    const fmtSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    return (
        <div className="max-w-5xl mx-auto">
            <div className="glass-card" style={{ padding: '40px' }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '36px' }}>
                    <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#e2e8f0', marginBottom: '8px' }}>
                        Upload Patient Data
                    </h2>
                    <p style={{ color: '#64748b', fontSize: '1rem' }}>
                        Clinical PDF report is required for cascade analysis.
                    </p>
                </div>

                {/* Upload Zones */}
                <div style={{ marginBottom: '32px' }}>
                    {/* PDF Zone */}
                    <div
                        onClick={() => fileInputRef.current?.click()}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        style={{
                            border: isDragging
                                ? '2px solid rgba(6,182,212,0.8)'
                                : selectedFile
                                    ? '2px solid rgba(16,185,129,0.5)'
                                    : '2px dashed rgba(6,182,212,0.3)',
                            borderRadius: '16px',
                            padding: '32px 24px',
                            textAlign: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            background: isDragging
                                ? 'rgba(6,182,212,0.08)'
                                : selectedFile
                                    ? 'rgba(16,185,129,0.06)'
                                    : 'rgba(6,182,212,0.04)',
                            transform: isDragging ? 'scale(1.02)' : 'scale(1)',
                            boxShadow: isDragging ? '0 0 30px rgba(6,182,212,0.2)' : 'none'
                        }}
                    >
                        <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept="application/pdf" className="hidden" />

                        {selectedFile ? (
                            <div>
                                <div style={{
                                    width: '64px', height: '64px', margin: '0 auto 16px',
                                    background: 'rgba(16,185,129,0.2)', borderRadius: '16px',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}>
                                    <svg width="32" height="32" fill="none" stroke="#10b981" strokeWidth="2" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <p style={{ color: '#10b981', fontWeight: 700, marginBottom: '6px' }}>PDF Ready</p>
                                <p style={{ color: '#94a3b8', fontSize: '0.85rem', wordBreak: 'break-all' }}>{selectedFile.name}</p>
                                <p style={{ color: '#475569', fontSize: '0.78rem', marginTop: '4px' }}>{fmtSize(selectedFile.size)}</p>
                                <button
                                    onClick={(e) => { e.stopPropagation(); setSelectedFile(null) }}
                                    style={{ marginTop: '12px', color: '#ef4444', fontSize: '0.78rem', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                                >Remove</button>
                            </div>
                        ) : (
                            <div>
                                <div style={{
                                    width: '64px', height: '64px', margin: '0 auto 16px',
                                    background: 'rgba(6,182,212,0.15)', borderRadius: '16px',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}>
                                    <svg width="32" height="32" fill="none" stroke="#06b6d4" strokeWidth="2" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                    </svg>
                                </div>
                                <p style={{ color: '#e2e8f0', fontWeight: 700, marginBottom: '6px' }}>PDF Clinical Report</p>
                                <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Drop here or click to browse</p>
                                <span className="medical-badge badge-info" style={{ marginTop: '12px', display: 'inline-flex' }}>Required</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Submit Button */}
                {selectedFile && (
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '32px' }}>
                        <button onClick={handleSubmit} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '1.1rem' }}>
                            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            Start Cascade Analysis
                        </button>
                    </div>
                )}

                {/* Cascade Feature Grid */}
                <div style={{
                    borderTop: '1px solid rgba(6,182,212,0.1)',
                    paddingTop: '28px',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '16px'
                }}>
                    {[
                        { val: '3', label: 'Cascade Layers', sub: 'Sequential validation' },
                        { val: '5', label: 'AI Specialists', sub: 'Parallel analysis' },
                        { val: 'LLM', label: 'Cross-Validator', sub: 'Conflict resolution' },
                        { val: 'XAI', label: 'Explainability', sub: 'Evidence-annotated' },
                    ].map(s => (
                        <div key={s.label} className="stat-card" style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.8rem', fontWeight: 900, background: 'linear-gradient(135deg,#06b6d4,#818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '4px' }}>{s.val}</div>
                            <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>{s.label}</div>
                            <div style={{ color: '#475569', fontSize: '0.72rem', marginTop: '2px' }}>{s.sub}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Specialists Info */}
            <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
                {Object.values(SPECIALIST_ICONS).map(s => (
                    <div key={s.label} className="glass-card-light" style={{ padding: '14px', textAlign: 'center' }}>
                        <div style={{ fontSize: '1.6rem', marginBottom: '6px' }}>{s.icon}</div>
                        <div style={{ color: '#67e8f9', fontSize: '0.7rem', fontWeight: 600, lineHeight: 1.3 }}>{s.label}</div>
                    </div>
                ))}
            </div>
        </div>
    )
}
