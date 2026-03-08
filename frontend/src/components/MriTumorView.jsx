import { Suspense, useEffect, useMemo, useState } from 'react'
import { Bounds, OrbitControls, useGLTF } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { Color, DoubleSide } from 'three'

const MODALITIES = [
  { key: 't1', label: 'T1' },
  { key: 't1ce', label: 'T1ce (contrast)' },
  { key: 't2', label: 'T2' },
  { key: 'flair', label: 'FLAIR' },
]

const LAYERS = [
  { key: 'brain', label: 'Brain' },
  { key: 'necrotic', label: 'Necrotic Core' },
  { key: 'edema', label: 'Edema' },
  { key: 'enhancing', label: 'Enhancing Tumor' },
]

export default function MriTumorView({ onBack }) {
  const [files, setFiles] = useState({ t1: null, t1ce: null, t2: null, flair: null })
  const [layerVisible, setLayerVisible] = useState({
    brain: true,
    necrotic: true,
    edema: true,
    enhancing: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const canSubmit = MODALITIES.every((m) => files[m.key]) && !loading
  const hasViewerData = Boolean(
    result &&
      Object.values(result.meshes || {}).some((url) => typeof url === 'string' && url.trim().length > 0),
  )

  const handleFileChange = (modality, file) => {
    setFiles((prev) => ({ ...prev, [modality]: file || null }))
  }

  const submit = async () => {
    if (!canSubmit) return

    setLoading(true)
    setError('')
    setResult(null)

    const form = new FormData()
    MODALITIES.forEach((m) => {
      form.append(m.key, files[m.key])
    })

    try {
      const res = await fetch('/api/mri/analyze', { method: 'POST', body: form })
      if (!res.ok) {
        let detail = `API error ${res.status}`
        try {
          const err = await res.json()
          if (err?.detail) detail = err.detail
        } catch {
          // Keep generic API message.
        }
        throw new Error(detail)
      }
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setError(e.message || 'MRI analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  const resetAll = () => {
    setFiles({ t1: null, t1ce: null, t2: null, flair: null })
    setError('')
    setResult(null)
    setLoading(false)
    setLayerVisible({ brain: true, necrotic: true, edema: true, enhancing: true })
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
            <div className="sidebar-subtitle">MRI 3D Tumor Mode</div>
          </div>
        </div>

        <div className="sidebar-section">Layers</div>
        {LAYERS.map((layer) => (
          <label
            key={layer.key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              marginBottom: 8,
              border: '1px solid var(--border)',
              borderRadius: 10,
              padding: 10,
            }}
          >
            <input
              type="checkbox"
              checked={layerVisible[layer.key]}
              onChange={(e) => setLayerVisible((prev) => ({ ...prev, [layer.key]: e.target.checked }))}
            />
            <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{layer.label}</span>
          </label>
        ))}

        <button className="btn-secondary" onClick={onBack} style={{ width: '100%', marginTop: 14 }}>
          Back To Clinical
        </button>
      </aside>

      <main style={{ flex: 1, padding: '28px 34px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="page-header">
          <h1 className="page-title">Brain MRI 3D Tumor View</h1>
          <p className="page-description">
            Upload the 4 MRI modalities (T1, T1ce, T2, FLAIR) to generate 3D tumor meshes.
          </p>
        </div>

        <div className="glass-card" style={{ border: '1px solid var(--border)', padding: 18 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
            {MODALITIES.map((modality) => (
              <div key={modality.key} style={{ border: '1px solid var(--border)', borderRadius: 10, padding: 10 }}>
                <div
                  style={{
                    color: 'var(--text-muted)',
                    fontSize: 11,
                    textTransform: 'uppercase',
                    letterSpacing: '0.07em',
                    marginBottom: 6,
                  }}
                >
                  {modality.label}
                </div>
                <input
                  type="file"
                  accept=".nii,.nii.gz,application/gzip"
                  onChange={(e) => handleFileChange(modality.key, e.target.files?.[0] || null)}
                  style={{ width: '100%', color: 'var(--text-secondary)', fontSize: 12 }}
                />
                {files[modality.key] && (
                  <div style={{ color: 'var(--accent-light)', fontSize: 11, marginTop: 6 }}>{files[modality.key].name}</div>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 14 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              {loading ? 'Running 3D segmentation...' : 'Upload all 4 modalities to begin.'}
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-secondary" onClick={resetAll} disabled={loading}>
                Reset
              </button>
              <button className="btn-primary" onClick={submit} disabled={!canSubmit}>
                {loading ? 'Analyzing' : 'Analyze MRI'}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        {result && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 14 }}>
            <div className="glass-card" style={{ border: '1px solid var(--border)', padding: 12 }}>
              <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: 8 }}>3D Brain + Tumor Mesh</div>
              <div style={{ height: 520, borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border)' }}>
                {hasViewerData ? (
                  <MriScene meshes={result.meshes || {}} visibleLayers={layerVisible} />
                ) : (
                  <div className="warning-box" style={{ margin: 14 }}>
                    No mesh geometry generated. This can happen when the predicted mask is empty.
                  </div>
                )}
              </div>
            </div>

            <div className="glass-card" style={{ border: '1px solid var(--border)', padding: 14 }}>
              <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: 10 }}>Segmentation Stats</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 10 }}>
                Request ID: <span style={{ color: 'var(--accent-light)' }}>{result.request_id}</span>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 16 }}>
                Processing time: {(result.processing_time || 0).toFixed(2)}s
              </div>

              {['necrotic', 'edema', 'enhancing'].map((label) => {
                const item = result?.stats?.[label] || {}
                return (
                  <div
                    key={label}
                    style={{
                      border: '1px solid var(--border)',
                      borderRadius: 10,
                      padding: 10,
                      marginBottom: 10,
                      background: 'var(--bg-hover)',
                    }}
                  >
                    <div style={{ color: 'var(--text-primary)', fontSize: 12, fontWeight: 700, textTransform: 'capitalize' }}>{label}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 4 }}>
                      Volume: {(item.volume_cc || 0).toFixed(3)} cc
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                      Confidence: {Math.round((item.confidence || 0) * 100)}%
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                      Voxels: {Math.round(item.voxel_count || 0)}
                    </div>
                  </div>
                )
              })}

              <div style={{ borderTop: '1px solid var(--border)', marginTop: 12, paddingTop: 12 }}>
                <div style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
                  Mesh Files
                </div>
                {Object.entries(result.meshes || {}).map(([name, url]) => (
                  <div key={name} style={{ marginBottom: 6 }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 12, textTransform: 'capitalize' }}>{name}: </span>
                    {url ? (
                      <a href={url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-light)', fontSize: 12 }}>
                        {url}
                      </a>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>No mesh generated</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function MriScene({ meshes, visibleLayers }) {
  return (
    <Canvas camera={{ position: [140, 110, 140], fov: 45 }}>
      <color attach="background" args={['#020617']} />
      <ambientLight intensity={0.95} />
      <directionalLight position={[120, 160, 80]} intensity={1.2} />
      <directionalLight position={[-120, -100, -80]} intensity={0.4} />

      <Suspense fallback={null}>
        <Bounds fit clip observe margin={1.2}>
          {meshes.brain && visibleLayers.brain && (
            <GltfLayer url={meshes.brain} opacity={0.4} color="#d9e6f2" emissiveIntensity={0.08} />
          )}
          {meshes.necrotic && visibleLayers.necrotic && <GltfLayer url={meshes.necrotic} opacity={0.92} />}
          {meshes.edema && visibleLayers.edema && <GltfLayer url={meshes.edema} opacity={0.8} />}
          {meshes.enhancing && visibleLayers.enhancing && <GltfLayer url={meshes.enhancing} opacity={0.94} />}
        </Bounds>
      </Suspense>

      <OrbitControls makeDefault />
    </Canvas>
  )
}

function GltfLayer({ url, opacity, color = '', emissiveIntensity = 0 }) {
  const { scene } = useGLTF(url)
  const cloned = useMemo(() => scene.clone(true), [scene])

  useEffect(() => {
    const tint = color ? new Color(color) : null

    cloned.traverse((node) => {
      if (node.isMesh && node.material) {
        if (Array.isArray(node.material)) {
          node.material = node.material.map((m) => {
            const copy = m.clone()
            copy.transparent = opacity < 0.999
            copy.opacity = opacity
            copy.depthWrite = opacity >= 0.999
            copy.side = DoubleSide
            if (tint && copy.color) {
              copy.vertexColors = false
              copy.color.copy(tint)
            }
            if (tint && copy.emissive) {
              copy.emissive.copy(tint).multiplyScalar(emissiveIntensity)
            }
            return copy
          })
        } else {
          const mat = node.material.clone()
          mat.transparent = opacity < 0.999
          mat.opacity = opacity
          mat.depthWrite = opacity >= 0.999
          mat.side = DoubleSide
          if (tint && mat.color) {
            mat.vertexColors = false
            mat.color.copy(tint)
          }
          if (tint && mat.emissive) {
            mat.emissive.copy(tint).multiplyScalar(emissiveIntensity)
          }
          node.material = mat
        }
      }
    })
  }, [cloned, color, emissiveIntensity, opacity])

  return <primitive object={cloned} />
}
