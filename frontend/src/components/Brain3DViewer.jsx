/**
 * MediCascade 3D Brain Tumor Viewer - React Component
 * Interactive 3D visualization with 360° rotation and zoom
 */

import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const Brain3DViewer = () => {
  const [loading, setLoading] = useState(false);
  const [meshData, setMeshData] = useState(null);
  const [volumes, setVolumes] = useState(null);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  
  // File upload handler
  const handleFileUpload = async (event) => {
    const files = event.target.files;
    
    if (files.length < 2) {
      setError('Please upload both FLAIR and Segmentation files');
      return;
    }
    
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    
    try {
      const formData = new FormData();
      
      // Identify which file is which based on filename
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
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setMeshData(data.meshes);
        setVolumes(data.volumes);
        
        // Render 3D scene
        render3DScene(data.meshes, data.colors, data.opacity);
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
  
  // Initialize Three.js scene
  useEffect(() => {
    if (!mountRef.current) return;
    
    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0e27); // Dark background
    sceneRef.current = scene;
    
    // Camera
    const camera = new THREE.PerspectiveCamera(
      50,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      2000
    );
    camera.position.set(200, 200, 300);
    cameraRef.current = camera;
    
    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;
    
    // Lighting - Professional medical lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight1.position.set(150, 150, 200);
    scene.add(directionalLight1);
    
    const directionalLight2 = new THREE.DirectionalLight(0x8899ff, 0.3);
    directionalLight2.position.set(-100, -100, -150);
    scene.add(directionalLight2);
    
    // Orbit controls - 360° rotation + zoom
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.enablePan = true;
    controls.minDistance = 50;
    controls.maxDistance = 800;
    controls.autoRotate = false; // Set to true for auto-rotation
    controls.autoRotateSpeed = 1.0;
    controlsRef.current = controls;
    
    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();
    
    // Handle window resize
    const handleResize = () => {
      if (!mountRef.current) return;
      
      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);
  
  // Render 3D meshes from backend data
  const render3DScene = (meshes, colors, opacity) => {
    const scene = sceneRef.current;
    
    // Clear existing meshes (but keep lights)
    const toRemove = [];
    scene.children.forEach(child => {
      if (!(child instanceof THREE.Light)) {
        toRemove.push(child);
      }
    });
    
    toRemove.forEach(object => {
      if (object.geometry) object.geometry.dispose();
      if (object.material) object.material.dispose();
      scene.remove(object);
    });
    
    // Helper to create mesh from backend data
    const createMesh = (data, color, opacity, name) => {
      if (!data || !data.vertices || !data.faces) {
        console.warn(`${name}: No mesh data`);
        return null;
      }
      
      const vertices = new Float32Array(data.vertices.flat());
      const indices = new Uint32Array(data.faces.flat());
      
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
      geometry.setIndex(new THREE.BufferAttribute(indices, 1));
      geometry.computeVertexNormals(); // Critical for smooth shading!
      
      const material = new THREE.MeshPhongMaterial({
        color: new THREE.Color(color),
        transparent: true,
        opacity: opacity,
        side: THREE.DoubleSide,
        flatShading: false, // Smooth shading
        shininess: 30,
        specular: new THREE.Color(0x333333)
      });
      
      const mesh = new THREE.Mesh(geometry, material);
      mesh.name = name;
      
      return mesh;
    };
    
    // Center all meshes
    const centerOffset = new THREE.Vector3(-120, -120, -77.5);
    
    // Add meshes in order: brain first (back), then tumors (front)
    const meshOrder = [
      { key: 'brain', name: 'Brain Cortex' },
      { key: 'edema', name: 'Edema' },
      { key: 'necrotic', name: 'Necrotic Core' },
      { key: 'enhancing', name: 'Enhancing Tumor' }
    ];
    
    meshOrder.forEach(({ key, name }) => {
      const mesh = createMesh(
        meshes[key],
        colors[key],
        opacity[key],
        name
      );
      
      if (mesh) {
        mesh.position.copy(centerOffset);
        scene.add(mesh);
        console.log(`Added ${name}: ${meshes[key].vertex_count} vertices`);
      }
    });
    
    // Reset camera to view all
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };
  
  // Toggle structure visibility
  const toggleStructure = (structureName) => {
    const scene = sceneRef.current;
    const mesh = scene.getObjectByName(structureName);
    if (mesh) {
      mesh.visible = !mesh.visible;
    }
  };
  
  // Reset camera
  const resetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };
  
  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative' }}>
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
          3D Brain Tumor Viewer
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
            color: 'white'
          }}
        />
        
        <p style={{ fontSize: '12px', color: '#999', margin: '5px 0' }}>
          Upload FLAIR + Segmentation files (.nii.gz)
        </p>
        
        {loading && (
          <div style={{ marginTop: '10px' }}>
            <p>Processing... {uploadProgress}%</p>
            <div style={{
              width: '100%',
              height: '6px',
              background: '#1a2040',
              borderRadius: '3px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                background: '#4a90e2',
                transition: 'width 0.3s'
              }} />
            </div>
          </div>
        )}
        
        {error && (
          <div style={{
            marginTop: '10px',
            padding: '10px',
            background: '#d0021b',
            borderRadius: '5px',
            fontSize: '12px'
          }}>
            {error}
          </div>
        )}
      </div>
      
      {/* Volume Stats Panel */}
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
          fontFamily: 'monospace',
          fontSize: '11px'
        }}>
          <h4 style={{ margin: '0 0 10px 0' }}>Tissue Volumes</h4>
          <div>Brain: {volumes.brain_cm3.toFixed(1)} cm³</div>
          <div>Necrotic: {volumes.necrotic_cm3.toFixed(2)} cm³</div>
          <div>Edema: {volumes.edema_cm3.toFixed(2)} cm³</div>
          <div>Enhancing: {volumes.enhancing_cm3.toFixed(2)} cm³</div>
          <div style={{ marginTop: '8px', fontWeight: 'bold' }}>
            Total Tumor: {volumes.total_tumor_cm3.toFixed(2)} cm³
          </div>
        </div>
      )}
      
      {/* Controls Panel */}
      {meshData && (
        <div style={{
          position: 'absolute',
          top: 20,
          right: 20,
          zIndex: 10,
          background: 'rgba(15, 20, 45, 0.9)',
          padding: '15px',
          borderRadius: '10px',
          border: '1.5px solid rgba(255, 255, 255, 0.3)',
          color: 'white'
        }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Controls</h4>
          
          <div style={{ fontSize: '12px', marginBottom: '10px' }}>
            <div>🖱️ Left drag: Rotate</div>
            <div>🖱️ Right drag: Pan</div>
            <div>🖱️ Scroll: Zoom</div>
          </div>
          
          <button
            onClick={resetCamera}
            style={{
              padding: '8px 15px',
              background: '#4a90e2',
              border: 'none',
              borderRadius: '5px',
              color: 'white',
              cursor: 'pointer',
              width: '100%',
              marginBottom: '8px'
            }}
          >
            Reset Camera
          </button>
          
          <div style={{ marginTop: '10px' }}>
            <h5 style={{ fontSize: '12px', margin: '5px 0' }}>Toggle Layers:</h5>
            {['Brain Cortex', 'Edema', 'Necrotic Core', 'Enhancing Tumor'].map(name => (
              <label key={name} style={{
                display: 'block',
                fontSize: '11px',
                cursor: 'pointer',
                marginBottom: '4px'
              }}>
                <input
                  type="checkbox"
                  defaultChecked
                  onChange={() => toggleStructure(name)}
                  style={{ marginRight: '6px' }}
                />
                {name}
              </label>
            ))}
          </div>
        </div>
      )}
      
      {/* 3D Canvas */}
      <div
        ref={mountRef}
        style={{
          width: '100%',
          height: '100%',
          background: '#0a0e27'
        }}
      />
    </div>
  );
};

export default Brain3DViewer;
