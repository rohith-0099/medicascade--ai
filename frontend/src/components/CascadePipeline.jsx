/**
 * CascadePipeline — Animated SVG diagram showing the three-layer cascade flow.
 * Used as a visual aid in the hero/upload section.
 */
export default function CascadePipeline() {
    const layers = [
        {
            id: 0, label: 'Layer 0', title: 'Data Extraction',
            color: '#818cf8', bg: 'rgba(99,102,241,0.12)',
            border: 'rgba(99,102,241,0.25)',
            items: ['PDF Parsing', 'OCR', 'Tables', 'Images'],
            icon: '📄'
        },
        {
            id: 1, label: 'Layer 1', title: '5 Specialists (Parallel)',
            color: '#06b6d4', bg: 'rgba(6,182,212,0.1)',
            border: 'rgba(6,182,212,0.25)',
            items: ['🩺 Symptoms', '🔬 Lab Results', '🧠 Imaging', '📋 Notes', '⚠️ Risk'],
            icon: '🤖'
        },
        {
            id: 2, label: 'Layer 2', title: 'Cross-Validation',
            color: '#a855f7', bg: 'rgba(168,85,247,0.1)',
            border: 'rgba(168,85,247,0.25)',
            items: ['LLM Validator', 'Conflict Resolution', 'Anomaly Detection', 'Consensus Score'],
            icon: '🎯'
        },
        {
            id: 3, label: 'Layer 3', title: 'XAI Explainer',
            color: '#10b981', bg: 'rgba(16,185,129,0.1)',
            border: 'rgba(16,185,129,0.25)',
            items: ['Pathophysiology', 'Evidence Annotation', 'Clinical XAI', 'PDF Report'],
            icon: '💡'
        }
    ]

    return (
        <div style={{
            display: 'flex', flexDirection: 'column', gap: '0',
            maxWidth: '800px', margin: '0 auto'
        }}>
            {layers.map((layer, i) => (
                <div key={layer.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    {/* Layer box */}
                    <div style={{
                        width: '100%', padding: '16px 20px',
                        background: layer.bg,
                        border: `1px solid ${layer.border}`,
                        borderRadius: '14px',
                        display: 'flex', alignItems: 'center', gap: '16px',
                        transition: 'all 0.3s',
                        boxShadow: `0 0 20px ${layer.bg}`
                    }}>
                        {/* Layer badge */}
                        <div style={{
                            width: '48px', height: '48px', borderRadius: '12px', flexShrink: 0,
                            background: `${layer.color}25`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            border: `1px solid ${layer.color}40`, fontSize: '1.4rem'
                        }}>
                            {layer.icon}
                        </div>

                        <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '6px' }}>
                                <span style={{
                                    background: `${layer.color}20`, color: layer.color,
                                    border: `1px solid ${layer.color}30`,
                                    padding: '2px 8px', borderRadius: '99px',
                                    fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.08em'
                                }}>{layer.label}</span>
                                <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: '0.95rem' }}>{layer.title}</span>
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                {layer.items.map(item => (
                                    <span key={item} style={{
                                        padding: '2px 8px', borderRadius: '6px', fontSize: '0.7rem',
                                        background: 'rgba(255,255,255,0.06)', color: '#64748b',
                                        border: '1px solid rgba(255,255,255,0.06)'
                                    }}>{item}</span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Connector arrow */}
                    {i < layers.length - 1 && (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '4px', paddingBottom: '4px' }}>
                            <div style={{ width: '2px', height: '12px', background: 'rgba(6,182,212,0.3)' }} />
                            <svg width="14" height="10" viewBox="0 0 14 10">
                                <path d="M7 10L0 0h14L7 10z" fill="rgba(6,182,212,0.4)" />
                            </svg>
                        </div>
                    )}
                </div>
            ))}

            {/* Final output */}
            <div style={{
                marginTop: '8px', padding: '12px 20px',
                background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
                borderRadius: '12px', textAlign: 'center'
            }}>
                <span style={{ color: '#6ee7b7', fontWeight: 700, fontSize: '0.9rem' }}>
                    ✅ Unified Diagnosis + Confidence Score + XAI-Annotated Report
                </span>
            </div>
        </div>
    )
}
