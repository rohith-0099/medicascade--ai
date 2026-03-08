"""
MediCascade Backend - 3D Brain Tumor Visualization API
FastAPI endpoint for processing uploaded MRI scans and generating 3D meshes
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import nibabel as nib
from skimage import measure
from scipy import ndimage
import tempfile
import os
import json
from typing import List, Dict, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MediCascade 3D Visualization API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
#                        ADVANCED BRAIN EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_brain_advanced(flair: np.ndarray) -> np.ndarray:
    """
    Multi-method brain extraction with heavy smoothing for perfect surface.
    """
    logger.info("Starting advanced brain extraction...")
    
    non_zero = flair[flair > 0]
    if len(non_zero) == 0:
        raise ValueError("Empty FLAIR volume")
    
    # Method 1: Very conservative percentile threshold
    threshold = np.percentile(non_zero, 2)  # 2nd percentile
    brain_mask = flair > threshold
    
    if brain_mask.sum() < 1000:
        logger.warning("Low voxel count, using fallback threshold")
        brain_mask = flair > (flair.max() * 0.005)
    
    # CRITICAL: Pre-smooth the binary mask before any morphology
    logger.info("Pre-smoothing mask (σ=4.0)...")
    brain_float = ndimage.gaussian_filter(brain_mask.astype(np.float32), sigma=4.0)
    brain_mask = brain_float > 0.25
    
    # Large-scale closing to fill ventricles/sulci
    logger.info("Morphological closing...")
    brain_mask = ndimage.binary_closing(brain_mask, structure=np.ones((9,9,9)))
    brain_mask = ndimage.binary_fill_holes(brain_mask)
    
    # Keep largest component only
    labeled, num_features = ndimage.label(brain_mask)
    if num_features > 1:
        sizes = ndimage.sum(brain_mask, labeled, range(1, num_features + 1))
        brain_mask = (labeled == (np.argmax(sizes) + 1))
    
    # Smooth morphology: erode then dilate more
    brain_mask = ndimage.binary_erosion(brain_mask, iterations=3)
    brain_mask = ndimage.binary_dilation(brain_mask, iterations=6)
    brain_mask = ndimage.binary_fill_holes(brain_mask)
    
    # Final ultra-smooth pass
    logger.info("Final smoothing pass (σ=3.0)...")
    brain_float = ndimage.gaussian_filter(brain_mask.astype(np.float32), sigma=3.0)
    brain_mask = brain_float > 0.4
    
    logger.info(f"Brain extracted: {brain_mask.sum():,} voxels")
    return brain_mask.astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
#                        ULTRA-SMOOTH MESH GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def laplacian_smooth_optimized(vertices: np.ndarray, 
                               faces: np.ndarray,
                               iterations: int = 20,
                               lambda_factor: float = 0.65) -> np.ndarray:
    """
    Optimized Laplacian smoothing with numpy vectorization.
    """
    vertices = vertices.copy()
    n_verts = len(vertices)
    
    # Build adjacency using sparse operations
    adjacency = [set() for _ in range(n_verts)]
    for face in faces:
        for i in range(3):
            v1, v2 = face[i], face[(i + 1) % 3]
            adjacency[v1].add(v2)
            adjacency[v2].add(v1)
    
    # Vectorized smoothing
    for iteration in range(iterations):
        new_vertices = vertices.copy()
        for i in range(n_verts):
            if len(adjacency[i]) > 0:
                neighbors = np.array(list(adjacency[i]))
                centroid = vertices[neighbors].mean(axis=0)
                new_vertices[i] = vertices[i] + lambda_factor * (centroid - vertices[i])
        vertices = new_vertices
        
        if (iteration + 1) % 5 == 0:
            logger.info(f"   Smoothing iteration {iteration + 1}/{iterations}")
    
    return vertices


def create_mesh_ultra_smooth(mask: np.ndarray,
                             step_size: int = 2,
                             gaussian_sigma: float = 3.5,
                             laplacian_iterations: int = 20,
                             structure_name: str = "Structure") -> Optional[Dict]:
    """
    Generate ultra-smooth 3D mesh from binary mask.
    
    Returns:
        Dict with 'vertices' (Nx3) and 'faces' (Mx3), or None if failed
    """
    voxel_count = mask.sum()
    
    if voxel_count == 0:
        logger.warning(f"{structure_name}: Empty mask, skipping")
        return None
    
    logger.info(f"Creating mesh for {structure_name} ({voxel_count:,} voxels)")
    
    # Downsample
    if step_size > 1:
        small = ndimage.zoom(mask.astype(np.float32), 1/step_size, order=1)
    else:
        small = mask.astype(np.float32)
    
    # Heavy Gaussian + median filtering
    logger.info(f"   Gaussian smoothing (σ={gaussian_sigma})...")
    small = ndimage.gaussian_filter(small, sigma=gaussian_sigma)
    small = ndimage.median_filter(small, size=3)
    
    if small.max() == 0:
        logger.error(f"{structure_name}: Lost after smoothing")
        return None
    
    # Marching cubes
    try:
        logger.info("   Running marching cubes...")
        verts, faces, normals, values = measure.marching_cubes(
            small,
            level=0.5,
            step_size=1,
            allow_degenerate=False
        )
        
        # Scale back
        verts = verts * step_size
        
        logger.info(f"   Generated {len(verts):,} vertices, {len(faces):,} faces")
        
        # Ultra-aggressive Laplacian smoothing
        if laplacian_iterations > 0:
            logger.info(f"   Laplacian smoothing ({laplacian_iterations} iterations)...")
            verts = laplacian_smooth_optimized(verts, faces, 
                                              iterations=laplacian_iterations,
                                              lambda_factor=0.65)
        
        logger.info(f"   ✓ {structure_name} mesh complete")
        
        return {
            'vertices': verts.tolist(),
            'faces': faces.tolist(),
            'vertex_count': len(verts),
            'face_count': len(faces)
        }
        
    except Exception as e:
        logger.error(f"{structure_name} mesh failed: {str(e)}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#                            API ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/mri/analyze-3d")
async def analyze_mri_3d(
    flair: UploadFile = File(..., description="FLAIR NIfTI file (.nii.gz)"),
    segmentation: UploadFile = File(..., description="Segmentation NIfTI file (.nii.gz)")
):
    """
    Process uploaded MRI files and return 3D mesh data for visualization.
    
    Request:
        - flair: FLAIR MRI scan (.nii.gz)
        - segmentation: Tumor segmentation mask (.nii.gz)
    
    Response:
        {
            "brain": { "vertices": [...], "faces": [...] },
            "necrotic": { "vertices": [...], "faces": [...] },
            "edema": { "vertices": [...], "faces": [...] },
            "enhancing": { "vertices": [...], "faces": [...] },
            "volumes": { "brain": 1200.5, "necrotic": 5.2, ... },
            "metadata": { "patient_id": "...", "processing_time": 45.2 }
        }
    """
    
    import time
    start_time = time.time()
    
    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Processing uploaded MRI files in {tmpdir}")
            
            # Save uploaded files
            flair_path = os.path.join(tmpdir, "flair.nii.gz")
            seg_path = os.path.join(tmpdir, "seg.nii.gz")
            
            with open(flair_path, "wb") as f:
                content = await flair.read()
                f.write(content)
            
            with open(seg_path, "wb") as f:
                content = await segmentation.read()
                f.write(content)
            
            logger.info("Files saved, loading NIfTI data...")
            
            # Load NIfTI files
            flair_nii = nib.load(flair_path)
            seg_nii = nib.load(seg_path)
            
            flair_data = flair_nii.get_fdata()
            seg_data = seg_nii.get_fdata()
            voxel_dims = flair_nii.header.get_zooms()[:3]
            
            logger.info(f"Loaded volumes: {flair_data.shape}, voxel size: {voxel_dims}")
            
            # Extract brain mask
            brain_mask = extract_brain_advanced(flair_data)
            
            # Extract tumor regions
            necrotic_mask = (seg_data == 1).astype(np.uint8)
            edema_mask = (seg_data == 2).astype(np.uint8)
            enhancing_mask = (seg_data == 4).astype(np.uint8)
            
            # Calculate volumes (mm³ and cm³)
            voxel_volume = np.prod(voxel_dims)
            volumes = {
                'brain_mm3': float(brain_mask.sum() * voxel_volume),
                'brain_cm3': float(brain_mask.sum() * voxel_volume / 1000),
                'necrotic_mm3': float(necrotic_mask.sum() * voxel_volume),
                'necrotic_cm3': float(necrotic_mask.sum() * voxel_volume / 1000),
                'edema_mm3': float(edema_mask.sum() * voxel_volume),
                'edema_cm3': float(edema_mask.sum() * voxel_volume / 1000),
                'enhancing_mm3': float(enhancing_mask.sum() * voxel_volume),
                'enhancing_cm3': float(enhancing_mask.sum() * voxel_volume / 1000),
                'total_tumor_mm3': float((seg_data > 0).sum() * voxel_volume),
                'total_tumor_cm3': float((seg_data > 0).sum() * voxel_volume / 1000),
            }
            
            logger.info(f"Volumes calculated: {volumes}")
            
            # Generate meshes with optimized parameters per structure
            logger.info("\n" + "="*70)
            logger.info("GENERATING 3D MESHES")
            logger.info("="*70)
            
            meshes = {}
            
            # Brain: Maximum smoothness, can downsample heavily
            meshes['brain'] = create_mesh_ultra_smooth(
                brain_mask,
                step_size=6,              # Heavy downsampling for speed
                gaussian_sigma=4.0,       # Maximum smoothing
                laplacian_iterations=20,  # Maximum smoothing passes
                structure_name="Brain Cortex"
            )
            
            # Edema: Moderate quality
            meshes['edema'] = create_mesh_ultra_smooth(
                edema_mask,
                step_size=2,
                gaussian_sigma=2.5,
                laplacian_iterations=15,
                structure_name="Edema"
            )
            
            # Necrotic: High detail (smaller structure)
            meshes['necrotic'] = create_mesh_ultra_smooth(
                necrotic_mask,
                step_size=1,
                gaussian_sigma=2.0,
                laplacian_iterations=15,
                structure_name="Necrotic Core"
            )
            
            # Enhancing: Highest detail
            meshes['enhancing'] = create_mesh_ultra_smooth(
                enhancing_mask,
                step_size=1,
                gaussian_sigma=2.0,
                laplacian_iterations=15,
                structure_name="Enhancing Tumor"
            )
            
            processing_time = time.time() - start_time
            logger.info(f"\n✓ Processing complete in {processing_time:.1f} seconds")
            
            # Prepare response
            response = {
                "success": True,
                "meshes": {
                    "brain": meshes.get('brain'),
                    "edema": meshes.get('edema'),
                    "necrotic": meshes.get('necrotic'),
                    "enhancing": meshes.get('enhancing'),
                },
                "volumes": volumes,
                "metadata": {
                    "volume_shape": list(flair_data.shape),
                    "voxel_dimensions": list(voxel_dims),
                    "processing_time_seconds": round(processing_time, 2),
                    "flair_filename": flair.filename,
                    "seg_filename": segmentation.filename
                },
                "colors": {
                    "brain": "#4a90e2",
                    "edema": "#f5a623",
                    "necrotic": "#d0021b",
                    "enhancing": "#ff6b35"
                },
                "opacity": {
                    "brain": 0.15,
                    "edema": 0.50,
                    "necrotic": 0.75,
                    "enhancing": 0.80
                }
            }
            
            return JSONResponse(content=response)
            
    except Exception as e:
        logger.error(f"Error processing MRI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "MediCascade 3D Visualization"}


@app.get("/")
async def root():
    """API info."""
    return {
        "service": "MediCascade 3D Brain Tumor Visualization API",
        "version": "1.0.0",
        "endpoints": {
            "/api/mri/analyze-3d": "POST - Upload MRI files for 3D visualization",
            "/api/health": "GET - Health check",
            "/docs": "GET - Swagger documentation"
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
#                            RUN SERVER
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         MediCascade 3D Visualization Backend API              ║
    ║                                                                ║
    ║  Starting server on http://localhost:8000                      ║
    ║  API docs: http://localhost:8000/docs                          ║
    ║                                                                ║
    ║  Ready to process MRI uploads and generate 3D meshes!          ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # Auto-reload on code changes (disable in production)
    )
