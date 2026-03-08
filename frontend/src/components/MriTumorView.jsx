import { useState, useMemo } from 'react'
import Plot from 'react-plotly.js'

const MODALITIES = [
  { key: 't1', label: 'T1', hint: 'Baseline anatomy' },
  { key: 't1ce', label: 'T1ce', hint: 'Contrast enhanced' },
  { key: 't2', label: 'T2', hint: 'Edema highlight' },
  { key: 'flair', label: 'FLAIR', hint: 'Fluid suppression' },
]

const LAYERS = [
  { key: 'brain', label: 'Brain', color: '#5ec4e8', defaultOpacity: 0.12 },
  { key: 'necrotic', label: 'Necrotic Core', color: '#e03050', defaultOpacity: 0.85 },
  { key: 'edema', label: 'Edema', color: '#e8a800', defaultOpacity: 0.65 },
  { key: 'enhancing', label: 'Enhancing Tumor', color: '#8040e0', defaultOpacity: 0.85 },
]

const MODALITY_COLORS = { t1: '#00d4ff', t1ce: '#7c3aed', t2: '#f59e0b', flair: '#00d4a0' }

export default function MriTumorView({ onBack }) {
  const [files, setFiles] = useState({ t1: null, t1ce: null, t2: null, flair: null })
  const [layerVisible, setLayerVisible] = useState({ brain: true, necrotic: true, edema: true, enhancing: true })
  const [brainOpacity, setBrainOpacity] = useState(15)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const canSubmit = MODALITIES.every((m) => files[m.key]) && !loading
  const hasMeshData = Boolean(
    result && Object.entries(result.meshes || {}).some(([, m]) => m && m.x && m.x.length > 0),
  )

  const handleFileChange = (modality, file) => setFiles((p) => ({ ...p, [modality]: file || null }))

  const submit = async () => {
    if (!canSubmit) return
    setLoading(true); setError(''); setResult(null)
    const form = new FormData()
    MODALITIES.forEach((m) => form.append(m.key, files[m.key]))
    try {
      const res = await fetch('/api/mri/analyze', { method: 'POST', body: form })
      if (!res.ok) {
        let detail = `API error ${res.status}`
        try { const err = await res.json(); if (err?.detail) detail = err.detail } catch {}
        throw new Error(detail)
      }
      setResult(await res.json())
    } catch (e) {
      setError(e.message || 'MRI analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  const resetAll = () => {
    setFiles({ t1: null, t1ce: null, t2: null, flair: null })
    setError(''); setResult(null); setLoading(false)
    setLayerVisible({ brain: true, necrotic: true, edema: true, enhancing: true })
    setBrainOpacity(15)
  }

  // Build Plotly traces (memoized to avoid recomputation on unrelated state changes)
  const plotTraces = useMemo(() => {
    const traces = []
    if (!result?.meshes) return traces
    const m = result.meshes

    // Brain — semi-transparent outer shell
    if (m.brain && m.brain.x?.length > 0 && layerVisible.brain) {
      traces.push({
        type: 'mesh3d', x: m.brain.x, y: m.brain.y, z: m.brain.z,
        i: m.brain.i, j: m.brain.j, k: m.brain.k,
        color: '#a0d2e8', opacity: brainOpacity / 100, name: 'Brain',
        flatshading: false,
        lighting: { ambient: 0.6, diffuse: 0.7, specular: 0.2, roughness: 0.7 },
        lightposition: { x: 100, y: 200, z: 150 },
        hoverinfo: 'name',
      })
    }

    // Tumors — solid colored
    const tumorCfg = [
      { key: 'necrotic', color: '#e03050', opacity: 0.85, name: 'Necrotic Core' },
      { key: 'edema', color: '#e8a800', opacity: 0.65, name: 'Edema' },
      { key: 'enhancing', color: '#8040e0', opacity: 0.85, name: 'Enhancing Tumor' },
    ]
    for (const cfg of tumorCfg) {
      const mesh = m[cfg.key]
      if (mesh && mesh.x?.length > 0 && layerVisible[cfg.key]) {
        traces.push({
          type: 'mesh3d', x: mesh.x, y: mesh.y, z: mesh.z,
          i: mesh.i, j: mesh.j, k: mesh.k,
          color: cfg.color, opacity: cfg.opacity, name: cfg.name,
          flatshading: false,
          lighting: { ambient: 0.5, diffuse: 0.8, specular: 0.4, roughness: 0.4 },
          lightposition: { x: 100, y: 200, z: 150 },
          hoverinfo: 'name',
        })
      }
    }
    return traces
  }, [result?.meshes, layerVisible, brainOpacity])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg-base)' }}>
      {/* Sidebar */}
      <aside className="sidebar" style={{ width: 240 }}>
        <div className="sidebar-logo">
          <svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs><linearGradient id="lg-mri" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse"><stop stopColor="#00d4ff" /><stop offset="1" stopColor="#7c3aed" /></linearGradient></defs>
            <rect width="36" height="36" rx="10" fill="url(#lg-mri)" />
            <path d="M8 18 L14 10 L18 14 L22 8 L28 18" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <circle cx="18" cy="24" r="4" stroke="white" strokeWidth="1.8" fill="none" />
            <circle cx="18" cy="24" r="1.5" fill="white" opacity="0.9" />
          </svg>
          <div>
            <div className="sidebar-title">MediCascade AI</div>
            <div className="sidebar-subtitle">3D Brain MRI Viewer</div>
          </div>
        </div>

        <div className="sidebar-section">Toggle Layers</div>
        {LAYERS.map((layer) => (
          <label key={layer.key} style={{
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6,
            border: `1px solid ${layerVisible[layer.key] ? `${layer.color}30` : 'var(--border)'}`,
            borderRadius: 10, padding: '9px 12px', cursor: 'pointer',
            background: layerVisible[layer.key] ? `${layer.color}08` : 'transparent',
          }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
              background: layerVisible[layer.key] ? layer.color : 'var(--text-muted)',
              boxShadow: layerVisible[layer.key] ? `0 0 6px ${layer.color}` : 'none',
            }} />
            <input type="checkbox" checked={layerVisible[layer.key]}
              onChange={(e) => setLayerVisible((p) => ({ ...p, [layer.key]: e.target.checked }))}
              style={{ display: 'none' }}
            />
            <span style={{ color: layerVisible[layer.key] ? 'var(--text-primary)' : 'var(--text-muted)', fontSize: 12 }}>{layer.label}</span>
          </label>
        ))}

        {result && (
          <div style={{ marginTop: 12, padding: '0 4px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 10, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
              Brain Opacity: {brainOpacity}%
            </div>
            <input type="range" min="0" max="100" value={brainOpacity}
              onChange={(e) => setBrainOpacity(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#5ec4e8' }}
            />
          </div>
        )}

        <button className="btn-secondary" onClick={onBack} style={{ width: '100%', marginTop: 14 }}>
          &#8592; Back To Clinical
        </button>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, padding: '28px 34px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <h1 className="page-title">3D Brain Tumor Visualization</h1>
          <p className="page-description">
            Upload 4 MRI modalities — nnU-Net segments the tumor and renders it inside the brain in 3D.
          </p>
        </div>

        {/* Upload */}
        <div className="glass-card" style={{ padding: 18 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'monospace', marginBottom: 14 }}>
            Upload 4 MRI Modalities (.nii / .nii.gz)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 10 }}>
            {MODALITIES.map((mod) => {
              const mc = MODALITY_COLORS[mod.key]
              const hasFile = Boolean(files[mod.key])
              return (
                <div key={mod.key} style={{
                  border: `1.5px dashed ${hasFile ? mc : 'rgba(0,212,255,0.15)'}`,
                  borderRadius: 10, padding: 12,
                  background: hasFile ? `${mc}08` : 'rgba(0,0,0,0.15)',
                  cursor: 'pointer',
                }} onClick={() => document.getElementById(`mri-${mod.key}`)?.click()}>
                  <div style={{ color: mc, fontSize: 11, fontWeight: 800, fontFamily: 'monospace', marginBottom: 4 }}>{mod.label}</div>
                  <input id={`mri-${mod.key}`} type="file" accept=".nii,.nii.gz,application/gzip"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFileChange(mod.key, e.target.files?.[0] || null)}
                  />
                  {hasFile
                    ? <div style={{ color: 'var(--text-primary)', fontSize: 11, wordBreak: 'break-all' }}>
                        {files[mod.key].name.slice(0, 22)}{files[mod.key].name.length > 22 ? '...' : ''}
                      </div>
                    : <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{mod.hint}</div>
                  }
                </div>
              )
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {loading && <div className="pulse-dot" />}
              <span style={{ color: loading ? 'var(--accent)' : 'var(--text-muted)', fontSize: 12 }}>
                {loading ? 'Running nnU-Net segmentation (may take 1-3 min)...' : canSubmit ? 'Ready to analyze' : 'Upload all 4 modalities'}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-secondary" onClick={resetAll} disabled={loading}>Reset</button>
              <button className="btn-primary" onClick={submit} disabled={!canSubmit}>
                {loading ? 'Analyzing...' : 'Analyze MRI'}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        {/* Results */}
        {result && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 14, flex: 1, minHeight: 0 }}>
            {/* 3D Plotly Viewer */}
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 13 }}>3D Brain + Tumor</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 10, fontFamily: 'monospace' }}>Drag to rotate | Scroll to zoom</span>
              </div>
              <div style={{ flex: 1, minHeight: 520 }}>
                {hasMeshData ? (
                  <Plot
                    data={plotTraces}
                    layout={{
                      scene: {
                        xaxis: { visible: false }, yaxis: { visible: false }, zaxis: { visible: false },
                        bgcolor: '#0a1628',
                        camera: { eye: { x: 1.5, y: 1.5, z: 1.0 } },
                        aspectmode: 'data',
                      },
                      paper_bgcolor: '#0a1628',
                      margin: { l: 0, r: 0, t: 0, b: 0 },
                      showlegend: false,
                    }}
                    config={{ displayModeBar: true, displaylogo: false, responsive: true }}
                    style={{ width: '100%', height: '100%' }}
                    useResizeHandler
                  />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 8 }}>
                    <div style={{ fontSize: 48, opacity: 0.2 }}>&#9672;</div>
                    <div className="warning-box" style={{ margin: 14 }}>No mesh geometry generated — the segmentation may be empty.</div>
                  </div>
                )}
              </div>
            </div>

            {/* Stats Panel */}
            <div className="glass-card" style={{ padding: 16, overflow: 'auto' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: 10, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 14 }}>
                Segmentation Results
              </div>

              {/* Info cards */}
              <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
                {[
                  { label: 'ID', value: result.request_id?.slice(0, 12) },
                  { label: 'Time', value: `${(result.processing_time || 0).toFixed(1)}s` },
                  { label: 'Shape', value: (result.volume_shape || []).join(' x ') },
                ].map((c) => (
                  <div key={c.label} style={{ flex: 1, minWidth: 80, background: 'var(--accent-dim)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: 9, fontFamily: 'monospace', textTransform: 'uppercase' }}>{c.label}</div>
                    <div style={{ color: 'var(--accent)', fontSize: 11, fontFamily: 'monospace', fontWeight: 700, marginTop: 2 }}>{c.value}</div>
                  </div>
                ))}
              </div>

              {/* Mesh geometry info */}
              {result.meshes && (
                <div style={{ marginBottom: 14, padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'rgba(0,212,255,0.03)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 9, fontFamily: 'monospace', textTransform: 'uppercase', marginBottom: 6 }}>Mesh Geometry</div>
                  {LAYERS.map((layer) => {
                    const mesh = result.meshes[layer.key]
                    if (!mesh || !mesh.vertex_count) return null
                    return (
                      <div key={layer.key} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                        <span style={{ color: layer.color, fontSize: 11, fontFamily: 'monospace' }}>{layer.label}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: 11, fontFamily: 'monospace' }}>
                          {mesh.vertex_count.toLocaleString()} verts / {mesh.face_count.toLocaleString()} faces
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Tumor stats */}
              {LAYERS.filter(l => l.key !== 'brain').map((layer) => {
                const item = result?.stats?.[layer.key] || {}
                return (
                  <div key={layer.key} style={{
                    border: `1px solid ${layer.color}20`,
                    borderLeft: `3px solid ${layer.color}`,
                    borderRadius: 10, padding: 12, marginBottom: 10,
                    background: `${layer.color}06`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 700 }}>{layer.label}</span>
                    </div>
                    <div style={{ display: 'flex', gap: 14 }}>
                      <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>Volume: <b style={{ color: 'var(--text-primary)' }}>{(item.volume_cc || 0).toFixed(2)} cm3</b></span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>Voxels: <b style={{ color: 'var(--text-primary)' }}>{(item.voxel_count || 0).toLocaleString()}</b></span>
                    </div>
                  </div>
                )
              })}

              {/* Total tumor */}
              {result?.stats?.total_tumor && (
                <div style={{ border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, padding: 12, background: 'rgba(255,255,255,0.03)', marginTop: 8 }}>
                  <div style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 700, marginBottom: 6 }}>Total Tumor</div>
                  <div style={{ display: 'flex', gap: 14 }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>Volume: <b style={{ color: 'var(--accent)' }}>{(result.stats.total_tumor.volume_cc || 0).toFixed(2)} cm3</b></span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>Voxels: <b style={{ color: 'var(--accent)' }}>{(result.stats.total_tumor.voxel_count || 0).toLocaleString()}</b></span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
