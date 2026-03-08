import os
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db, save_case, get_case_history, get_case, save_feedback, get_stats
from utils.icd_mapper import get_icd10_code

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from layers.layer0_pdf_processor import layer0_processor
from layers.layer1_specialists import layer1_specialists
from layers.layer2_validator import layer2_validator
from layers.layer3_annotator import layer3_annotator
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

# Initialise SQLite database on startup
init_db()




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

        # ICD-10 coding for structured reporting
        icd_code, icd_desc = get_icd10_code(layer2.primary_diagnosis or "")

        # Persist case to SQLite for history / longitudinal tracking
        drug_safety = layer3.visualization_data.get("drug_safety", {}) if layer3.visualization_data else {}
        try:
            save_case(
                case_id=layer0.case.case_id,
                source_pdf=file.filename or "",
                ingested_at=layer0.case.ingested_at,
                primary_diagnosis=layer2.primary_diagnosis or "Undetermined",
                icd10_code=icd_code,
                icd10_description=icd_desc,
                confidence=layer2.confidence,
                processing_time=total_elapsed,
                pdf_path=layer3.annotated_pdf_path or "",
                layer1_findings={"candidate_diagnoses": layer1.candidate_diagnoses, "red_flags": layer1.red_flags},
                layer2_assessment={"primary_diagnosis": layer2.primary_diagnosis, "confidence": layer2.confidence},
                drug_warnings=drug_safety.get("warnings", []) or [],
            )
        except Exception as db_err:
            logger.warning(f"DB save failed (non-fatal): {db_err}")

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
            "icd10_code": icd_code,
            "icd10_description": icd_desc,
            "drug_safety": drug_safety,
        }
        return response

    except Exception as e:
        print(f"[API ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#                     MRI 3D TUMOR SEGMENTATION (nnU-Net)
# ═══════════════════════════════════════════════════════════════════════════════

def _is_nifti_file(filename: str) -> bool:
    lower = filename.lower()
    return lower.endswith(".nii") or lower.endswith(".nii.gz")


@app.post("/api/mri/analyze")
async def analyze_mri(
    t1: UploadFile = File(...),
    t1ce: UploadFile = File(...),
    t2: UploadFile = File(...),
    flair: UploadFile = File(...),
):
    """
    Upload 4 MRI modalities (NIfTI), run nnU-Net segmentation,
    and return Plotly Mesh3d data for 3D brain + tumor visualization.
    """
    import nibabel as nib
    import numpy as np

    start_time = time.time()
    request_id = f"{int(start_time)}_{uuid4().hex[:6]}"
    upload_dir = Path(settings.UPLOAD_DIR) / "mri" / request_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploads = {"t1": t1, "t1ce": t1ce, "t2": t2, "flair": flair}
    saved_paths: dict[str, Path] = {}

    try:
        # Save uploaded NIfTI files
        for modality, upload in uploads.items():
            filename = upload.filename or ""
            if not _is_nifti_file(filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file for {modality.upper()}. Only .nii or .nii.gz accepted.",
                )
            ext = ".nii.gz" if filename.lower().endswith(".nii.gz") else ".nii"
            path = upload_dir / f"{modality}{ext}"
            with path.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)
            saved_paths[modality] = path

        # Load raw NIfTI volumes at full resolution
        volumes = {}
        spacing = (1.0, 1.0, 1.0)
        vol_shape = None

        for modality in ("t1", "t1ce", "t2", "flair"):
            img = nib.load(str(saved_paths[modality]))
            data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
            if data.ndim != 3:
                raise HTTPException(400, f"{modality.upper()} must be a 3D volume, got shape {data.shape}")
            volumes[modality] = data

            if vol_shape is None:
                vol_shape = data.shape
                spacing = tuple(float(s) for s in img.header.get_zooms()[:3])
            elif data.shape != vol_shape:
                raise HTTPException(400, f"Shape mismatch: {modality} is {data.shape}, expected {vol_shape}")

        logger.info(f"Loaded 4 modalities at full resolution {vol_shape}, spacing={spacing}")

        # Run nnU-Net segmentation
        from mri.predictor import get_predictor
        predictor = get_predictor()
        segmentation = predictor.predict(
            t1=volumes["t1"],
            t1ce=volumes["t1ce"],
            t2=volumes["t2"],
            flair=volumes["flair"],
            spacing=spacing,
        )

        logger.info(f"Segmentation labels: {np.unique(segmentation)}")

        # Generate Plotly meshes from raw FLAIR + segmentation
        from mri.mesh_generator import generate_meshes, compute_stats
        meshes = generate_meshes(
            flair_raw=volumes["flair"],
            segmentation=segmentation,
            spacing=spacing,
        )
        stats = compute_stats(segmentation=segmentation, spacing=spacing)

        processing_time = time.time() - start_time
        logger.info(f"MRI analysis complete in {processing_time:.1f}s")

        return {
            "request_id": request_id,
            "meshes": meshes,
            "stats": stats,
            "processing_time": round(processing_time, 2),
            "volume_shape": list(vol_shape),
            "voxel_spacing": list(spacing),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MRI analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MRI processing error: {e}")
    finally:
        shutil.rmtree(upload_dir, ignore_errors=True)


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


@app.get("/api/history")
async def case_history(limit: int = 20, offset: int = 0):
    """Return paginated list of all processed cases from the SQLite database."""
    cases = get_case_history(limit=limit, offset=offset)
    stats = get_stats()
    return {"cases": cases, "stats": stats, "limit": limit, "offset": offset}


@app.post("/api/feedback/{case_id}")
async def submit_feedback(case_id: str, rating: int, comment: str = ""):
    """
    Clinician feedback on diagnosis accuracy.
    rating: 1 (incorrect) → 5 (excellent).
    """
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    existing = get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found.")
    save_feedback(case_id=case_id, rating=rating, comment=comment)
    return {"success": True, "case_id": case_id, "rating": rating}


@app.get("/api/stats")
async def system_stats():
    """Aggregate statistics: total cases, avg confidence, top diagnoses."""
    return get_stats()


@app.get("/api/fhir/{case_id}")
async def fhir_export(case_id: str):
    """
    Export a case as a minimal FHIR R4 DiagnosticReport resource.
    Enables integration with EHR systems (Epic, Cerner, etc.).
    """
    row = get_case(case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case not found.")

    import json as _json
    l2 = _json.loads(row.get("layer2_json") or "{}") if row.get("layer2_json") else {}

    fhir = {
        "resourceType": "DiagnosticReport",
        "id": case_id,
        "status": "final",
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "47519-4",
                "display": "History and physical note"
            }]
        },
        "subject": {"display": row.get("source_pdf", "unknown")},
        "effectiveDateTime": row.get("ingested_at", ""),
        "issued": row.get("created_at", ""),
        "conclusion": row.get("primary_diagnosis", "Undetermined"),
        "conclusionCode": [{
            "coding": [{
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": row.get("icd10_code", "R69"),
                "display": row.get("icd10_description", "Illness, unspecified")
            }]
        }],
        "extension": [{
            "url": "https://medicascade.ai/fhir/StructureDefinition/confidence",
            "valueDecimal": row.get("confidence", 0.0)
        }],
        "presentedForm": [{
            "contentType": "application/pdf",
            "url": f"/outputs/cases/{case_id}/MediCascade_Report_{case_id}.pdf",
            "title": "MediCascade AI Diagnostic Report"
        }]
    }
    return JSONResponse(content=fhir, media_type="application/fhir+json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
