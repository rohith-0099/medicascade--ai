import os
import shutil
import time
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Optional, Dict

import numpy as np
import nibabel as nib
from skimage import measure
from scipy import ndimage
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from layers.layer0_pdf_processor import layer0_processor
from layers.layer1_specialists import layer1_specialists
from layers.layer2_validator import layer2_validator
from layers.layer3_annotator import layer3_annotator
from mri.mesh_export import export_mesh_bundle
from mri.predict import get_predictor
from mri.preprocess import DEFAULT_TARGET_SHAPE, load_and_preprocess_modalities
from schemas import MriAnalyzeResponse

app = FastAPI(
    title="MediCascade AI — Multi-Layer Clinical Intake",
    description="Layered pipeline: PDF → structured facts → specialists → evidence validation → annotated report.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(settings.OUTPUT_DIR):
    app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")


MODEL_PATH = Path(__file__).resolve().parent / "kagglemodel" / "best_model.pth"


# ═══════════════════════════════════════════════════════════════════════════════
#                        3D BRAIN VISUALIZATION - HELPER FUNCTIONS
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
    
    # Normalize to 0-1 range for marching cubes
    data_min = small.min()
    data_max = small.max()
    if data_max > data_min:
        small = (small - data_min) / (data_max - data_min)
    
    # Marching cubes
    try:
        logger.info("   Running marching cubes...")
        # Use threshold at 0.5 for normalized 0-1 data
        threshold = 0.5 if data_max > 0 else small.max() / 2
        verts, faces, normals, values = measure.marching_cubes(
            small,
            level=threshold,
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


@app.get("/")
async def root():
    return {
        "message": "MediCascade API running",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": {
            "validator": settings.OPENROUTER_VALIDATOR_MODEL,
            "text_specialist": settings.GROQ_MODEL,
            "vision": settings.HF_VISION_MODEL,
        },
        "storage": {
            "uploads": settings.UPLOAD_DIR,
            "cases": settings.CASE_DIR,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/diagnose")
async def diagnose(file: UploadFile = File(...), scan: UploadFile = File(None)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    start_time = time.time()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    upload_path = os.path.join(settings.UPLOAD_DIR, f"{int(start_time)}_{file.filename}")
    scan_path = None

    def format_url(path: str) -> str:
        if not path:
            return ""
        clean_path = path.replace("\\", "/")
        # Serve generated files through /outputs mount
        if clean_path.startswith("outputs/"):
            return "/" + clean_path
        marker = "/outputs/"
        if marker in clean_path:
            return clean_path[clean_path.index(marker):]
        return "/" + clean_path

    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        if scan:
            from pathlib import Path

            ext = Path(scan.filename).suffix
            scan_path = os.path.join(settings.UPLOAD_DIR, f"scan_{int(time.time())}{ext}")
            with open(scan_path, "wb") as buffer:
                shutil.copyfileobj(scan.file, buffer)

        # Layer 0 — deterministic intake
        layer0 = layer0_processor.process(upload_path, scan_path)

        # Layer 1 — specialists
        layer1 = layer1_specialists.process(layer0.case)

        # Layer 2 — evidence validator
        layer2 = layer2_validator.process(layer0.case, layer1)

        # Layer 3 — annotated PDF
        layer3 = layer3_annotator.process(layer0.case, layer1, layer2)

        total_elapsed = time.time() - start_time

        response = {
            "success": True,
            "case_id": layer0.case.case_id,
            "primary_diagnosis": layer2.primary_diagnosis,
            "confidence": layer2.confidence,
            "processing_time": total_elapsed,
            "evidence_items_count": len(layer2.evidence_pack),
            "specialist_views_count": len(layer1.views),
            "xai_summary": (layer3.explanation_text or "")[:4000],
            "artifacts": {
                "case_json": format_url(layer0.case_json_path),
                "layer1_findings": format_url(layer1.findings_json_path),
                "final_assessment": format_url(layer2.final_assessment_path),
                "report_pdf": format_url(layer3.annotated_pdf_path),
                "images_dir": format_url(layer0.images_dir),
            },
            "data_flow_trace": [
                {
                    "layer": "Layer 0",
                    "input": "patient PDF",
                    "output": "case.json + provenance + images",
                    "status": "completed",
                },
                {
                    "layer": "Layer 1",
                    "input": "case.json",
                    "output": "layer1_findings.json",
                    "status": "completed",
                },
                {
                    "layer": "Layer 2",
                    "input": "layer1_findings + external evidence",
                    "output": "final_assessment.json",
                    "status": "completed",
                },
                {
                    "layer": "Layer 3",
                    "input": "final_assessment + highlight targets",
                    "output": f"MediCascade_Report_{layer0.case.case_id}.pdf",
                    "status": "completed",
                },
            ],
            "layer1_findings": {
                "candidate_diagnoses": layer1.candidate_diagnoses,
                "red_flags": layer1.red_flags,
                "abnormal_labs": layer1.abnormal_labs,
                "symptom_timeline": layer1.symptom_timeline,
                "risk_factors": layer1.risk_factors,
            },
            "final_assessment": {
                "final_problem_list": layer2.final_problem_list,
                "final_differentials": layer2.final_differentials,
                "final_red_flags": layer2.final_red_flags,
                "supported_findings": layer2.supported_findings,
                "uncertain_findings": layer2.uncertain_findings,
                "contradicted_findings": layer2.contradicted_findings,
                "missing_data": layer2.missing_data,
                "evidence_pack": [e.model_dump(mode="json") for e in layer2.evidence_pack],
                "highlight_targets": [h.model_dump(mode="json") for h in layer2.highlight_targets],
            },
            "layer1_views": [
                {
                    "agent": v.agent,
                    "role": v.role,
                    "confidence": v.confidence,
                    "findings": v.findings,
                }
                for v in layer1.views
            ],
            "evidence_count": len(layer3.evidence_items),
            "total_processing_time": total_elapsed,
        }
        return response

    except Exception as e:
        print(f"[API ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")


def _is_nifti_file(filename: str) -> bool:
    lower = filename.lower()
    return lower.endswith(".nii") or lower.endswith(".nii.gz")


@app.post("/api/mri/analyze", response_model=MriAnalyzeResponse)
async def analyze_mri(
    t1: UploadFile = File(...),
    t1ce: UploadFile = File(...),
    t2: UploadFile = File(...),
    flair: UploadFile = File(...),
):
    start_time = time.time()
    request_id = f"{int(start_time)}_{uuid4().hex[:6]}"
    upload_dir = Path(settings.UPLOAD_DIR) / "mri" / request_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploads = {"t1": t1, "t1ce": t1ce, "t2": t2, "flair": flair}
    saved_paths: dict[str, Path] = {}

    try:
        for modality, upload in uploads.items():
            filename = upload.filename or ""
            if not _is_nifti_file(filename):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid file for {modality.upper()}. "
                        "Only NIfTI files (.nii or .nii.gz) are accepted."
                    ),
                )

            ext = ".nii.gz" if filename.lower().endswith(".nii.gz") else ".nii"
            path = upload_dir / f"{modality}{ext}"
            with path.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)
            saved_paths[modality] = path

        preprocessed = load_and_preprocess_modalities(
            file_paths=saved_paths,
            target_shape=DEFAULT_TARGET_SHAPE,
            prefer_hdbet=settings.MRI_USE_HDBET,
        )
        predictor = get_predictor(MODEL_PATH)
        prediction = predictor.predict(preprocessed.volume)

        mesh_result = export_mesh_bundle(
            masks=prediction.masks,
            probabilities=prediction.probabilities,
            brain_mask=preprocessed.brain_mask,
            voxel_spacing=preprocessed.voxel_spacing,
            output_dir=Path(settings.OUTPUT_DIR) / "meshes",
            request_id=request_id,
        )

        return MriAnalyzeResponse(
            request_id=request_id,
            uid=request_id,
            meshes=mesh_result.meshes,
            stats=mesh_result.stats,
            processing_time=time.time() - start_time,
            input_shape=list(preprocessed.volume.shape),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[MRI API ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"MRI processing error: {e}")
    finally:
        shutil.rmtree(upload_dir, ignore_errors=True)


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
            "metadata": { "processing_time": 45.2 }
        }
    """
    
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


@app.get("/api/report/{case_id}")
async def get_report(case_id: str):
    file_path = os.path.join(settings.CASE_DIR, case_id, f"MediCascade_Report_{case_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, media_type="application/pdf", filename=os.path.basename(file_path))


@app.get("/api/case/{case_id}")
async def get_case(case_id: str):
    case_path = os.path.join(settings.CASE_DIR, case_id, "case.json")
    if not os.path.exists(case_path):
        raise HTTPException(status_code=404, detail="Case not found")
    return FileResponse(case_path, media_type="application/json", filename="case.json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
