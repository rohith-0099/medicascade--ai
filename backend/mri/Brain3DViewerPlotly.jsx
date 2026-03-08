/**
 * MediCascade 3D Brain Viewer - Plotly Version (Simpler Alternative)
 * No Three.js dependencies - uses Plotly for 3D rendering
 */

import React, { useState } from 'react';
import Plot from 'react-plotly.js';

const Brain3DViewerPlotly = () => {
  const [loading, setLoading] = useState(false);
  const [plotData, setPlotData] = useState([]);
  const [volumes, setVolumes] = useState(null);
  const [error, setError] = useState(null);
  
  // Convert backend mesh data to Plotly format
  const meshToPlotly = (meshData, color, opacity, name) => {
    if (!meshData || !meshData.vertices || !meshData.faces) {
      return null;
    }
    
    const vertices = meshData.vertices;
    const faces = meshData.faces;
    
    // Extract X, Y, Z coordinates
    const x = vertices.map(v => v[0]);
    const y = vertices.map(v => v[1]);
    const z = vertices.map(v => v[2]);
    
    // Extract face indices
    const i = faces.map(f => f[0]);
    const j = faces.map(f => f[1]);
    const k = faces.map(f => f[2]);
    
    return {
      type: 'mesh3d',
      x, y, z,
      i, j, k,
      color: color,
      opacity: opacity,
      name: name,
      lighting: {
        ambient: 0.5,
        diffuse: 0.75,
        specular: 0.35,
        roughness: 0.4,
        fresnel: 0.2
      },
      lightposition: {
        x: 150,
        y: 150,
        z: 200
      },
      flatshading: false,
      hovertemplate: `<b>${name}</b><br>` +
                     'X: %{x:.1f}<br>' +
                     'Y: %{y:.1f}<br>' +
                     'Z: %{z:.1f}<br>' +
                     '<extra></extra>'
    };
  };
  
  // File upload handler
  const handleFileUpload = async (event) => {
    const files = event.target.files;
    
    if (files.length < 2) {
      setError('Please upload both FLAIR and Segmentation files');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      
      // Identify files
      for (let file of files) {
        if (file.name.includes('flair')) {
          formData.append('flair', file);
        } else if (file.name.includes('seg')) {
          formData.append('segmentation', file);
        }
      }
      
      // Upload to backend
      const response = await fetch('http://localhost:8000/api/mri/analyze-3d', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Convert meshes to Plotly format
        const traces = [];
        
        const meshOrder = [
          { key: 'brain', name: 'Brain Cortex' },
          { key: 'edema', name: 'Edema' },
          { key: 'necrotic', name: 'Necrotic Core' },
          { key: 'enhancing', name: 'Enhancing Tumor' }
        ];
        
        meshOrder.forEach(({ key, name }) => {
          const trace = meshToPlotly(
            data.meshes[key],
            data.colors[key],
            data.opacity[key],
            name
          );
          if (trace) {
            traces.push(trace);
          }
        });
        
        setPlotData(traces);
        setVolumes(data.volumes);
      } else {
        throw new Error('Processing failed');
      }
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#0a0e27' }}>
      {/* Upload Panel */}
      <div style={{
        position: 'absolute',
        top: 20,
        left: 20,
        zIndex: 10,
        background: 'rgba(15, 20, 45, 0.9)',
        padding: '20px',
        borderRadius: '10px',
        border: '1.5px solid rgba(255, 255, 255, 0.3)',
        color: 'white',
        maxWidth: '300px'
      }}>
        <h3 style={{ margin: '0 0 15px 0', fontSize: '18px' }}>
          🧠 3D Brain Tumor Viewer
        </h3>
        
        <input
          type="file"
          multiple
          accept=".nii,.nii.gz"
          onChange={handleFileUpload}
          disabled={loading}
          style={{
            marginBottom: '10px',
            padding: '8px',
            width: '100%',
            background: '#1a2040',
            border: '1px solid #4a90e2',
            borderRadius: '5px',
            color: 'white',
            cursor: 'pointer'
          }}
        />
        
        <p style={{ fontSize: '12px', color: '#999', margin: '5px 0' }}>
          📁 Upload FLAIR + Segmentation (.nii.gz)
        </p>
        
        {loading && (
          <div style={{ marginTop: '15px', textAlign: 'center' }}>
            <div className="spinner" style={{
              border: '3px solid #1a2040',
              borderTop: '3px solid #4a90e2',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              animation: 'spin 1s linear infinite',
              margin: '0 auto'
            }} />
            <p style={{ marginTop: '10px', fontSize: '13px' }}>
              Processing MRI scan...
            </p>
          </div>
        )}
        
        {error && (
          <div style={{
            marginTop: '10px',
            padding: '10px',
            background: 'rgba(208, 2, 27, 0.2)',
            border: '1px solid #d0021b',
            borderRadius: '5px',
            fontSize: '12px',
            color: '#ff6b6b'
          }}>
            ❌ {error}
          </div>
        )}
        
        {plotData.length > 0 && (
          <div style={{
            marginTop: '15px',
            padding: '10px',
            background: 'rgba(74, 144, 226, 0.1)',
            border: '1px solid #4a90e2',
            borderRadius: '5px',
            fontSize: '12px'
          }}>
            ✅ Visualization loaded!
            <div style={{ marginTop: '8px', fontSize: '11px', color: '#aaa' }}>
              🖱️ Drag to rotate<br/>
              🔍 Scroll to zoom<br/>
              👆 Click legend to toggle layers
            </div>
          </div>
        )}
      </div>
      
      {/* Volume Stats */}
      {volumes && (
        <div style={{
          position: 'absolute',
          bottom: 20,
          right: 20,
          zIndex: 10,
          background: 'rgba(15, 20, 45, 0.9)',
          padding: '15px',
          borderRadius: '10px',
          border: '1.5px solid rgba(255, 255, 255, 0.3)',
          color: 'white',
          fontFamily: 'Courier New, monospace',
          fontSize: '11px',
          minWidth: '200px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', fontWeight: 'bold' }}>
            📊 Tissue Volumes
          </h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              <tr>
                <td style={{ padding: '4px 0', color: '#4a90e2' }}>Brain:</td>
                <td style={{ padding: '4px 0', textAlign: 'right' }}>{volumes.brain_cm3.toFixed(1)} cm³</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 0', color: '#f5a623' }}>Edema:</td>
                <td style={{ padding: '4px 0', textAlign: 'right' }}>{volumes.edema_cm3.toFixed(2)} cm³</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 0', color: '#d0021b' }}>Necrotic:</td>
                <td style={{ padding: '4px 0', textAlign: 'right' }}>{volumes.necrotic_cm3.toFixed(2)} cm³</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 0', color: '#ff6b35' }}>Enhancing:</td>
                <td style={{ padding: '4px 0', textAlign: 'right' }}>{volumes.enhancing_cm3.toFixed(2)} cm³</td>
              </tr>
              <tr style={{ borderTop: '1px solid rgba(255,255,255,0.2)' }}>
                <td style={{ padding: '8px 0 4px 0', fontWeight: 'bold' }}>Total Tumor:</td>
                <td style={{ padding: '8px 0 4px 0', textAlign: 'right', fontWeight: 'bold' }}>
                  {volumes.total_tumor_cm3.toFixed(2)} cm³
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      
      {/* 3D Plot */}
      {plotData.length > 0 && (
        <Plot
          data={plotData}
          layout={{
            title: {
              text: '<b>3D Brain Tumor Segmentation</b>',
              font: { color: 'white', size: 20, family: 'Arial' },
              x: 0.5,
              xanchor: 'center'
            },
            paper_bgcolor: '#0a0e27',
            plot_bgcolor: '#0a0e27',
            scene: {
              bgcolor: '#0a0e27',
              xaxis: {
                visible: false,
                showbackground: false,
                showgrid: false,
                zeroline: false
              },
              yaxis: {
                visible: false,
                showbackground: false,
                showgrid: false,
                zeroline: false
              },
              zaxis: {
                visible: false,
                showbackground: false,
                showgrid: false,
                zeroline: false
              },
              camera: {
                eye: { x: 1.6, y: 1.6, z: 1.3 },
                center: { x: 0, y: 0, z: 0 },
                up: { x: 0, y: 0, z: 1 }
              },
              aspectmode: 'data'
            },
            legend: {
              font: { color: 'white', size: 13, family: 'Arial' },
              bgcolor: 'rgba(15, 20, 45, 0.85)',
              bordercolor: 'rgba(255, 255, 255, 0.3)',
              borderwidth: 1.5,
              x: 0.02,
              y: 0.98,
              xanchor: 'left',
              yanchor: 'top'
            },
            margin: { l: 0, r: 0, t: 60, b: 0 },
            autosize: true,
            modebar: {
              bgcolor: 'rgba(15, 20, 45, 0.8)',
              color: 'white',
              activecolor: '#4a90e2'
            }
          }}
          config={{
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['select2d', 'lasso2d'],
            toImageButtonOptions: {
              format: 'png',
              filename: 'brain_tumor_3d',
              height: 1200,
              width: 1600,
              scale: 2
            }
          }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      )}
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Brain3DViewerPlotly;
